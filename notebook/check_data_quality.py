
from pathlib import Path
import pandas as pd

# Project folders
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

files_to_check = [
    "routes",
    "trips",
    "stops",
    "stop_times"
]

# GTFS tables and their expected unique identifiers
key_columns = {
    "routes": "route_id",
    "trips": "trip_id",
    "stops": "stop_id",
    "stop_times": None
}

summary = []
column_details = []

for city in cities:
    city_dir = PROCESSED_DIR / city

    for file_name in files_to_check:
        file_path = city_dir / f"{file_name}.csv"

        if not file_path.exists():
            print(f"File not found: {file_path}")
            continue

        try:
            df = pd.read_csv(file_path, low_memory=False)
        except Exception as error:
            print(f"Could not read {file_path}: {error}")
            continue

        print(f"\nChecking {city} - {file_name}")
        print(f"Rows: {len(df)}, Columns: {len(df.columns)}")

        # Duplicate entire rows
        duplicate_rows = int(df.duplicated().sum())

        # Missing cells across the file
        missing_cells = int(df.isna().sum().sum())

        # Duplicate values in the primary key
        key = key_columns[file_name]
        duplicate_keys = 0

        if key and key in df.columns:
            duplicate_keys = int(
                df[key].dropna().duplicated().sum()
            )

        summary.append({
            "city": city,
            "file": file_name,
            "rows": len(df),
            "columns": len(df.columns),
            "duplicate_rows": duplicate_rows,
            "duplicate_key_values": duplicate_keys,
            "missing_cells": missing_cells
        })

        # Inspect each column
        for column in df.columns:
            column_details.append({
                "city": city,
                "file": file_name,
                "column": column,
                "data_type": str(df[column].dtype),
                "missing_values": int(df[column].isna().sum()),
                "missing_percent": round(
                    df[column].isna().mean() * 100, 2
                ),
                "unique_values": int(df[column].nunique())
            })

# Save reports
summary_df = pd.DataFrame(summary)
details_df = pd.DataFrame(column_details)

summary_path = REPORT_DIR / "data_quality_summary.csv"
details_path = REPORT_DIR / "column_quality_details.csv"

summary_df.to_csv(summary_path, index=False)
details_df.to_csv(details_path, index=False)

print("\n========== DATA QUALITY SUMMARY ==========")

if not summary_df.empty:
    print(summary_df.to_csv(index=False))
else:
    print("No processed CSV files were found.")

print(f"\nSummary saved to: {summary_path}")
print(f"Column details saved to: {details_path}")
