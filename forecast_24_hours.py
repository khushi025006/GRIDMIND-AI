import joblib
import pandas as pd

from grid_controller import evaluate_grid_state


# --------------------------------------------------
# GRIDMIND AI - 24-HOUR FORECAST PIPELINE
# --------------------------------------------------

MODEL_PATH = "gridmind_baseline_model.joblib"
INPUT_PATH = "sample_test_input.csv"
OUTPUT_PATH = "forecast_24_hours.csv"

FORECAST_HOURS = 24


def generate_24_hour_forecast():
    print("=" * 70)
    print("GRIDMIND AI - 24-HOUR DEMAND FORECAST")
    print("=" * 70)

    # 1. Load the trained model
    artifact = joblib.load(MODEL_PATH)

    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    print("\n1. SAVED ML MODEL LOADED")
    print("Model:", type(model).__name__)

    # 2. Read the input dataset
    df = pd.read_csv(INPUT_PATH)

    required_columns = [
        "timestamp",
        "ambient_temp_c",
        "humidity_pct",
        "solar_irradiance_wm2",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Input CSV is missing required columns: {missing_columns}"
        )

    # 3. Validate and sort timestamps
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise"
    )

    df = df.sort_values("timestamp").reset_index(drop=True)

    if df["timestamp"].duplicated().any():
        raise ValueError(
            "Input CSV contains duplicate timestamps."
        )

    if len(df) < FORECAST_HOURS:
        raise ValueError(
            f"At least {FORECAST_HOURS} input rows are required."
        )

    # 4. Select 24 consecutive hourly records
    forecast_df = df.head(FORECAST_HOURS).copy()

    timestamp_differences = (
        forecast_df["timestamp"].diff().dropna()
    )

    if not timestamp_differences.eq(pd.Timedelta(hours=1)).all():
        raise ValueError(
            "The selected records must have consecutive hourly timestamps."
        )

    print("\n2. INPUT DATA VALIDATED")
    print("Forecast records:", len(forecast_df))
    print("Start:", forecast_df["timestamp"].iloc[0])
    print("End:", forecast_df["timestamp"].iloc[-1])

    # 5. Create the same time features used during training
    forecast_df["hour"] = forecast_df["timestamp"].dt.hour
    forecast_df["day_of_week"] = (
        forecast_df["timestamp"].dt.day_of_week
    )
    forecast_df["month"] = forecast_df["timestamp"].dt.month

    # 6. Predict demand
    X = forecast_df[feature_columns]
    predictions = model.predict(X)

    forecast_df["predicted_demand_kw"] = predictions.round(2)

    # 7. Apply the grid controller to every prediction
    results = []

    for _, row in forecast_df.iterrows():
        prediction = float(row["predicted_demand_kw"])
        timestamp = row["timestamp"]

        decision = evaluate_grid_state(
            demand_kw=prediction,
            timestamp=timestamp.to_pydatetime()
        )

        results.append({
            "timestamp": timestamp,
            "predicted_demand_kw": prediction,
            "grid_mode": decision["grid_mode"],
            "critical_alert": decision["critical_alert"],
            "alert_message": decision["alert_message"],
            "explanation": decision["explanation"],
        })

    # 8. Build the final forecast table
    results_df = pd.DataFrame(results)

    # 9. Save forecast results
    results_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # 10. Display the forecast
    print("\n3. 24-HOUR FORECAST RESULTS")
    print("-" * 70)
    print(results_df.to_string(index=False))

    critical_count = int(
        results_df["critical_alert"].fillna(False).astype(bool).sum()
    )

    storage_count = int(
        results_df["grid_mode"]
        .eq("Renewable Storage Mode")
        .sum()
    )

    main_grid_count = int(
        results_df["grid_mode"]
        .eq("Main Grid Mode")
        .sum()
    )

    print("\n4. FORECAST SUMMARY")
    print("-" * 70)
    print("Total forecast hours:", len(results_df))
    print("Renewable Storage Mode hours:", storage_count)
    print("Main Grid Mode hours:", main_grid_count)
    print("Critical overload alerts:", critical_count)

    print("\nSaved forecast:", OUTPUT_PATH)
    print("\n24-hour forecast completed successfully.")

    return results_df


if __name__ == "__main__":
    generate_24_hour_forecast()

