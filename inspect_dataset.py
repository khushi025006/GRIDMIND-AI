import pandas as pd

# Load the historical training dataset.
df = pd.read_csv("train_telemetry.csv")

print("=" * 60)
print("GRIDMIND AI - DATASET INSPECTION")
print("=" * 60)

# 1. Dataset dimensions
print("\n1. DATASET SIZE")
print(f"Rows: {df.shape[0]}")
print(f"Columns: {df.shape[1]}")

# 2. Column names and data types
print("\n2. COLUMN TYPES")
print(df.dtypes)

# 3. Missing values
print("\n3. MISSING VALUES")
print(df.isnull().sum())

# 4. Duplicate records
print("\n4. DUPLICATE ROWS")
print(f"Duplicate rows: {df.duplicated().sum()}")

# 5. Numerical summary
print("\n5. NUMERICAL SUMMARY")
print(df.describe().round(2).to_string())

# 6. Timestamp validation
print("\n6. TIMESTAMP VALIDATION")
timestamps = pd.to_datetime(df["timestamp"], errors="coerce")

print(f"Invalid timestamps: {timestamps.isna().sum()}")

if timestamps.notna().any():
    print(f"First timestamp: {timestamps.min()}")
    print(f"Last timestamp:  {timestamps.max()}")

# 7. Target distribution
print("\n7. TARGET DEMAND")
print(f"Minimum demand: {df['target_demand_kw'].min():.2f} kW")
print(f"Maximum demand: {df['target_demand_kw'].max():.2f} kW")
print(f"Average demand: {df['target_demand_kw'].mean():.2f} kW")
print(f"Median demand:  {df['target_demand_kw'].median():.2f} kW")

print("\nDataset inspection completed.")