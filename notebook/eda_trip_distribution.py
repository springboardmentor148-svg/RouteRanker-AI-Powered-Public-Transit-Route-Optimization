
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"

INPUT_PATH = REPORT_DIR / "eda_top_routes.csv"
OUTPUT_PATH = REPORT_DIR / "eda_trip_distribution.csv"

# Load all route indicators instead of only the top 10 routes
CITIES = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad",
]

frames = []

for city in CITIES:
    path = REPORT_DIR / f"{city}_route_indicators.csv"

    if not path.exists():
        print(f"Missing file: {path}")
        continue

    df = pd.read_csv(path, low_memory=False)

    if "scheduled_trip_count" not in df.columns:
        print(f"Missing scheduled_trip_count in {path}")
        continue

    df["city"] = city
    df["scheduled_trip_count"] = pd.to_numeric(
        df["scheduled_trip_count"], errors="coerce"
    ).fillna(0)

    frames.append(df)

if not frames:
    raise FileNotFoundError(
        "No route indicator files were found in the reports folder."
    )

all_routes = pd.concat(frames, ignore_index=True)
results = []

for city, group in all_routes.groupby("city"):
    trips = group["scheduled_trip_count"]

    results.append({
        "city": city,
        "total_routes": len(group),
        "routes_with_zero_trips": int((trips == 0).sum()),
        "routes_with_1_to_10_trips": int(
            ((trips >= 1) & (trips <= 10)).sum()
        ),
        "routes_with_11_to_50_trips": int(
            ((trips >= 11) & (trips <= 50)).sum()
        ),
        "routes_with_more_than_50_trips": int(
            (trips > 50).sum()
        ),
        "minimum_trips": int(trips.min()),
        "median_trips": float(trips.median()),
        "maximum_trips": int(trips.max()),
    })

summary = pd.DataFrame(results)
summary.to_csv(OUTPUT_PATH, index=False)


print("\n=== ROUTE TRIP DISTRIBUTION ===")
print(summary.to_string(index=False, col_space=12))
print("\nReport saved to:", OUTPUT_PATH)
