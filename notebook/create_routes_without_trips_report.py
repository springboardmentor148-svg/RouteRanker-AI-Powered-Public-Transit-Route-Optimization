
from pathlib import Path
import pandas as pd

# Set project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

INPUT_FILE = PROCESSED_DIR / "route_features.csv"
OUTPUT_FILE = PROCESSED_DIR / "routes_without_trips.csv"

# Check whether the input file exists
if not INPUT_FILE.exists():
    print(f"ERROR: File not found: {INPUT_FILE}")
    raise SystemExit(1)

# Read route features
df = pd.read_csv(INPUT_FILE, low_memory=False)

# Find routes with zero scheduled trips
routes_without_trips = df[
    pd.to_numeric(df["scheduled_trip_count"], errors="coerce").eq(0)
].copy()

# Select available columns for the report
wanted_columns = [
    "city",
    "route_id",
    "route_short_name",
    "route_long_name",
    "scheduled_trip_count",
    "stop_count",
    "estimated_straight_line_route_km",
    "trips_with_distance",
]

columns = [column for column in wanted_columns if column in df.columns]
report = routes_without_trips[columns].sort_values(
    ["city", "route_id"]
)

# Save report
report.to_csv(OUTPUT_FILE, index=False)

# Display results
print("\nRoutes without scheduled trips report created!")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Total routes without scheduled trips: {len(report)}")

print("\nCount by city:")
print(report.groupby("city").size().to_string())

print("\nFirst 10 records:")
print(report.head(10).to_string(index=False))
