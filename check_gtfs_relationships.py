
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")

def load_table(folder, filename):
    path = folder / filename
    if not path.exists():
        return None
    return pd.read_csv(path, dtype=str, low_memory=False).fillna("")

print("ROUTERANKER - RELATIONSHIP VALIDATION")
print("=" * 50)

if not DATA_DIR.exists():
    print(f"Folder not found: {DATA_DIR.resolve()}")
else:
    for city in sorted(DATA_DIR.iterdir()):
        if not city.is_dir():
            continue

        print(f"\nCITY: {city.name}")
        print("-" * 40)

        routes = load_table(city, "routes.txt")
        trips = load_table(city, "trips.txt")
        stops = load_table(city, "stops.txt")
        stop_times = load_table(city, "stop_times.txt")

        if any(x is None for x in [routes, trips, stops, stop_times]):
            print("SKIPPED: One or more required files are missing.")
            continue

        required_columns = {
            "routes": (routes, ["route_id"]),
            "trips": (trips, ["trip_id", "route_id"]),
            "stops": (stops, ["stop_id"]),
            "stop_times": (stop_times, ["trip_id", "stop_id"]),
        }

        missing_columns = []
        for name, (df, columns) in required_columns.items():
            for column in columns:
                if column not in df.columns:
                    missing_columns.append(f"{name}.{column}")

        if missing_columns:
            print("Missing columns:", ", ".join(missing_columns))
            continue

        route_ids = set(routes["route_id"])
        trip_ids = set(trips["trip_id"])
        stop_ids = set(stops["stop_id"])

        invalid_routes = (
            ~trips["route_id"].isin(route_ids)
        ).sum()

        invalid_trips = (
            ~stop_times["trip_id"].isin(trip_ids)
        ).sum()

        invalid_stops = (
            ~stop_times["stop_id"].isin(stop_ids)
        ).sum()

        print("Trips referencing unknown routes:", invalid_routes)
        print("Stop times referencing unknown trips:", invalid_trips)
        print("Stop times referencing unknown stops:", invalid_stops)

        if invalid_routes + invalid_trips + invalid_stops == 0:
            print("RESULT: All checked ID relationships passed.")
        else:
            print("RESULT: Investigate the reported mismatches.")

print("\nRelationship validation complete.")

