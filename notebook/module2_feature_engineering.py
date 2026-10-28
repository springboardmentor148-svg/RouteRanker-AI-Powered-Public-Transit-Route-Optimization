
from pathlib import Path
import math
import pandas as pd

# --------------------------------------------------
# ROUTERANKER - MODULE 2: FEATURE ENGINEERING
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

CITIES = ["ahmedabad", "chennai", "hyderabad", "mumbai", "pune"]

DAY_COLUMNS = [
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
]


def read_gtfs(city, filename, required=True):
    """Read a GTFS text file while preserving IDs as strings."""
    path = RAW_DIR / city / filename

    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing file: {path}")
        return None

    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        low_memory=False
    )


def parse_gtfs_time(value):
    """
    Convert GTFS HH:MM:SS into seconds.
    Supports extended hours such as 25:10:00.
    Returns None for invalid or missing values.
    """
    try:
        parts = str(value).strip().split(":")
        if len(parts) != 3:
            return None

        hours, minutes, seconds = map(int, parts)

        if hours < 0 or not (0 <= minutes < 60):
            return None
        if not (0 <= seconds < 60):
            return None

        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, TypeError):
        return None


def time_period(hour):
    """Classify the clock hour into a broad time period."""
    if 5 <= hour <= 11:
        return "Morning"
    elif 12 <= hour <= 16:
        return "Afternoon"
    elif 17 <= hour <= 20:
        return "Evening"
    return "Night"


def haversine_km(lat1, lon1, lat2, lon2):
    """Calculate approximate straight-line distance between coordinates."""
    values = [lat1, lon1, lat2, lon2]

    if any(pd.isna(v) for v in values):
        return None

    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
        return None
    if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        return None

    radius = 6371.0088

    lat1, lon1, lat2, lon2 = map(
        math.radians, values
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    a = min(1.0, max(0.0, a))

    return 2 * radius * math.asin(math.sqrt(a))


def add_quality(rows, city, filename, df, key_columns=None):
    """Record missing values, duplicate keys and row counts."""
    for column in df.columns:
        missing = df[column].isna() | df[column].astype(str).str.strip().eq("")

        rows.append({
            "city": city,
            "file": filename,
            "check": "missing_values",
            "column": column,
            "count": int(missing.sum()),
            "total_rows": len(df),
            "percent": round(missing.mean() * 100, 2) if len(df) else 0
        })

    if key_columns:
        available = [c for c in key_columns if c in df.columns]

        if available:
            duplicate_mask = df.duplicated(
                subset=available, keep=False
            )

            rows.append({
                "city": city,
                "file": filename,
                "check": "duplicate_key_rows",
                "column": ",".join(available),
                "count": int(duplicate_mask.sum()),
                "total_rows": len(df),
                "percent": round(duplicate_mask.mean() * 100, 2)
                if len(df) else 0
            })


def process_city(city, quality_rows):
    print(f"\nProcessing {city.title()}...")

    routes = read_gtfs(city, "routes.txt")
    trips = read_gtfs(city, "trips.txt")
    stop_times = read_gtfs(city, "stop_times.txt")
    stops = read_gtfs(city, "stops.txt")
    calendar = read_gtfs(city, "calendar.txt", required=False)

    add_quality(
        quality_rows, city, "routes.txt", routes, ["route_id"]
    )
    add_quality(
        quality_rows, city, "trips.txt", trips, ["trip_id"]
    )
    add_quality(
        quality_rows, city, "stop_times.txt",
        stop_times, ["trip_id", "stop_sequence"]
    )
    add_quality(
        quality_rows, city, "stops.txt", stops, ["stop_id"]
    )

    # Ensure expected columns exist, without changing the raw files.
    for column in ["route_id", "route_short_name",
                   "route_long_name", "route_type"]:
        if column not in routes.columns:
            routes[column] = ""

    for column in ["trip_id", "route_id", "service_id"]:
        if column not in trips.columns:
            trips[column] = ""

    for column in ["trip_id", "stop_id", "stop_sequence",
                   "arrival_time", "departure_time"]:
        if column not in stop_times.columns:
            stop_times[column] = ""

    for column in ["stop_id", "stop_lat", "stop_lon"]:
        if column not in stops.columns:
            stops[column] = ""

    # IDs are identifiers, not numeric measurements.
    routes = routes.drop_duplicates(subset=["route_id"])
    trips = trips.drop_duplicates(subset=["trip_id"])
    stops = stops.drop_duplicates(subset=["stop_id"])

    trips = trips[
        trips["trip_id"].ne("") & trips["route_id"].ne("")
    ].copy()

    # Convert stop sequence to numeric for reliable ordering.
    stop_times["sequence_num"] = pd.to_numeric(
        stop_times["stop_sequence"], errors="coerce"
    )

    # GTFS times can exceed 24 hours; preserve the service hour.
    for column in ["arrival_time", "departure_time"]:
        stop_times[f"{column}_seconds"] = (
            stop_times[column].map(parse_gtfs_time)
        )

    stop_times["departure_valid"] = (
        stop_times["departure_time_seconds"].notna()
    )

    # Check invalid time values separately.
    for column in ["arrival_time", "departure_time"]:
        invalid = (
            stop_times[column].astype(str).str.strip().ne("")
            & stop_times[f"{column}_seconds"].isna()
        )

        quality_rows.append({
            "city": city,
            "file": "stop_times.txt",
            "check": f"invalid_{column}",
            "column": column,
            "count": int(invalid.sum()),
            "total_rows": len(stop_times),
            "percent": round(invalid.mean() * 100, 2)
            if len(stop_times) else 0
        })

    # Join trip information to stop-time records.
    trip_stops = stop_times.merge(
        trips[["trip_id", "route_id", "service_id"]],
        on="trip_id",
        how="left",
        suffixes=("", "_trip"),
        indicator=True
    )

    unmatched_trips = int((trip_stops["_merge"] == "left_only").sum())

    quality_rows.append({
        "city": city,
        "file": "stop_times.txt",
        "check": "unmatched_trip_ids",
        "column": "trip_id",
        "count": unmatched_trips,
        "total_rows": len(stop_times),
        "percent": round(unmatched_trips / len(stop_times) * 100, 2)
        if len(stop_times) else 0
    })

    trip_stops = trip_stops.drop(columns="_merge")

    # Join stop coordinates for geographic checks and distance estimates.
    stop_coordinates = stops[["stop_id", "stop_lat", "stop_lon"]].copy()
    stop_coordinates["stop_lat"] = pd.to_numeric(
        stop_coordinates["stop_lat"], errors="coerce"
    )
    stop_coordinates["stop_lon"] = pd.to_numeric(
        stop_coordinates["stop_lon"], errors="coerce"
    )

    valid_coordinates = (
        stop_coordinates["stop_lat"].between(-90, 90)
        & stop_coordinates["stop_lon"].between(-180, 180)
    )

    quality_rows.append({
        "city": city,
        "file": "stops.txt",
        "check": "missing_or_invalid_coordinates",
        "column": "stop_lat,stop_lon",
        "count": int((~valid_coordinates).sum()),
        "total_rows": len(stops),
        "percent": round((~valid_coordinates).mean() * 100, 2)
        if len(stops) else 0
    })

    trip_stops = trip_stops.merge(
        stop_coordinates, on="stop_id", how="left"
    )

    # Sort each trip by stop sequence.
    trip_stops = trip_stops.sort_values(
        ["trip_id", "sequence_num"], na_position="last"
    )

    # First and last stop-time records for each trip.
    valid_sequence = trip_stops.dropna(subset=["sequence_num"])

    first_stops = valid_sequence.drop_duplicates(
        "trip_id", keep="first"
    ).copy()

    last_stops = valid_sequence.drop_duplicates(
        "trip_id", keep="last"
    ).copy()

    # Create departure-time features from each trip's first stop.
    departures = first_stops[
        ["trip_id", "route_id", "service_id", "departure_time",
         "departure_time_seconds"]
    ].copy()

    departures = departures[
        departures["departure_time_seconds"].notna()
    ].copy()

    departures["service_hour"] = (
        departures["departure_time_seconds"] // 3600
    ).astype(int)

    departures["clock_hour"] = departures["service_hour"] % 24

    departures["minute"] = (
        departures["departure_time_seconds"] % 3600 // 60
    ).astype(int)

    departures["time_period"] = departures["clock_hour"].map(
        time_period
    )

    # Save trip-level time features.
    departures.insert(0, "city", city)

    departures.to_csv(
        PROCESSED_DIR / f"{city}_trip_time_features.csv",
        index=False
    )

    # Calculate headway between consecutive scheduled departures.
    # Headways are grouped by route and service_id.
    headway_features = departures.sort_values(
        ["route_id", "service_id", "departure_time_seconds"]
    ).copy()

    headway_features["headway_minutes"] = (
        headway_features.groupby(
            ["route_id", "service_id"]
        )["departure_time_seconds"].diff() / 60
    )

    headway_features.to_csv(
        PROCESSED_DIR / f"{city}_trip_headway_features.csv",
        index=False
    )


    # Scheduled departures per route and service hour.
    hourly = (
        departures.groupby(
            ["route_id", "service_hour", "clock_hour", "time_period"],
            as_index=False
        )
        .agg(scheduled_departures=("trip_id", "nunique"))
    )

    hourly.insert(0, "city", city)
    hourly.to_csv(
        PROCESSED_DIR / f"{city}_trips_by_route_hour.csv",
        index=False
    )

    # Distinct scheduled trips and distinct stops served by each route.
    trip_counts = (
        trips.groupby("route_id", as_index=False)
        .agg(scheduled_trip_count=("trip_id", "nunique"))
    )

    stop_counts = (
        trip_stops.dropna(subset=["route_id"])
        .groupby("route_id", as_index=False)
        .agg(stop_count=("stop_id", "nunique"))
    )

    # Start and end hours based on scheduled stop times.
    first_hours = departures.groupby("route_id").agg(
        first_departure_seconds=("departure_time_seconds", "min")
    ).reset_index()

    last_arrivals = last_stops[
        ["route_id", "arrival_time_seconds", "departure_time_seconds"]
    ].copy()

    last_arrivals["end_seconds"] = last_arrivals[
        "arrival_time_seconds"
    ].combine_first(last_arrivals["departure_time_seconds"])

    last_hours = (
        last_arrivals.dropna(subset=["end_seconds"])
        .groupby("route_id", as_index=False)
        .agg(last_scheduled_seconds=("end_seconds", "max"))
    )

    # Approximate trip distance by summing straight-line distances
    # between consecutive stop coordinates. This is NOT road distance.
    distance_rows = []

    for trip_id, group in valid_sequence.groupby("trip_id", sort=False):
        group = group.reset_index(drop=True)
        segment_distances = []

        for i in range(1, len(group)):
            previous = group.iloc[i - 1]
            current = group.iloc[i]

            distance = haversine_km(
                previous["stop_lat"],
                previous["stop_lon"],
                current["stop_lat"],
                current["stop_lon"]
            )

            if distance is not None:
                segment_distances.append(distance)

        route_id = group["route_id"].iloc[0]

        if segment_distances:
            distance_rows.append({
                "route_id": route_id,
                "trip_id": trip_id,
                "estimated_straight_line_km": sum(segment_distances)
            })

    if distance_rows:
        trip_distances = pd.DataFrame(distance_rows)

        route_distances = (
            trip_distances.groupby("route_id", as_index=False)
            .agg(
                estimated_straight_line_route_km=(
                    "estimated_straight_line_km", "median"
                ),
                trips_with_distance=("trip_id", "nunique")
            )
        )
    else:
        route_distances = pd.DataFrame(
            columns=[
                "route_id",
                "estimated_straight_line_route_km",
                "trips_with_distance"
            ]
        )

    # Operating-day features from calendar.txt.
    operating = []

    if calendar is not None and not calendar.empty:
        calendar = calendar.drop_duplicates(subset=["service_id"])

        # Keep exact service IDs. This also handles combined IDs
        # such as "1,2,3,4,5,6,7" when the calendar uses that exact ID.
        trip_calendar = trips[
            ["route_id", "service_id"]
        ].merge(
            calendar, on="service_id", how="left"
        )

        for day in DAY_COLUMNS:
            if day not in trip_calendar.columns:
                trip_calendar[day] = ""

        for route_id, group in trip_calendar.groupby("route_id"):
            row = {"route_id": route_id}

            for day in DAY_COLUMNS:
                active = group[day].astype(str).str.strip().eq("1")
                row[f"operates_{day}"] = int(active.any())

            row["operating_day_count"] = sum(
                row[f"operates_{day}"] for day in DAY_COLUMNS
            )

            operating.append(row)

    operating_df = pd.DataFrame(operating)

    # Assemble the route profile.
    profile = routes[
        ["route_id", "route_short_name", "route_long_name", "route_type"]
    ].copy()

    profile = profile.merge(trip_counts, on="route_id", how="left")
    profile = profile.merge(stop_counts, on="route_id", how="left")
    profile = profile.merge(first_hours, on="route_id", how="left")
    profile = profile.merge(last_hours, on="route_id", how="left")
    profile = profile.merge(route_distances, on="route_id", how="left")

    if not operating_df.empty:
        profile = profile.merge(operating_df, on="route_id", how="left")
    else:
        for day in DAY_COLUMNS:
            profile[f"operates_{day}"] = pd.NA
        profile["operating_day_count"] = pd.NA

    profile["city"] = city

    profile["start_service_hour"] = (
        profile["first_departure_seconds"] // 3600
    )

    profile["end_service_hour"] = (
        profile["last_scheduled_seconds"] // 3600
    )

    # Count scheduled departures, not passengers, per route.
    departure_counts = departures.groupby("route_id").agg(
        trips_with_valid_departure=("trip_id", "nunique")
    ).reset_index()

    profile = profile.merge(
        departure_counts, on="route_id", how="left"
    )

    profile["scheduled_trip_count"] = profile[
        "scheduled_trip_count"
    ].fillna(0).astype(int)

    profile["stop_count"] = profile["stop_count"].fillna(0).astype(int)
    profile["trips_with_valid_departure"] = profile[
        "trips_with_valid_departure"
    ].fillna(0).astype(int)

    profile = profile.drop(
        columns=["first_departure_seconds", "last_scheduled_seconds"],
        errors="ignore"
    )

    profile.to_csv(
        REPORTS_DIR / f"{city}_route_profile.csv",
        index=False
    )

    # Route-level features across all cities are combined later.
    print(
        f"Completed {city.title()}: "
        f"{len(profile)} routes, "
        f"{len(departures)} trips with valid first-stop departure times."
    )

    return profile, hourly


def main():
    all_profiles = []
    all_hourly = []
    quality_rows = []

    for city in CITIES:
        city_dir = RAW_DIR / city

        if not city_dir.is_dir():
            print(f"Skipping {city}: raw data folder not found.")
            continue

        try:
            profile, hourly = process_city(city, quality_rows)
            all_profiles.append(profile)
            all_hourly.append(hourly)
        except Exception as error:
            print(f"ERROR processing {city}: {error}")
            quality_rows.append({
                "city": city,
                "file": "multiple",
                "check": "processing_error",
                "column": "",
                "count": 1,
                "total_rows": 0,
                "percent": 0,
                "details": str(error)
            })

    if all_profiles:
        combined_profile = pd.concat(
            all_profiles, ignore_index=True, sort=False
        )
        combined_profile.to_csv(
            REPORTS_DIR / "route_profile.csv", index=False
        )
        combined_profile.to_csv(
            PROCESSED_DIR / "route_features.csv", index=False
        )

    if all_hourly:
        pd.concat(
            all_hourly, ignore_index=True, sort=False
        ).to_csv(
            PROCESSED_DIR / "trips_by_route_hour.csv", index=False
        )

    pd.DataFrame(quality_rows).to_csv(
        REPORTS_DIR / "module2_data_quality_report.csv",
        index=False
    )

    # Feature dictionary for documentation.
    feature_dictionary = [
        ["city", "City containing the route", "Folder name", "Categorical"],
        ["route_id", "GTFS route identifier", "routes.txt", "Identifier"],
        ["route_short_name", "Short public route name when provided", "routes.txt", "Categorical"],
        ["route_long_name", "Long route name when provided", "routes.txt", "Categorical"],
        ["route_type", "GTFS transport mode code", "routes.txt", "Categorical/code"],
        ["scheduled_trip_count", "Number of distinct scheduled trips", "trips.txt", "Integer"],
        ["stop_count", "Number of distinct stops referenced by route trips", "stop_times.txt + trips.txt", "Integer"],
        ["scheduled_departures", "Distinct scheduled trip departures in a service hour", "First stop per trip", "Integer"],
["headway_minutes", "Minutes between consecutive scheduled first-stop departures for the same route and service_id; first trip in each group is blank.", "Difference between consecutive departure_time_seconds values, divided by 60, grouped by route_id and service_id.", "Numeric minutes"],
        ["service_hour", "GTFS service-time hour; may exceed 23", "departure_time", "Integer"],
        ["clock_hour", "Hour on a 0-23 clock", "service_hour modulo 24", "Integer"],
        ["minute", "Minute component of first-stop departure time", "departure_time", "Integer"],
        ["time_period", "Morning, afternoon, evening or night", "clock_hour", "Categorical"],
        ["start_service_hour", "Earliest valid first-stop departure hour", "stop_times.txt", "Integer"],
        ["end_service_hour", "Latest valid final-stop time hour", "stop_times.txt", "Integer"],
        ["operates_monday to operates_sunday", "Whether any matched calendar service operates on that day", "calendar.txt", "Binary"],
        ["operating_day_count", "Number of weekdays with any matched active service", "calendar.txt", "Integer"],
        ["estimated_straight_line_route_km", "Median estimated trip distance from consecutive stop coordinates", "stops.txt + stop_times.txt", "Approximate numeric"],
        ["trips_with_distance", "Number of trips with at least one valid distance segment", "Stop coordinates", "Integer"]
    ]





    pd.DataFrame(
        feature_dictionary,
        columns=["feature", "description", "source_or_method", "data_type"]
    ).to_csv(
        REPORTS_DIR / "module2_feature_dictionary.csv",
        index=False
    )

    assumptions = """# RouteRanker Module 2: Assumptions and Limitations

1. GTFS files describe scheduled transit service, not actual passenger counts.
2. Scheduled trips and departures must not be interpreted as passenger occupancy or crowding.
3. A trip's departure features use the first stop in stop_sequence.
4. GTFS times above 24:00 are retained as extended service hours.
5. Clock hour is service hour modulo 24; time-period labels use the clock hour.
6. Operating days are derived from matching trips.service_id to calendar.service_id.
7. Calendar exceptions are not applied unless calendar_dates.txt is available and implemented.
8. Missing or invalid data are reported; they are not automatically replaced with zero.
9. Route IDs and trip IDs are identifiers, not numeric measurements.
10. No shapes.txt file was found in the data directory. Route distances, where available,
    are approximate straight-line distances along consecutive stop coordinates. They are
    not road distances and can be inaccurate when coordinates are missing or stops are
    ordered incorrectly.
11. Operating-day flags indicate whether any matched service is active on a day; they
    do not prove that a bus runs on every calendar date in the feed's date range.
12. This script does not calculate passenger demand or true crowding.
13. Headway is calculated from scheduled first-stop departure times within each route_id and service_id group; it is not an observed real-world interval.
14. The first trip in each route/service group has no previous departure, so its headway is blank.
15. A zero headway means two or more trips share the same scheduled departure time; negative headways are not expected after sorting departures by time.
"""

    (REPORTS_DIR / "module2_assumptions_and_limitations.md").write_text(
        assumptions, encoding="utf-8"
    )

    print("\nModule 2 processing finished.")
    print(f"Route profiles and reports: {REPORTS_DIR}")
    print(f"Processed datasets: {PROCESSED_DIR}")


if __name__ == "__main__":
    main()


