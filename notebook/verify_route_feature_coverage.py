
from pathlib import Path
import pandas as pd

# Project paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
FEATURES_FILE = PROJECT_DIR / "data" / "processed" / "route_features.csv"

cities = ["ahmedabad", "chennai", "hyderabad", "mumbai", "pune"]

features = pd.read_csv(FEATURES_FILE, dtype={"route_id": str})
results = []

for city in cities:
    trips_file = RAW_DIR / city / "trips.txt"

    # Get route IDs that appear in the original trips file
    trips = pd.read_csv(
        trips_file,
        dtype=str,
        usecols=["route_id"]
    )

    source_routes = set(trips["route_id"].dropna())

    # Get routes with scheduled trips in the generated features
    city_features = features[
        (features["city"] == city)
        & (features["scheduled_trip_count"] > 0)
    ]

    feature_routes = set(city_features["route_id"].astype(str))

    missing_routes = source_routes - feature_routes

    results.append({
        "city": city,
        "source_routes_with_trips": len(source_routes),
        "feature_routes_with_trips": len(feature_routes),
        "source_routes_missing_from_features": len(missing_routes),
    })

report = pd.DataFrame(results)

output_file = (
    PROJECT_DIR
    / "data"
    / "processed"
    / "route_feature_coverage_report.csv"
)

report.to_csv(output_file, index=False)

print("\nRoute feature coverage verification completed!")
print(report.to_string(index=False))
print(f"\nReport saved to: {output_file}")
