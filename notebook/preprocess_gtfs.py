
from pathlib import Path
import pandas as pd

# RouteRanker project folders
PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
PROCESSED = PROJECT / "data" / "processed"
REPORTS = PROJECT / "reports"

# Use only these four cities
CITIES = ["ahmedabad", "chennai", "mumbai", "pune"]

# Required columns for core GTFS files
REQUIRED = {
    "routes": ["route_id"],
    "trips": ["route_id", "service_id", "trip_id"],
    "stops": ["stop_id", "stop_lat", "stop_lon"],
    "stop_times": [
        "trip_id", "stop_id", "stop_sequence",
        "arrival_time", "departure_time"
    ],
}

REPORTS.mkdir(parents=True, exist_ok=True)

quality_rows = []
relationship_rows = []


def record_quality(city, filename, df, original_rows, removed_duplicates):
    quality_rows.append({
        "city": city,
        "file": filename,
        "rows_before": original_rows,
        "rows_after": len(df),
        "columns": len(df.columns),
        "exact_duplicates_removed": removed_duplicates,
        "missing_cells": int(df.isna().sum().sum()),
        "missing_required_columns": ", ".join(
            c for c in REQUIRED.get(filename, [])
            if c not in df.columns
        ),
    })


for city in CITIES:
    source = RAW / city
    destination = PROCESSED / city
    destination.mkdir(parents=True, exist_ok=True)

    print(f"\n{'=' * 50}\nCITY: {city.upper()}")

    if not source.exists():
        print("Raw folder not found:", source)
        continue

    tables = {}

    # Read and standardize the core GTFS tables
    for name in ["routes", "trips", "stops", "stop_times"]:
        txt_path = source / f"{name}.txt"

        if not txt_path.exists():
            print(f"Missing source file: {name}.txt")
            continue

        try:
            df = pd.read_csv(
                txt_path,
                dtype=str,
                keep_default_na=False,
                low_memory=False
            )

            original_rows = len(df)

            # Remove extra spaces from column names and text values
            df.columns = df.columns.str.strip()
            for col in df.columns:
                df[col] = df[col].map(
                    lambda value: value.strip()
                    if isinstance(value, str) else value
                )

            # Standardize empty strings as missing values
            df = df.replace(r"^\s*$", pd.NA, regex=True)

            missing_columns = [
                col for col in REQUIRED[name]
                if col not in df.columns
            ]

            # Remove exact duplicate rows only; report the count
            before_dedup = len(df)
            df = df.drop_duplicates().copy()
            removed = before_dedup - len(df)

            # Convert selected fields to numeric safely
            numeric_columns = {
                "routes": ["route_type"],
                "trips": ["direction_id"],
                "stops": ["stop_lat", "stop_lon"],
                "stop_times": ["stop_sequence"],
            }

            for col in numeric_columns[name]:
                if col in df.columns:
                    df[col] = pd.to_numeric(
                        df[col], errors="coerce"
                    )

            # Validate stop coordinates when present
            if name == "stops":
                if "stop_lat" in df.columns:
                    bad_lat = (
                        df["stop_lat"].notna()
                        & ~df["stop_lat"].between(-90, 90)
                    )
                    df.loc[bad_lat, "stop_lat"] = pd.NA

                if "stop_lon" in df.columns:
                    bad_lon = (
                        df["stop_lon"].notna()
                        & ~df["stop_lon"].between(-180, 180)
                    )
                    df.loc[bad_lon, "stop_lon"] = pd.NA

            # Save processed data
            output = destination / f"{name}.csv"
            df.to_csv(output, index=False)

            tables[name] = df

            record_quality(
                city, name, df, original_rows, removed
            )

            print(
                f"{name}: {len(df)} rows, "
                f"{len(df.columns)} columns; "
                f"exact duplicates removed: {removed}"
            )

            if missing_columns:
                print("  Missing required columns:", missing_columns)

        except Exception as error:
            print(f"Error processing {name}.txt: {error}")

    # Check relationships between GTFS tables
    def check_relationship(
        child_name, child_col, parent_name, parent_col
    ):
        if child_name not in tables or parent_name not in tables:
            return

        child = tables[child_name]
        parent = tables[parent_name]

        if child_col not in child.columns:
            return
        if parent_col not in parent.columns:
            return

        parent_ids = set(parent[parent_col].dropna().astype(str))
        values = child[child_col]

        nonblank = values.notna()
        invalid = nonblank & ~values.astype(str).isin(parent_ids)

        relationship_rows.append({
            "city": city,
            "relationship": (
                f"{child_name}.{child_col} -> "
                f"{parent_name}.{parent_col}"
            ),
            "nonblank_values": int(nonblank.sum()),
            "unmatched_values": int(invalid.sum()),
            "blank_values": int((~nonblank).sum()),
        })

    check_relationship("trips", "route_id", "routes", "route_id")
    check_relationship("stop_times", "trip_id", "trips", "trip_id")
    check_relationship("stop_times", "stop_id", "stops", "stop_id")

# Save reports for mentor review
pd.DataFrame(quality_rows).to_csv(
    REPORTS / "preprocessing_quality_report.csv",
    index=False
)

pd.DataFrame(relationship_rows).to_csv(
    REPORTS / "gtfs_relationship_report.csv",
    index=False
)

print("\nPreprocessing completed.")
print("Processed files:", PROCESSED)
print("Quality report:", REPORTS / "preprocessing_quality_report.csv")
print("Relationship report:", REPORTS / "gtfs_relationship_report.csv")
print("Cities processed:", ", ".join(CITIES))
