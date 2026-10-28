
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

REPORT_FILE = PROCESSED_DIR / "routes_without_trips.csv"
OUTPUT_FILE = PROCESSED_DIR / "routes_without_trips_source_check.csv"

report = pd.read_csv(REPORT_FILE)
results = []

for city in report["city"].dropna().unique():
    city_dir = DATA_DIR / "raw" / city

    routes_file = city_dir / "routes.txt"
    trips_file = city_dir / "trips.txt"

    if not routes_file.exists() or not trips_file.exists():
        print(f"Source files not found for {city}: {city_dir}")
        continue

    routes = pd.read_csv(routes_file, dtype=str, low_memory=False)
    trips = pd.read_csv(trips_file, dtype=str, low_memory=False)

    if "route_id" not in routes.columns or "route_id" not in trips.columns:
        print(f"route_id column missing for {city}")
        continue

    # Count trips associated with each route in the original trips.txt
    trip_counts = trips["route_id"].value_counts()

    city_routes = report[report["city"] == city]

    for _, route in city_routes.iterrows():
        route_id = str(route["route_id"])

        source_route = routes[routes["route_id"] == route_id]
        source_trip_count = int(trip_counts.get(route_id, 0))

        results.append({
            "city": city,
            "route_id": route_id,
            "route_exists_in_routes_txt": not source_route.empty,
            "matching_trips_in_trips_txt": source_trip_count,
            "has_matching_source_trips": source_trip_count > 0,
        })

result_df = pd.DataFrame(results)
result_df.to_csv(OUTPUT_FILE, index=False)

print("\nSource verification completed!")
print(f"Saved to: {OUTPUT_FILE}")
print(f"Routes checked: {len(result_df)}")

if not result_df.empty:
    print("\nSummary by city:")
    print(
        result_df.groupby("city").agg(
            routes_checked=("route_id", "count"),
            routes_found_in_source=("route_exists_in_routes_txt", "sum"),
            routes_with_source_trips=("has_matching_source_trips", "sum"),
        ).to_string()
    )

    print("\nFirst 10 results:")
    print(result_df.head(10).to_string(index=False))
