import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

print("=" * 65)
print("GRIDMIND AI - LOCAL ML BASELINE")
print("=" * 65)

# 1. Load the training dataset
df = pd.read_csv("train_telemetry.csv")

print("\n1. DATASET LOADED")
print(f"Total rows: {len(df)}")

# 2. Parse timestamps
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="raise"
)

# 3. Create time-based features
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.day_of_week
df["month"] = df["timestamp"].dt.month

# 4. Select model inputs
feature_columns = [
    "ambient_temp_c",
    "humidity_pct",
    "solar_irradiance_wm2",
    "hour",
    "day_of_week",
    "month",
]

X = df[feature_columns]
y = df["target_demand_kw"]

# 5. Split chronologically:
#    First 80% for training; final 20% for validation.
split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_valid = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_valid = y.iloc[split_index:]

print("\n2. TIME-BASED DATA SPLIT")
print(f"Training rows: {len(X_train)}")
print(f"Validation rows: {len(X_valid)}")
print(f"Training ends: {df['timestamp'].iloc[split_index - 1]}")
print(f"Validation starts: {df['timestamp'].iloc[split_index]}")

# 6. Create a genuine machine-learning model
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=12,
    min_samples_leaf=3,
    random_state=42,
    n_jobs=-1,
)

# 7. Train the model
print("\n3. TRAINING MODEL...")
model.fit(X_train, y_train)
print("Model training completed.")

# 8. Predict demand for the validation period
predictions = model.predict(X_valid)

# 9. Evaluate predictions
mae = mean_absolute_error(y_valid, predictions)
rmse = mean_squared_error(y_valid, predictions) ** 0.5
r2 = r2_score(y_valid, predictions)

print("\n4. VALIDATION RESULTS")
print("-" * 45)
print(f"Mean Absolute Error (MAE): {mae:.2f} kW")
print(f"Root Mean Squared Error (RMSE): {rmse:.2f} kW")
print(f"R-squared (R²): {r2:.4f}")

# 10. Show actual versus predicted values
results = pd.DataFrame({
    "timestamp": df["timestamp"].iloc[split_index:].values,
    "actual_demand_kw": y_valid.values,
    "predicted_demand_kw": predictions,
})

results["prediction_error_kw"] = (
    results["predicted_demand_kw"]
    - results["actual_demand_kw"]
)

print("\n5. FIRST 10 VALIDATION PREDICTIONS")

display_results = results.head(10).copy()

numeric_columns = [
    "actual_demand_kw",
    "predicted_demand_kw",
    "prediction_error_kw",
]

display_results[numeric_columns] = (
    display_results[numeric_columns].round(2)
)

print(display_results.to_string(index=False))

# 11. Save validation results
results.to_csv(
    "baseline_validation_results.csv",
    index=False
)

print("\n6. OUTPUT FILE")
print("Saved: baseline_validation_results.csv")

print("\nBaseline training and evaluation completed.")

# 12. Save the trained model and its feature configuration
model_artifact = {
    "model": model,
    "feature_columns": feature_columns,
    "mae_kw": float(mae),
    "rmse_kw": float(rmse),
    "r2": float(r2),
}

joblib.dump(
    model_artifact,
    "gridmind_baseline_model.joblib"
)

print("\n7. SAVED MODEL")
print("File: gridmind_baseline_model.joblib")