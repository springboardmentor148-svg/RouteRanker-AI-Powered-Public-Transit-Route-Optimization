
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

all_missing_routes = []

for city in cities:
    city_dir = PROCESSED_DIR / city

    routes_path = city_dir / "routes.csv"
    trips_path = city_dir / "trips.csv"

    if not routes_path.exists() or not trips_path.exists():
        print(f"Missing routes or trips file for {city}")
        continue

    routes = pd.read_csv(routes_path, low_memory=False)
    trips = pd.read_csv(trips_path, low_memory=False)

    if "route_id" not in routes.columns:
        print(f"{city}: routes.csv has no route_id column")
        continue

    if "route_id" not in trips.columns:
        print(f"{city}: trips.csv has no route_id column")
        continue

    used_route_ids = set(trips["route_id"].dropna().unique())

    missing_routes = routes[
        ~routes["route_id"].isin(used_route_ids)
    ].copy()

    missing_routes.insert(0, "city", city)

    print(
        f"{city}: {len(missing_routes)} route records "
        "have no matching trip"
    )

    all_missing_routes.append(missing_routes)

if all_missing_routes:
    result = pd.concat(all_missing_routes, ignore_index=True)

    output_path = REPORT_DIR / "routes_without_trips.csv"
    result.to_csv(output_path, index=False)

    print(f"\nDetailed report saved to: {output_path}")
else:
    print("No routes-without-trips report was generated.")
