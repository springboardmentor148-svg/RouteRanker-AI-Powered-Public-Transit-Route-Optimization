
from pathlib import Path
import pandas as pd
from math import radians, sin, cos, sqrt, atan2

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

cities = [
    "Hyderabad", "Mumbai", "Pune",
    "Chennai", "Ahmedabad", "Rajkot"
]

def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    x = (sin(dlat / 2) ** 2 +
         cos(radians(lat1)) * cos(radians(lat2)) *
         sin(dlon / 2) ** 2)
    return 2 * r * atan2(sqrt(x), sqrt(1 - x))

for city in cities:
    print("\nProcessing:", city)

    try:
        folder = RAW / city

        routes = pd.read_csv(
            folder / "routes.txt", dtype=str
        )
        trips = pd.read_csv(
            folder / "trips.txt", dtype=str
        )
        stops = pd.read_csv(
            folder / "stops.txt", dtype=str
        )

        # 1. Remove duplicates and missing IDs
        routes = routes.drop_duplicates()
        trips = trips.drop_duplicates()
        stops = stops.drop_duplicates()

        routes = routes.dropna(subset=["route_id"])
        trips = trips.dropna(
            subset=["trip_id", "route_id", "service_id"]
        )
        stops = stops.dropna(subset=["stop_id"])

        # 2. Remove orphan trip references
        trips = trips[
            trips["route_id"].isin(routes["route_id"])
        ].copy()

        # 3. Clean stop coordinates
        stops["stop_lat"] = pd.to_numeric(
            stops["stop_lat"], errors="coerce"
        )
        stops["stop_lon"] = pd.to_numeric(
            stops["stop_lon"], errors="coerce"
        )

        invalid = (
            ~stops["stop_lat"].between(-90, 90) |
            ~stops["stop_lon"].between(-180, 180)
        )
        stops.loc[
            invalid, ["stop_lat", "stop_lon"]
        ] = float("nan")

        # 4. Weekday and weekend service
        cal_path = folder / "calendar.txt"

        if cal_path.exists():
            cal = pd.read_csv(cal_path, dtype=str)
            weekdays = [
                "monday", "tuesday", "wednesday",
                "thursday", "friday"
            ]
            weekends = ["saturday", "sunday"]

            for col in weekdays + weekends:
                cal[col] = pd.to_numeric(
                    cal[col], errors="coerce"
                ).fillna(0)

            cal["weekday_service"] = (
                cal[weekdays].sum(axis=1) > 0
            )
            cal["weekend_service"] = (
                cal[weekends].sum(axis=1) > 0
            )

            cal.to_csv(
                OUT / f"{city}_service_days.csv",
                index=False
            )
        else:
            print("No calendar.txt:", city)

        # 5. Trip count per route
        profiles = (
            trips.groupby("route_id")["trip_id"]
            .nunique()
            .reset_index(name="scheduled_trip_records")
        )

        # 6. Connect trips to routes
        trip_map = (
            trips.drop_duplicates("trip_id")
            .set_index("trip_id")["route_id"]
        )

        stop_coords = (
            stops.drop_duplicates("stop_id")
            .set_index("stop_id")[
                ["stop_lat", "stop_lon"]
            ].to_dict("index")
        )

        hourly_parts = []
        sample_trip = {}
        sample_points = {}

        # 7. Read stop times in chunks
        for chunk in pd.read_csv(
            folder / "stop_times.txt",
            dtype=str,
            chunksize=100000
        ):
            chunk = chunk.dropna(
                subset=["trip_id", "stop_id"]
            ).drop_duplicates()

            chunk["route_id"] = (
                chunk["trip_id"].map(trip_map)
            )
            chunk = chunk.dropna(subset=["route_id"])

            # GTFS times can exceed 24 hours
            hours = pd.to_numeric(
                chunk["departure_time"]
                .str.split(":").str[0],
                errors="coerce"
            )
            chunk["hour"] = hours % 24

            # Stop events by route and hour
            hourly = (
                chunk.dropna(subset=["hour"])
                .groupby(["route_id", "hour"])
                .size()
                .reset_index(name="stop_events")
            )
            hourly_parts.append(hourly)

            # Keep one representative trip per route
            for route_id, group in chunk.groupby("route_id"):
                if route_id not in sample_trip:
                    sample_trip[route_id] = (
                        group["trip_id"].iloc[0]
                    )

                selected = group[
                    group["trip_id"] == sample_trip[route_id]
                ]

                sample_points.setdefault(
                    route_id, []
                ).extend(
                    selected[
                        ["stop_sequence", "stop_id"]
                    ].values.tolist()
                )

        if hourly_parts:
            activity = (
                pd.concat(hourly_parts)
                .groupby(["route_id", "hour"], as_index=False)
                ["stop_events"].sum()
            )
        else:
            activity = pd.DataFrame(
                columns=["route_id", "hour", "stop_events"]
            )

        # 8. Approximate length from stop positions
        lengths = []

        for route_id, points in sample_points.items():
            points.sort(
                key=lambda x: float(x[0])
                if pd.notna(x[0]) else -1
            )

            distance = 0
            previous = None
            valid_segments = 0

            for sequence, stop_id in points:
                coord = stop_coords.get(stop_id)

                if coord is None:
                    previous = None
                    continue

                lat = coord["stop_lat"]
                lon = coord["stop_lon"]

                if pd.isna(lat) or pd.isna(lon):
                    previous = None
                    continue

                current = (lat, lon)

                if previous is not None:
                    distance += haversine(
                        previous, current
                    )
                    valid_segments += 1

                previous = current

            lengths.append({
                "route_id": route_id,
                "approx_length_km": (
                    round(distance, 2)
                    if valid_segments > 0 else None
                )
            })

        length_df = pd.DataFrame(
            lengths,
            columns=["route_id", "approx_length_km"]
        )

        profiles = profiles.merge(
            length_df, on="route_id", how="left"
        )

        # 9. Save cleaned and engineered datasets
        routes.to_csv(
            OUT / f"{city}_routes_cleaned.csv",
            index=False
        )
        trips.to_csv(
            OUT / f"{city}_trips_cleaned.csv",
            index=False
        )
        stops.to_csv(
            OUT / f"{city}_stops_cleaned.csv",
            index=False
        )
        profiles.to_csv(
            OUT / f"{city}_route_profiles.csv",
            index=False
        )
        activity.to_csv(
            OUT / f"{city}_hourly_activity.csv",
            index=False
        )

        print("SUCCESS:", city)
        print("Routes:", len(routes))
        print("Trips:", len(trips))
        print("Stops:", len(stops))

    except Exception as e:
        print("FAILED:", city, str(e))

print("\nProcessing finished.")
