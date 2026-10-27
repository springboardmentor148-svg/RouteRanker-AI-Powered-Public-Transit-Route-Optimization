
from pathlib import Path

import pandas as pd


# Project folders
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
REPORT_DIR = PROJECT_DIR / "reports"

# Start with Delhi only; we'll expand to all eight cities later.
CITIES = [
    "BANGALORE",
    "CHENNAI",
    "DEHLI",
    "GUJARATI",
    "KOCHI",
    "MUMBAI",
    "PUNE",
    "TELANGANA",
]


def time_to_seconds(time_series):
    """Convert GTFS HH:MM:SS strings into seconds after midnight."""
    parts = time_series.str.split(":", expand=True).astype(int)

    return (
        parts[0] * 3600
        + parts[1] * 60
        + parts[2]
    )


def build_trip_features(city):
    """Create one row of scheduled features per trip."""
    stop_times_path = DATA_DIR / city / "stop_times.txt"

    print(f"Reading {city} stop times...")

    stop_times = pd.read_csv(
        stop_times_path,
        dtype={
            "trip_id": str,
            "arrival_time": str,
            "departure_time": str,
            "stop_id": str,
        },
    )

    stop_times["stop_sequence"] = pd.to_numeric(
        stop_times["stop_sequence"],
        errors="raise",
    )

    stop_times["arrival_seconds"] = time_to_seconds(
        stop_times["arrival_time"]
    )

    stop_times["departure_seconds"] = time_to_seconds(
        stop_times["departure_time"]
    )

    stop_times = stop_times.sort_values(
        ["trip_id", "stop_sequence"]
    )

    features = (
        stop_times.groupby("trip_id")
        .agg(
            first_departure_seconds=(
                "departure_seconds", "first"
            ),
            last_arrival_seconds=(
                "arrival_seconds", "last"
            ),
            number_of_stops=("stop_id", "count"),
        )
        .reset_index()
    )

     
    # Calculate trip duration in seconds.
    features["trip_duration_seconds"] = (
        features["last_arrival_seconds"]
        - features["first_departure_seconds"]
    )

    # Flag trips that need the midnight correction.
    midnight_crossing = features["trip_duration_seconds"] < 0
    features["midnight_corrected"] = midnight_crossing

    # Correct for one midnight crossing.
    features.loc[midnight_crossing, "trip_duration_seconds"] += 24 * 60 * 60

    # Convert duration from seconds to minutes.
    features["trip_duration_minutes"] = (
        features["trip_duration_seconds"] / 60
    )

    # Flag unusually long trips for review; do not delete them.
    features["duration_quality"] = "OK"
    features.loc[
        features["trip_duration_minutes"] > 240,
        "duration_quality"
    ] = "Review"

    # Flag schedules containing extreme GTFS times (48 hours or more).
    features["extreme_schedule_time"] = (
        (features["first_departure_seconds"] >= 48 * 3600)
        | (features["last_arrival_seconds"] >= 48 * 3600)
    )
    
   

    # Time-of-day features
    features["departure_hour"] = (
        features["first_departure_seconds"] // 3600
    ).astype(int)

    def classify_departure(hour):
        if 5 <= hour < 7:
            return "Early morning"
        elif 7 <= hour < 10:
            return "Morning peak"
        elif 10 <= hour < 15:
            return "Midday"
        elif 15 <= hour < 17:
            return "Afternoon peak"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"

    features["departure_period"] = (
        features["departure_hour"].apply(classify_departure)
    )

    
    # Add route IDs from the cleaned trip records.
    cleaned_trips_path = REPORT_DIR / f"{city}_trips_cleaned.txt"

    if city == "DEHLI" and cleaned_trips_path.exists():
        trips = pd.read_csv(cleaned_trips_path, dtype=str)
    else:
        trips_path = DATA_DIR / city / "trips.txt"
        trips = pd.read_csv(trips_path, dtype=str)

    route_lookup = trips[["trip_id", "route_id"]].drop_duplicates(
        subset=["trip_id"]
    )

    features = features.merge(
        route_lookup,
        on="trip_id",
        how="left",
        validate="one_to_one",
    )

    features["city"] = city

    return features






def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    for city in CITIES:
        print(f"\nProcessing {city}...")

        try:
            features = build_trip_features(city)

            trip_output = REPORT_DIR / f"{city}_trip_features.csv"
            features.to_csv(trip_output, index=False)

           
            # Original route-level statistics, including all scheduled trips.
            route_features = (
                features.groupby(["city", "route_id"], as_index=False)
                .agg(
                    scheduled_trip_count=("trip_id", "nunique"),
                    average_trip_duration_minutes=("trip_duration_minutes", "mean"),
                    average_stops_per_trip=("number_of_stops", "mean"),
                    trips_flagged_for_review=(
                        "duration_quality",
                        lambda s: (s == "Review").sum(),
                    ),
                    extreme_schedule_trip_count=(
                        "extreme_schedule_time", "sum"
                    ),
                    midnight_corrected_trip_count=(
                        "midnight_corrected", "sum"
                    ),
                )
            )

            # Calculate a separate average using only trips not flagged
            # for duration review. Keep the original average unchanged.
            reliable_durations = (
                features.loc[features["duration_quality"] == "OK"]
                .groupby(["city", "route_id"])["trip_duration_minutes"]
                .mean()
                .rename("average_unflagged_trip_duration_minutes")
                .reset_index()
            )

            route_features = route_features.merge(
                reliable_durations,
                on=["city", "route_id"],
                how="left",
                validate="one_to_one",
            )

            # Make data coverage explicit for each route.
            route_features["unflagged_trip_count"] = (
                route_features["scheduled_trip_count"]
                - route_features["trips_flagged_for_review"]
            )

            route_features["route_duration_quality"] = "Has unflagged trips"
            route_features.loc[
                route_features["unflagged_trip_count"] == 0,
                "route_duration_quality",
            ] = "No unflagged trips"

            # Round numeric averages for readability.
            average_columns = [
                "average_trip_duration_minutes",
                "average_stops_per_trip",
                "average_unflagged_trip_duration_minutes",
            ]

            route_features[average_columns] = route_features[
                average_columns
            ].round(2)

            route_output = REPORT_DIR / f"{city}_route_features.csv"
            route_features.to_csv(route_output, index=False)

            print(f"  Trips processed: {len(features)}")
            print(f"  Routes processed: {len(route_features)}")
            print(f"  Trip features saved: {trip_output}")
            print(f"  Route features saved: {route_output}")

        except Exception as error:
            print(f"  ERROR processing {city}: {error}")

    print("\nFEATURE ENGINEERING RUN FINISHED.")


if __name__ == "__main__":
    main()
