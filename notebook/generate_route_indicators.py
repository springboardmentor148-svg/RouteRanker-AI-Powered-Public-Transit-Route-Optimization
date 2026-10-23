
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

cities = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad"
]

all_city_summaries = []

for city in cities:
    print(f"\nAnalyzing routes in {city}...")

    city_dir = PROCESSED_DIR / city

    required_files = {
        "routes": city_dir / "routes.csv",
        "trips": city_dir / "trips.csv",
        "stop_times": city_dir / "stop_times.csv"
    }

    if not all(path.exists() for path in required_files.values()):
        print(f"Required files missing for {city}. Skipping.")
        continue

    routes = pd.read_csv(required_files["routes"], low_memory=False)
    trips = pd.read_csv(required_files["trips"], low_memory=False)
    stop_times = pd.read_csv(
        required_files["stop_times"], low_memory=False
    )

    if not {"route_id", "trip_id"}.issubset(trips.columns):
        print(f"Required columns missing in {city} trips.")
        continue

    if not {"trip_id", "stop_id"}.issubset(stop_times.columns):
        print(f"Required columns missing in {city} stop_times.")
        continue

    # Count scheduled trips for each route
    trip_counts = (
        trips.groupby("route_id")["trip_id"]
        .nunique()
        .rename("scheduled_trip_count")
    )

    # Attach each stop-time record to its route
    trip_routes = trips[["trip_id", "route_id"]].drop_duplicates(
        subset=["trip_id"]
    )

    events = stop_times.merge(
        trip_routes,
        on="trip_id",
        how="left",
        validate="many_to_one"
    )

    # Count stop-time records and distinct stops per route
    event_counts = (
        events.groupby("route_id")
        .size()
        .rename("scheduled_stop_events")
    )

    distinct_stops = (
        events.groupby("route_id")["stop_id"]
        .nunique()
        .rename("distinct_stops_served")
    )

    # Count stop records per trip, then average by route
    stops_per_trip = (
        events.groupby(["route_id", "trip_id"])
        .size()
        .groupby(level="route_id")
        .mean()
        .rename("average_stops_per_trip")
    )

    # Combine route indicators
    result = routes.copy()

    result = result.merge(
        trip_counts, on="route_id", how="left"
    )
    result = result.merge(
        event_counts, on="route_id", how="left"
    )
    result = result.merge(
        distinct_stops, on="route_id", how="left"
    )
    result = result.merge(
        stops_per_trip, on="route_id", how="left"
    )

    result.insert(0, "city", city)

    count_columns = [
        "scheduled_trip_count",
        "scheduled_stop_events",
        "distinct_stops_served"
    ]

    result[count_columns] = (
        result[count_columns].fillna(0).astype(int)
    )

    result["average_stops_per_trip"] = (
        result["average_stops_per_trip"].round(2)
    )

    output_path = REPORT_DIR / f"{city}_route_indicators.csv"
    result.to_csv(output_path, index=False)

    all_city_summaries.append({
        "city": city,
        "routes_analyzed": len(result),
        "total_scheduled_trips": int(
            result["scheduled_trip_count"].sum()
        ),
        "total_scheduled_stop_events": int(
            result["scheduled_stop_events"].sum()
        ),
        "routes_without_trips": int(
            (result["scheduled_trip_count"] == 0).sum()
        )
    })

    print(f"Routes analyzed: {len(result)}")
    print(f"Saved: {output_path}")

# Save a combined city summary
if all_city_summaries:
    summary = pd.DataFrame(all_city_summaries)

    summary_path = REPORT_DIR / "route_indicator_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("\n========== ROUTE INDICATOR SUMMARY ==========")
    print(summary.to_csv(index=False))
    print(f"\nSummary saved to: {summary_path}")
else:
    print("No city indicators were generated.")
