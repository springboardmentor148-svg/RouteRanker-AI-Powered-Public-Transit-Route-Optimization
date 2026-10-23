
from pathlib import Path
import pandas as pd

project = Path(__file__).resolve().parent.parent
data_folder = project / "data" / "processed"
report_folder = project / "reports"
report_folder.mkdir(parents=True, exist_ok=True)

# Essential columns for common GTFS files
required_columns = {
    "routes.csv": ["route_id"],
    "trips.csv": ["route_id", "service_id", "trip_id"],
    "stops.csv": ["stop_id", "stop_name"],
    "stop_times.csv": [
        "trip_id", "stop_id", "stop_sequence",
        "arrival_time", "departure_time"
    ],
    "calendar.csv": [
        "service_id", "monday", "tuesday", "wednesday",
        "thursday", "friday", "saturday", "sunday",
        "start_date", "end_date"
    ]
}

key_columns = {
    "routes.csv": ["route_id"],
    "trips.csv": ["trip_id"],
    "stops.csv": ["stop_id"],
    "calendar.csv": ["service_id"],
    "stop_times.csv": ["trip_id", "stop_sequence"]
}

report = []

for city_folder in sorted(data_folder.iterdir()):
    if not city_folder.is_dir():
        continue

    city = city_folder.name
    print(f"\n{'=' * 55}")
    print(f"CITY: {city.upper()}")
    print("=" * 55)

    for file in sorted(city_folder.rglob("*.csv")):
        try:
            df = pd.read_csv(file, dtype=str)
            df.columns = df.columns.str.strip()

            filename = file.name.lower()
            missing_columns = [
                col for col in required_columns.get(filename, [])
                if col not in df.columns
            ]

            duplicate_rows = int(df.duplicated().sum())
            blank_cells = int(
                df.replace(r"^\s*$", pd.NA, regex=True)
                  .isna().sum().sum()
            )

            duplicate_keys = None
            keys = key_columns.get(filename, [])

            if keys and all(col in df.columns for col in keys):
                # Count repeated key combinations, not whole rows
                duplicate_keys = int(
                    df.duplicated(subset=keys).sum()
                )

            print(f"\nFile: {file.relative_to(data_folder)}")
            print(f"Rows: {len(df)}")
            print(f"Columns ({len(df.columns)}): {list(df.columns)}")
            print(f"Blank/missing cells: {blank_cells}")
            print(f"Exact duplicate rows: {duplicate_rows}")
            print(f"Repeated key combinations: {duplicate_keys}")
            print(f"Missing required columns: {missing_columns}")

            report.append({
                "city": city,
                "file": str(file.relative_to(data_folder)),
                "rows": len(df),
                "column_count": len(df.columns),
                "columns": ", ".join(df.columns),
                "missing_cells": blank_cells,
                "duplicate_rows": duplicate_rows,
                "duplicate_keys": duplicate_keys,
                "missing_required_columns": ", ".join(missing_columns),
                "status": (
                    "CHECK REQUIRED COLUMNS"
                    if missing_columns else "Schema check passed"
                )
            })

        except Exception as error:
            print(f"Could not inspect {file}: {error}")
            report.append({
                "city": city,
                "file": str(file),
                "status": f"ERROR: {error}"
            })

report_path = report_folder / "dataset_validation_report.csv"
pd.DataFrame(report).to_csv(report_path, index=False)

print("\nValidation finished.")
print(f"Report saved to: {report_path}")
