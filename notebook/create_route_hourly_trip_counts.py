
from pathlib import Path
import pandas as pd

# 1. Set project paths
project_dir = Path(
    r"C:\Users\LENOVO\OneDrive\Desktop\RouteRanker"
)
raw_dir = project_dir / "data" / "raw"
processed_dir = project_dir / "data" / "processed"

processed_dir.mkdir(parents=True, exist_ok=True)

hourly_results = []

# 2. Process each city
for city_folder in raw_dir.iterdir():

    if not city_folder.is_dir():
        continue

    city = city_folder.name.lower()

    trips_file = city_folder / "trips.txt"
    stop_times_file = city_folder / "stop_times.txt"

    if not trips_file.exists() or not stop_times_file.exists():
        print(f"Skipping {city}: required files missing")
        continue

    print(f"Processing {city}...")

    trips = pd.read_csv(trips_file, dtype=str)
    stop_times = pd.read_csv(stop_times_file, dtype=str)

    # Check required columns
    if not {"trip_id", "route_id"}.issubset(trips.columns):
        print(f"Skipping {city}: trip_id or route_id missing")
        continue

    if not {
        "trip_id", "stop_sequence", "departure_time"
    }.issubset(stop_times.columns):
        print(f"Skipping {city}: required stop_times columns missing")
        continue

    # 3. Find each trip's first stop using stop_sequence
    stop_times["stop_sequence"] = pd.to_numeric(
        stop_times["stop_sequence"], errors="coerce"
    )

    first_departures = (
        stop_times
        .dropna(subset=["stop_sequence"])
        .sort_values(["trip_id", "stop_sequence"])
        .drop_duplicates(subset=["trip_id"], keep="first")
        [["trip_id", "departure_time"]]
        .copy()
    )

    # 4. Extract GTFS service hour
    # Handles times such as 08:30:00 and 25:15:00
    time_parts = first_departures["departure_time"].str.extract(
        r"^(\d+):([0-5]\d):([0-5]\d)$"
    )

    first_departures["service_hour"] = pd.to_numeric(
        time_parts[0], errors="coerce"
    )

    first_departures = first_departures.dropna(
        subset=["service_hour"]
    )

    first_departures["service_hour"] = (
        first_departures["service_hour"].astype(int)
    )

    # 5. Connect each trip to its route
    trip_routes = (
        trips[["trip_id", "route_id"]]
        .drop_duplicates(subset=["trip_id"])
    )

    first_departures = first_departures.merge(
        trip_routes,
        on="trip_id",
        how="inner",
        validate="one_to_one"
    )

    # 6. Count distinct scheduled trips per route and hour
    hourly = (
        first_departures
        .groupby(["route_id", "service_hour"])["trip_id"]
        .nunique()
        .reset_index(name="scheduled_trip_count")
    )

    hourly.insert(0, "city", city)

    hourly_results.append(hourly)

# 7. Combine all cities and save the CSV
if hourly_results:

    hourly_df = pd.concat(
        hourly_results, ignore_index=True
    )

    output_file = (
        processed_dir / "route_hourly_trip_counts.csv"
    )

    hourly_df.to_csv(output_file, index=False)

    print("\nHourly trip counts created successfully!")
    print("\nFirst 10 records:")
    print(hourly_df.head(10).to_string(index=False))

    print("\nTotal records:", len(hourly_df))
    print("Cities processed:", hourly_df["city"].nunique())
    print("Saved to:", output_file)

else:
    print("No results created. Check your GTFS folders and columns.")
