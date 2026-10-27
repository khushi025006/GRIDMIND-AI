import joblib
import pandas as pd

from grid_controller import evaluate_grid_state

print("=" * 70)
print("GRIDMIND AI - ML + GRID CONTROLLER INTEGRATION TEST")
print("=" * 70)

# 1. Load the saved ML model
artifact = joblib.load("gridmind_baseline_model.joblib")

model = artifact["model"]
feature_columns = artifact["feature_columns"]

print("\n1. SAVED ML MODEL LOADED")

# 2. Read sample input data
df = pd.read_csv("sample_test_input.csv").head(10)

# 3. Prepare timestamps
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="raise"
)

# 4. Create the time features used during training
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.day_of_week
df["month"] = df["timestamp"].dt.month

# 5. Generate demand predictions
X = df[feature_columns]
predictions = model.predict(X)

print("\n2. APPLYING GRID RULES TO ML PREDICTIONS")

results = []

for timestamp, prediction in zip(
    df["timestamp"],
    predictions
):
    decision = evaluate_grid_state(
        demand_kw=float(prediction),
        timestamp=timestamp.to_pydatetime()
    )

    results.append({
        "timestamp": timestamp,
        "predicted_demand_kw": round(float(prediction), 2),
        "grid_mode": decision["grid_mode"],
        "critical_alert": decision["critical_alert"],
        "alert_message": decision["alert_message"],
        "explanation": decision["explanation"],
    })

# 6. Display integration results
results_df = pd.DataFrame(results)

print(results_df.to_string(index=False))

# 7. Save the results
results_df.to_csv(
    "ml_grid_integration_results.csv",
    index=False
)

print("\n3. INTEGRATION OUTPUT")
print("Saved: ml_grid_integration_results.csv")
print("\nML + grid controller integration test completed.")