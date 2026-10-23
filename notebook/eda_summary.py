
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CITIES = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad",
]

CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"
REPORT_DIR = PROJECT_ROOT / "reports"


def read_csv(folder, filename):
    path = folder / filename

    if not path.exists():
        print(f"[WARNING] Missing file: {path}")
        return None

    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
        low_memory=False,
    )


def summarize_city(city, city_summary, route_summaries):
    folder = CLEANED_DIR / city

    routes = read_csv(folder, "routes.csv")
    trips = read_csv(folder, "trips.csv")
    stops = read_csv(folder, "stops.csv")
    stop_times = read_csv(folder, "stop_times.csv")

    city_summary.append({
        "city": city,
        "routes": len(routes) if routes is not None else None,
        "trips": len(trips) if trips is not None else None,
        "stops": len(stops) if stops is not None else None,
        "stop_time_records": (
            len(stop_times) if stop_times is not None else None
        ),
    })

    if routes is None or trips is None:
        print(f"[SKIP] {city}: routes or trips file is missing.")
        return

    if "route_id" not in routes.columns or "route_id" not in trips.columns:
        print(f"[SKIP] {city}: route_id column is missing.")
        return

    if "trip_id" not in trips.columns:
        print(f"[SKIP] {city}: trips.trip_id is missing.")
        return

    trips_valid = trips[
        trips["route_id"].astype(str).str.strip().ne("")
        & trips["trip_id"].astype(str).str.strip().ne("")
    ].copy()

    trip_counts = (
        trips_valid.groupby("route_id")["trip_id"]
        .nunique()
        .rename("scheduled_trips")
    )

    stop_counts = pd.Series(dtype="int64")

    if (
        stop_times is not None
        and "trip_id" in stop_times.columns
        and "stop_id" in stop_times.columns
    ):
        trip_route = trips_valid[["trip_id", "route_id"]].drop_duplicates()

        joined = stop_times.merge(
            trip_route,
            on="trip_id",
            how="inner",
        )

        joined = joined[
            joined["stop_id"].astype(str).str.strip().ne("")
        ]

        stop_counts = (
            joined.groupby("route_id")["stop_id"]
            .nunique()
            .rename("unique_stops")
        )

    route_summary = pd.DataFrame({
        "route_id": routes["route_id"].astype(str).str.strip().drop_duplicates()
    })

    route_summary = route_summary[route_summary["route_id"].ne("")]
    route_summary = route_summary.merge(
        trip_counts, on="route_id", how="left"
    )
    route_summary = route_summary.merge(
        stop_counts, on="route_id", how="left"
    )

    route_summary["scheduled_trips"] = (
        route_summary["scheduled_trips"].fillna(0).astype(int)
    )
    route_summary["unique_stops"] = (
        route_summary["unique_stops"].fillna(0).astype(int)
    )
    route_summary.insert(0, "city", city)

    route_summaries.append(route_summary)


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    city_summary = []
    route_summaries = []

    for city in CITIES:
        summarize_city(city, city_summary, route_summaries)

    city_df = pd.DataFrame(city_summary)
    city_output = REPORT_DIR / "eda_city_summary.csv"
    city_df.to_csv(city_output, index=False, encoding="utf-8-sig")

    if route_summaries:
        route_df = pd.concat(route_summaries, ignore_index=True)
    else:
        route_df = pd.DataFrame(
            columns=["city", "route_id", "scheduled_trips", "unique_stops"]
        )

    route_output = REPORT_DIR / "eda_route_summary.csv"
    route_df.to_csv(route_output, index=False, encoding="utf-8-sig")

    print("\nCITY SUMMARY")
    print(city_df.to_string(index=False))
    print(f"\nSaved: {city_output}")
    print(f"Saved: {route_output}")


if __name__ == "__main__":
    main()
