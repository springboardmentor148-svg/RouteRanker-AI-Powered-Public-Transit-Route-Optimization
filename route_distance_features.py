
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/raw")
REPORT_DIR = Path("reports")
EARTH_RADIUS_KM = 6371.0


def calculate_shapes(shapes_path, city):
    shapes = pd.read_csv(shapes_path)

    required = {
        "shape_id",
        "shape_pt_lat",
        "shape_pt_lon",
        "shape_pt_sequence",
    }

    if not required.issubset(shapes.columns):
        print(f"{city}: missing required shape columns.")
        return pd.DataFrame()

    for column in [
        "shape_pt_lat",
        "shape_pt_lon",
        "shape_pt_sequence",
    ]:
        shapes[column] = pd.to_numeric(
            shapes[column], errors="coerce"
        )

    shapes = shapes.dropna(
        subset=[
            "shape_id",
            "shape_pt_lat",
            "shape_pt_lon",
            "shape_pt_sequence",
        ]
    )

    shapes = shapes.sort_values(
        ["shape_id", "shape_pt_sequence"]
    ).copy()

    grouped = shapes.groupby("shape_id", sort=False)

    previous_lat = np.radians(
        grouped["shape_pt_lat"].shift()
    )
    previous_lon = np.radians(
        grouped["shape_pt_lon"].shift()
    )
    current_lat = np.radians(shapes["shape_pt_lat"])
    current_lon = np.radians(shapes["shape_pt_lon"])

    delta_lat = current_lat - previous_lat
    delta_lon = current_lon - previous_lon

    a = (
        np.sin(delta_lat / 2) ** 2
        + np.cos(previous_lat)
        * np.cos(current_lat)
        * np.sin(delta_lon / 2) ** 2
    )

    shapes["segment_km"] = (
        2
        * EARTH_RADIUS_KM
        * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    )

    first_point = grouped.cumcount() == 0
    shapes.loc[first_point, "segment_km"] = 0.0

    return (
        shapes.groupby("shape_id")
        .agg(
            shape_distance_km=("segment_km", "sum"),
            point_count=("shape_pt_sequence", "count"),
            max_segment_km=("segment_km", "max"),
        )
        .reset_index()
    )


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    all_routes = []

    for city_dir in sorted(DATA_DIR.iterdir()):
        if not city_dir.is_dir():
            continue

        trips_path = city_dir / "trips.txt"
        shapes_path = city_dir / "shapes.txt"

        if not trips_path.exists():
            continue

        trips = pd.read_csv(trips_path, dtype=str)

        if not {"route_id", "shape_id"}.issubset(trips.columns):
            print(f"{city_dir.name}: trips missing route_id/shape_id.")
            continue

        if not shapes_path.exists():
            print(f"{city_dir.name}: no shapes.txt; distances unavailable.")
            continue

        shape_features = calculate_shapes(
            shapes_path, city_dir.name
        )
        shape_features["shape_id"] = shape_features["shape_id"].astype(str)

        if shape_features.empty:
            continue

        shape_features.insert(0, "city", city_dir.name)

        trips = trips.dropna(
            subset=["route_id", "shape_id"]
        ).copy()

        trips["shape_id"] = trips["shape_id"].astype(str)

        trips = trips[["route_id", "shape_id"]].drop_duplicates()

        mapped = trips.merge(
            shape_features,
            on="shape_id",
            how="left",
            validate="many_to_one",
        )

        mapped = mapped.dropna(
            subset=["shape_distance_km"]
        )

        if mapped.empty:
            print(f"{city_dir.name}: no trips mapped to shape distances.")
            continue

        route_features = (
            mapped.groupby("route_id")
            .agg(
                shape_count=("shape_id", "nunique"),
                minimum_shape_distance_km=(
                    "shape_distance_km", "min"
                ),
                median_shape_distance_km=(
                    "shape_distance_km", "median"
                ),
                maximum_shape_distance_km=(
                    "shape_distance_km", "max"
                ),
                shapes_with_large_gaps=(
                    "max_segment_km",
                    lambda values: int((values > 1).sum()),
                ),
            )
            .reset_index()
        )

        route_features.insert(0, "city", city_dir.name)

        route_features["distance_quality"] = np.where(
            route_features["shapes_with_large_gaps"] > 0,
            "Review: shape gap over 1 km",
            "Calculated",
        )

        all_routes.append(route_features)

        print(
            f"{city_dir.name}: "
            f"{len(route_features)} routes with shape distances."
        )

    if not all_routes:
        print("No route-distance features generated.")
        return

    result = pd.concat(all_routes, ignore_index=True)

    output_path = REPORT_DIR / "route_distance_features.csv"
    result.to_csv(output_path, index=False)

    print("\nTotal route rows:", len(result))
    print("Cities represented:", result["city"].nunique())
    print(
        "Routes flagged for review:",
        int(
            result["distance_quality"]
            .str.startswith("Review")
            .sum()
        ),
    )
    print("Saved:", output_path)


if __name__ == "__main__":
    main()

