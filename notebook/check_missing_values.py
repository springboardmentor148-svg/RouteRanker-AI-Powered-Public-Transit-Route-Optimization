
from pathlib import Path
import pandas as pd

# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# All five cities in RouteRanker
CITIES = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad"
]

# Folders
CLEANED_DIR = BASE_DIR / "data" / "cleaned"
REPORT_DIR = BASE_DIR / "reports"

# GTFS files to check
GTFS_FILES = [
    "routes",
    "trips",
    "stops",
    "stop_times",
    "calendar",
    "calendar_dates",
    "frequencies",
    "shapes"
]


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    missing_data = []

    for city in CITIES:
        city_folder = CLEANED_DIR / city

        if not city_folder.exists():
            print(f"\nWARNING: Cleaned folder not found for {city}")
            continue

        print(f"\nChecking missing values: {city}")

        for file_name in GTFS_FILES:
            file_path = city_folder / f"{file_name}.csv"

            # Skip optional files that do not exist
            if not file_path.exists():
                continue

            try:
                df = pd.read_csv(
                    file_path,
                    dtype=str,
                    keep_default_na=True
                )

                # Check missing values in every column
                for column in df.columns:
                    missing_count = df[column].isna().sum()

                    # Also count empty or whitespace-only strings
                    if df[column].dtype == "object":
                        missing_count = (
                            df[column].isna()
                            | df[column].str.strip().eq("").fillna(False)
                        ).sum()

                    if missing_count > 0:
                        missing_data.append({
                            "city": city,
                            "file": file_name,
                            "column": column,
                            "missing_values": int(missing_count),
                            "total_rows": len(df),
                            "missing_percent": round(
                                missing_count / len(df) * 100, 2
                            ) if len(df) > 0 else 0
                        })

            except Exception as error:
                print(f"ERROR reading {file_path}: {error}")

    columns = [
        "city",
        "file",
        "column",
        "missing_values",
        "total_rows",
        "missing_percent"
    ]

    report = pd.DataFrame(missing_data, columns=columns)

    output_path = REPORT_DIR / "missing_values_report.csv"
    report.to_csv(output_path, index=False)

    if report.empty:
        print("\nNo missing values found in the available GTFS files.")
    else:
        print("\nMissing-value summary:")
        print(report.to_string(index=False))

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
