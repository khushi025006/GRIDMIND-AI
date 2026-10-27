import joblib
import pandas as pd

print("=" * 60)
print("GRIDMIND AI - SAVED MODEL TEST")
print("=" * 60)

# 1. Load the saved model
artifact = joblib.load("gridmind_baseline_model.joblib")

model = artifact["model"]
feature_columns = artifact["feature_columns"]

print("\n1. MODEL LOADED SUCCESSFULLY")
print(f"Model type: {type(model).__name__}")
print(f"Number of features: {len(feature_columns)}")
print(f"Features: {feature_columns}")

# 2. Load five sample input records
df = pd.read_csv("sample_test_input.csv").head(5)

# 3. Convert timestamps into datetime values
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="raise"
)

# 4. Create the same time features used during training
df["hour"] = df["timestamp"].dt.hour
df["day_of_week"] = df["timestamp"].dt.day_of_week
df["month"] = df["timestamp"].dt.month

# 5. Select features in the exact training order
X = df[feature_columns]

# 6. Generate predictions using the saved model
predictions = model.predict(X)

print("\n2. SAMPLE PREDICTIONS")

for timestamp, prediction in zip(
    df["timestamp"],
    predictions
):
    print(f"{timestamp} -> {prediction:.2f} kW")

# 7. Display the saved evaluation metrics
print("\n3. SAVED VALIDATION METRICS")
print(f"MAE:  {artifact['mae_kw']:.2f} kW")
print(f"RMSE: {artifact['rmse_kw']:.2f} kW")
print(f"R²:   {artifact['r2']:.4f}")

print("\nSaved model test completed successfully.")