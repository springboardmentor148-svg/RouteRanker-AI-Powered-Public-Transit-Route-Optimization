
from pathlib import Path
import pandas as pd

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

cities = ["ahmedabad", "chennai", "hyderabad", "mumbai", "pune"]

all_profiles = []

for city in cities:
    print(f"Processing {city}...")

    city_dir = RAW_DIR / city

    routes_file = city_dir / "routes.txt"
    trips_file = city_dir / "trips.txt"
    stop_times_file = city_dir / "stop_times.txt"

    # Check required files
    for file_path in [routes_file, trips_file, stop_times_file]:
        if not file_path.exists():
            raise FileNotFoundError(f"Missing file: {file_path}")

    routes = pd.read_csv(routes_file, dtype=str)
    trips = pd.read_csv(trips_file, dtype=str)
    stop_times = pd.read_csv(stop_times_file, dtype=str)

    # Count unique trips for each route
    trip_counts = (
        trips.groupby("route_id")["trip_id"]
        .nunique()
        .reset_index(name="distinct_trip_count")
    )

    # Connect trips to their routes and count unique stops
    trip_routes = trips[["trip_id", "route_id"]].drop_duplicates()

    trip_stops = stop_times[["trip_id", "stop_id"]].dropna().drop_duplicates()

    route_stops = trip_routes.merge(
        trip_stops,
        on="trip_id",
        how="inner"
    )

    stop_counts = (
        route_stops.groupby("route_id")["stop_id"]
        .nunique()
        .reset_index(name="distinct_stop_count")
    )

    # Combine route details and calculated counts
    profiles = routes.merge(
        trip_counts,
        on="route_id",
        how="left"
    )

    profiles = profiles.merge(
        stop_counts,
        on="route_id",
        how="left"
    )

    profiles["city"] = city
    profiles["distinct_trip_count"] = (
        profiles["distinct_trip_count"].fillna(0).astype(int)
    )
    profiles["distinct_stop_count"] = (
        profiles["distinct_stop_count"].fillna(0).astype(int)
    )

    all_profiles.append(profiles)

# Combine all five cities
final_profiles = pd.concat(all_profiles, ignore_index=True)

# Arrange identifying columns first
first_columns = [
    "city",
    "route_id",
    "route_short_name",
    "route_long_name",
    "distinct_trip_count",
    "distinct_stop_count"
]

available_first = [
    col for col in first_columns if col in final_profiles.columns
]

remaining_columns = [
    col for col in final_profiles.columns if col not in available_first
]

final_profiles = final_profiles[available_first + remaining_columns]

# Save output
output_file = PROCESSED_DIR / "route_profiles.csv"
final_profiles.to_csv(output_file, index=False)

print("\nRoute profiles created successfully!")
print(f"Total route records: {len(final_profiles)}")
print(f"Cities processed: {final_profiles['city'].nunique()}")
print(f"Saved to: {output_file}")

print("\nFirst 10 records:")
print(final_profiles[available_first].head(10).to_string(index=False))
