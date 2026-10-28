from pathlib import Path
from flask_cors import CORS
from flask import Flask
import joblib
import pandas as pd

from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

from grid_controller import evaluate_grid_state


# --------------------------------------------------
# GRIDMIND AI - BACKEND API
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "gridmind_baseline_model.joblib"

REQUIRED_COLUMNS = [
    "timestamp",
    "ambient_temp_c",
    "humidity_pct",
    "solar_irradiance_wm2",
]

FORECAST_HOURS = 24
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
app = Flask(__name__)

CORS(
    app,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
)

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE


# --------------------------------------------------
# LOAD TRAINED MODEL
# --------------------------------------------------

model = None
feature_columns = []
model_metrics = {}
model_status = "not_loaded"

try:
    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]
    feature_columns = artifact["feature_columns"]
    model_metrics = artifact.get("metrics", {})
    model_status = "loaded"

    print("GRIDMIND AI: ML model loaded successfully.")

except Exception as error:
    model_status = "error"
    print(f"GRIDMIND AI: Model loading failed: {error}")


# --------------------------------------------------
# HOME ENDPOINT
# --------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "application": "GRIDMIND AI",
        "message": "Smart Energy Microgrid & Demand Forecasting API",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "forecast": "/api/forecast",
        },
    })


# --------------------------------------------------
# HEALTH CHECK ENDPOINT
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    status_code = 200 if model_status == "loaded" else 503

    return jsonify({
        "application": "GRIDMIND AI",
        "api_status": "healthy",
        "model_status": model_status,
        "model_type": (
            type(model).__name__
            if model is not None
            else None
        ),
        "model_features": feature_columns,
        "grid_controller_status": "available",
    }), status_code


# --------------------------------------------------
# MODEL METRICS ENDPOINT
# --------------------------------------------------

@app.route("/api/model-metrics", methods=["GET"])
def get_model_metrics():
    if model is None:
        return jsonify({
            "error": "The trained model is not available."
        }), 503

    return jsonify({
        "model_type": type(model).__name__,
        "metrics": model_metrics,
        "metric_note": (
            "Metrics come from historical holdout validation. "
            "They do not guarantee future real-world accuracy."
        ),
    })


# --------------------------------------------------
# CSV FORECAST ENDPOINT
# --------------------------------------------------

@app.route("/api/forecast", methods=["POST"])
def forecast():
    if model is None:
        return jsonify({
            "error": "The trained ML model is not available."
        }), 503

    # 1. Check whether a CSV file was uploaded.
    if "file" not in request.files:
        return jsonify({
            "error": "No file uploaded.",
            "expected_field": "file",
        }), 400

    uploaded_file = request.files["file"]

    if not uploaded_file.filename:
        return jsonify({
            "error": "Please select a CSV file."
        }), 400

    safe_filename = secure_filename(uploaded_file.filename)

    if not safe_filename.lower().endswith(".csv"):
        return jsonify({
            "error": "Only CSV files are accepted."
        }), 400

    # 2. Read the uploaded CSV.
    try:
        df = pd.read_csv(uploaded_file)
    except Exception:
        return jsonify({
            "error": "The uploaded file could not be read as CSV."
        }), 400

    # 3. Validate required columns.
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        return jsonify({
            "error": "The CSV is missing required columns.",
            "missing_columns": missing_columns,
            "required_columns": REQUIRED_COLUMNS,
        }), 400

    # 4. Validate the number of records.
    if len(df) < FORECAST_HOURS:
        return jsonify({
            "error": (
                f"The CSV must contain at least "
                f"{FORECAST_HOURS} records."
            ),
            "received_records": len(df),
        }), 400

    # 5. Validate timestamps and numeric features.
    try:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="raise",
        )

        numeric_columns = [
            "ambient_temp_c",
            "humidity_pct",
            "solar_irradiance_wm2",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="raise",
            )

    except (ValueError, TypeError):
        return jsonify({
            "error": (
                "Invalid timestamps or non-numeric "
                "environmental features were found."
            )
        }), 400

    # 6. Reject missing or non-finite values.
    if df[REQUIRED_COLUMNS].isnull().any().any():
        return jsonify({
            "error": "Required columns contain missing values."
        }), 400

    import numpy as np

    if not np.isfinite(
        df[numeric_columns].to_numpy(dtype=float)
    ).all():
        return jsonify({
            "error": "Environmental features contain invalid numeric values."
        }), 400

    # 7. Sort and validate timestamps.
    df = df.sort_values("timestamp").reset_index(drop=True)

    if df["timestamp"].duplicated().any():
        return jsonify({
            "error": "Duplicate timestamps are not allowed."
        }), 400

    # Select the first 24 consecutive hourly records.
    forecast_df = df.head(FORECAST_HOURS).copy()

    differences = forecast_df["timestamp"].diff().dropna()

    if not differences.eq(pd.Timedelta(hours=1)).all():
        return jsonify({
            "error": (
                "The first 24 records must have consecutive "
                "hourly timestamps."
            )
        }), 400

    # 8. Generate the same time features used during training.
    forecast_df["hour"] = forecast_df["timestamp"].dt.hour
    forecast_df["day_of_week"] = (
        forecast_df["timestamp"].dt.day_of_week
    )
    forecast_df["month"] = forecast_df["timestamp"].dt.month

    # 9. Predict demand using the saved ML model.
    try:
        X = forecast_df[feature_columns]
        predictions = model.predict(X)

    except Exception as error:
        app.logger.exception("Prediction failed")

        return jsonify({
            "error": "The demand prediction failed.",
            "details": str(error),
        }), 500

    # 10. Apply the existing grid decision rules.
    results = []

    for timestamp, prediction in zip(
        forecast_df["timestamp"],
        predictions,
    ):
        demand_kw = float(prediction)

        decision = evaluate_grid_state(
            demand_kw=demand_kw,
            timestamp=timestamp.to_pydatetime(),
        )

        alert_message = decision["alert_message"]

        results.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "predicted_demand_kw": round(demand_kw, 2),
            "grid_mode": decision["grid_mode"],
            "critical_alert": bool(decision["critical_alert"]),
            "alert_message": (
                str(alert_message)
                if alert_message
                else None
            ),
            "explanation": decision["explanation"],
        })

    # 11. Build summary information.
    critical_count = sum(
        item["critical_alert"]
        for item in results
    )

    storage_count = sum(
        item["grid_mode"] == "Renewable Storage Mode"
        for item in results
    )

    main_grid_count = sum(
        item["grid_mode"] == "Main Grid Mode"
        for item in results
    )

    return jsonify({
        "application": "GRIDMIND AI",
        "status": "success",
        "forecast_hours": len(results),
        "input_records": len(df),
        "forecast_period": {
            "start": results[0]["timestamp"],
            "end": results[-1]["timestamp"],
        },
        "summary": {
            "renewable_storage_hours": storage_count,
            "main_grid_hours": main_grid_count,
            "critical_alerts": critical_count,
        },
        "data_note": (
            "Predictions use supplied environmental features. "
            "They are not guaranteed real-world future demand."
        ),
        "forecast": results,
    })


# --------------------------------------------------
# HANDLE LARGE FILES
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({
        "error": "The uploaded file exceeds the 10 MB limit."
    }), 413


# --------------------------------------------------
# START DEVELOPMENT SERVER
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )

