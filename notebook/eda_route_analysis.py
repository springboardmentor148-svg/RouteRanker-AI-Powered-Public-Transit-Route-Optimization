
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

CITIES = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad",
]

summary_rows = []
route_results = []

for city in CITIES:
    path = REPORT_DIR / f"{city}_route_indicators.csv"

    if not path.exists():
        print(f"Skipping {city}: report not found at {path}")
        continue

    df = pd.read_csv(path, low_memory=False)

    if "scheduled_trip_count" not in df.columns:
        print(f"Skipping {city}: scheduled_trip_count column missing")
        continue

    trips = pd.to_numeric(
        df["scheduled_trip_count"], errors="coerce"
    ).fillna(0)

    summary_rows.append({
        "city": city,
        "routes_analyzed": len(df),
        "routes_with_trips": int((trips > 0).sum()),
        "routes_without_trips": int((trips == 0).sum()),
        "total_scheduled_trips": int(trips.sum()),
        "average_trips_per_route": round(trips.mean(), 2),
        "median_trips_per_route": round(trips.median(), 2),
        "maximum_trips_on_one_route": int(trips.max()),
    })

    temp = df.copy()
    temp["scheduled_trip_count"] = trips
    temp["city"] = city

    route_results.append(temp)

if summary_rows:
    summary = pd.DataFrame(summary_rows)
    summary_path = REPORT_DIR / "eda_city_summary.csv"
    summary.to_csv(summary_path, index=False)

    print("\n=== CITY-LEVEL EDA SUMMARY ===")
    print(summary.to_string(index=False))
    print(f"\nSaved: {summary_path}")

if route_results:
    all_routes = pd.concat(route_results, ignore_index=True)

    # Top 10 routes by scheduled trip count in each city
    top_routes = (
        all_routes.sort_values(
            ["city", "scheduled_trip_count"],
            ascending=[True, False]
        )
        .groupby("city", group_keys=False)
        .head(10)
    )

    top_path = REPORT_DIR / "eda_top_routes.csv"
    top_routes.to_csv(top_path, index=False)

    print("\n=== TOP ROUTES BY CITY ===")
    for city in CITIES:
        city_top = top_routes[top_routes["city"] == city]

        if not city_top.empty:
            print(f"\n{city.upper()}")
            columns = [
                col for col in [
                    "route_id",
                    "route_short_name",
                    "route_long_name",
                    "scheduled_trip_count",
                ]
                if col in city_top.columns
            ]
            print(city_top[columns].to_string(index=False))

    print(f"\nSaved: {top_path}")
