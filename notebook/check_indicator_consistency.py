
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"

cities = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad"
]

for city in cities:
    indicator_path = REPORT_DIR / f"{city}_route_indicators.csv"

    if not indicator_path.exists():
        print(f"{city}: route indicator report not found")
        continue

    df = pd.read_csv(indicator_path, low_memory=False)

    required = [
        "scheduled_trip_count",
        "scheduled_stop_events"
    ]

    if not all(column in df.columns for column in required):
        print(f"{city}: expected indicator columns are missing")
        print("Available columns:", df.columns.tolist())
        continue

    no_trips = df["scheduled_trip_count"].fillna(0).eq(0)
    no_stop_events = df["scheduled_stop_events"].fillna(0).eq(0)

    print(f"\n{city.upper()}")
    print("Total routes in indicators:", len(df))
    print("Routes with zero scheduled trips:", int(no_trips.sum()))
    print("Routes with zero scheduled stop events:", int(no_stop_events.sum()))
    print(
        "Routes with zero trips but nonzero stop events:",
        int((no_trips & ~no_stop_events).sum())
    )
