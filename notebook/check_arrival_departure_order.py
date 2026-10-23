
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "processed"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

CITIES = ["ahmedabad", "chennai", "mumbai", "pune", "hyderabad"]


def time_to_seconds(value):
    if pd.isna(value):
        return None

    try:
        hours, minutes, seconds = map(
            int, str(value).strip().split(":")
        )

        if hours < 0 or not 0 <= minutes <= 59:
            return None
        if not 0 <= seconds <= 59:
            return None

        # Supports GTFS times beyond midnight, e.g. 25:10:00
        return hours * 3600 + minutes * 60 + seconds

    except (ValueError, TypeError):
        return None


results = []

for city in CITIES:
    path = DATA_DIR / city / "stop_times.csv"

    if not path.exists():
        print(f"{city}: stop_times.csv not found")
        continue

    df = pd.read_csv(path, low_memory=False)

    required = [
        "trip_id", "stop_sequence",
        "arrival_time", "departure_time"
    ]

    if not all(column in df.columns for column in required):
        print(f"{city}: required columns are missing")
        continue

    df["arrival_seconds"] = df["arrival_time"].map(time_to_seconds)
    df["departure_seconds"] = df["departure_time"].map(time_to_seconds)
    df["stop_sequence_numeric"] = pd.to_numeric(
        df["stop_sequence"], errors="coerce"
    )

    # Check departure is not earlier than arrival at the same stop.
    same_stop_bad = (
        df["arrival_seconds"].notna()
        & df["departure_seconds"].notna()
        & (df["departure_seconds"] < df["arrival_seconds"])
    )

    # Sort stops within each trip to check travel-time progression.
    ordered = df.dropna(
        subset=[
            "trip_id", "stop_sequence_numeric",
            "arrival_seconds", "departure_seconds"
        ]
    ).sort_values(["trip_id", "stop_sequence_numeric"])

    previous_departure = ordered.groupby("trip_id")[
        "departure_seconds"
    ].shift(1)

    previous_trip = ordered["trip_id"].eq(
        ordered["trip_id"].shift(1)
    )

    # A later stop should not arrive before the previous stop's departure.
    between_stop_bad = (
        previous_trip
        & (ordered["arrival_seconds"] < previous_departure)
    )

    results.append({
        "city": city,
        "total_rows": len(df),
        "departure_before_arrival": int(same_stop_bad.sum()),
        "arrival_before_previous_departure": int(
            between_stop_bad.sum()
        )
    })

result = pd.DataFrame(results)
output_path = REPORT_DIR / "arrival_departure_order_report.csv"
result.to_csv(output_path, index=False)

print(result.to_csv(index=False))
print(f"Report saved to: {output_path}")
