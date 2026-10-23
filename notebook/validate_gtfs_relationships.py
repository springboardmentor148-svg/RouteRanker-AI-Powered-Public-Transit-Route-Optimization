
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

checks = []

def load_csv(city, filename):
    path = PROCESSED_DIR / city / f"{filename}.csv"

    if not path.exists():
        print(f"Missing file: {path}")
        return None

    return pd.read_csv(path, low_memory=False)

def check_relationship(city, child_df, child_column,
                       parent_df, parent_column,
                       child_table, parent_table):
    if child_df is None or parent_df is None:
        return

    if child_column not in child_df.columns:
        print(f"{city}: Missing column {child_column}")
        return

    if parent_column not in parent_df.columns:
        print(f"{city}: Missing column {parent_column}")
        return

    # Ignore blank references; report them separately
    child_values = child_df[child_column].dropna()
    parent_values = set(parent_df[parent_column].dropna())

    unmatched = int((~child_values.isin(parent_values)).sum())

    checks.append({
        "city": city,
        "child_table": child_table,
        "child_column": child_column,
        "parent_table": parent_table,
        "parent_column": parent_column,
        "checked_references": len(child_values),
        "unmatched_references": unmatched
    })

    print(
        f"{city}: {child_table}.{child_column} -> "
        f"{parent_table}.{parent_column}: "
        f"{unmatched} unmatched references"
    )

for city in cities:
    print(f"\nChecking GTFS relationships: {city}")

    routes = load_csv(city, "routes")
    trips = load_csv(city, "trips")
    stops = load_csv(city, "stops")
    stop_times = load_csv(city, "stop_times")

    check_relationship(
        city, trips, "route_id",
        routes, "route_id", "trips", "routes"
    )

    check_relationship(
        city, stop_times, "trip_id",
        trips, "trip_id", "stop_times", "trips"
    )

    check_relationship(
        city, stop_times, "stop_id",
        stops, "stop_id", "stop_times", "stops"
    )

report_path = REPORT_DIR / "gtfs_relationship_validation.csv"
pd.DataFrame(checks).to_csv(report_path, index=False)

print("\nRelationship validation report saved to:")
print(report_path)
