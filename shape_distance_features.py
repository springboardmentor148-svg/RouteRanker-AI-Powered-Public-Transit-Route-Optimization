
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path("data/raw")
REPORT_DIR = Path("reports")
EARTH_RADIUS_KM = 6371.0


def calculate_shape_distances(shapes_path, city):
    shapes = pd.read_csv(shapes_path)

    required = {
        "shape_id",
        "shape_pt_lat",
        "shape_pt_lon",
        "shape_pt_sequence",
    }

    if not required.issubset(shapes.columns):
        print(f"{city}: required shape columns are missing.")
        return pd.DataFrame()

    shapes["shape_pt_lat"] = pd.to_numeric(
        shapes["shape_pt_lat"], errors="coerce"
    )
    shapes["shape_pt_lon"] = pd.to_numeric(
        shapes["shape_pt_lon"], errors="coerce"
    )
    shapes["shape_pt_sequence"] = pd.to_numeric(
        shapes["shape_pt_sequence"], errors="coerce"
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

    results = (
        shapes.groupby("shape_id")
        .agg(
            shape_distance_km=("segment_km", "sum"),
            point_count=("shape_pt_sequence", "count"),
            max_segment_km=("segment_km", "max"),
        )
        .reset_index()
    )

    results.insert(0, "city", city)

    results["distance_quality"] = np.where(
        results["point_count"] < 2,
        "Review: fewer than 2 points",
        np.where(
            results["max_segment_km"] > 1,
            "Review: segment over 1 km",
            "Calculated",
        ),
    )

    return results


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    all_results = []

    for city_dir in sorted(DATA_DIR.iterdir()):
        if not city_dir.is_dir():
            continue

        shapes_path = city_dir / "shapes.txt"

        if not shapes_path.exists():
            print(f"{city_dir.name}: no shapes.txt; skipped.")
            continue

        result = calculate_shape_distances(
            shapes_path, city_dir.name
        )

        if not result.empty:
            all_results.append(result)

            print(
                f"{city_dir.name}: "
                f"{len(result)} shapes processed."
            )

    if not all_results:
        print("No shape-distance results were generated.")
        return

    final = pd.concat(all_results, ignore_index=True)

    output_path = REPORT_DIR / "shape_distances.csv"
    final.to_csv(output_path, index=False)

    print("\nTotal shapes:", len(final))
    print("Cities represented:", final["city"].nunique())
    print("Rows flagged for review:", int(
        final["distance_quality"].str.startswith("Review").sum()
    ))
    print("Saved:", output_path)


if __name__ == "__main__":
    main()
