
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

REQUIRED_FILES = [
    "routes.csv",
    "trips.csv",
    "stops.csv",
    "stop_times.csv",
]

ID_COLUMNS = {
    "routes.csv": ["route_id"],
    "trips.csv": ["trip_id", "route_id"],
    "stops.csv": ["stop_id"],
    "stop_times.csv": ["trip_id", "stop_id"],
}


def load_csv(folder, filename):
    path = folder / filename
    if not path.exists():
        return None

    return pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
        low_memory=False,
    )


def add_check(report, city, file_name, check, issues, details=""):
    report.append({
        "city": city,
        "file": file_name,
        "check": check,
        "issue_count": int(issues),
        "details": details,
    })


def validate_city(city, report):
    folder = CLEANED_DIR / city

    if not folder.exists():
        add_check(report, city, "", "folder_exists", 1, "Cleaned folder missing")
        return

    data = {}

    for filename in REQUIRED_FILES:
        df = load_csv(folder, filename)

        if df is None:
            add_check(report, city, filename, "file_exists", 1, "File missing")
        else:
            data[filename] = df
            add_check(report, city, filename, "file_exists", 0, "Found")

    # Check required ID columns and duplicate IDs.
    for filename, columns in ID_COLUMNS.items():
        if filename not in data:
            continue

        df = data[filename]

        for column in columns:
            if column not in df.columns:
                add_check(
                    report, city, filename,
                    f"{column}_column_exists", 1,
                    "Required column missing"
                )
                continue

            values = df[column].astype("string").str.strip()
            blank_count = int((values.isna() | values.eq("")).sum())

            add_check(
                report, city, filename,
                f"{column}_blank_values", blank_count
            )

            # Only primary IDs must be unique.
            primary_ids = {
                "routes.csv": "route_id",
                "trips.csv": "trip_id",
                "stops.csv": "stop_id",
            }

            if primary_ids.get(filename) == column:
                nonblank = values[values.notna() & values.ne("")]
                duplicate_count = int(nonblank.duplicated().sum())

                add_check(
                    report, city, filename,
                    f"{column}_duplicate_values", duplicate_count
                )

    # Validate stop coordinates.
    if "stops.csv" in data:
        stops = data["stops.csv"]

        for column, low, high in [
            ("stop_lat", -90, 90),
            ("stop_lon", -180, 180),
        ]:
            if column not in stops.columns:
                add_check(
                    report, city, "stops.csv",
                    f"{column}_column_exists", 1,
                    "Coordinate column missing"
                )
                continue

            values = pd.to_numeric(stops[column], errors="coerce")
            present = stops[column].astype(str).str.strip().ne("")
            invalid = present & (
                values.isna() | ~values.between(low, high)
            )

            add_check(
                report, city, "stops.csv",
                f"{column}_invalid_values", int(invalid.sum())
            )

    # Validate time format (HH:MM:SS; hours may exceed 23 in GTFS).
    if "stop_times.csv" in data:
        stop_times = data["stop_times.csv"]

        for column in ["arrival_time", "departure_time"]:
            if column not in stop_times.columns:
                continue

            values = stop_times[column].astype(str).str.strip()
            present = values.ne("")

            pattern = values.str.fullmatch(
                r"\d{1,3}:[0-5]\d:[0-5]\d"
            )
            invalid = present & ~pattern

            add_check(
                report, city, "stop_times.csv",
                f"{column}_invalid_format", int(invalid.sum())
            )

        if "stop_sequence" in stop_times.columns:
            seq = pd.to_numeric(
                stop_times["stop_sequence"], errors="coerce"
            )
            present = stop_times["stop_sequence"].astype(str).str.strip().ne("")
            invalid = present & (
                seq.isna() | (seq < 0) | (seq % 1 != 0)
            )

            add_check(
                report, city, "stop_times.csv",
                "stop_sequence_invalid_values", int(invalid.sum())
            )

    # Check GTFS relationships.
    relationships = [
        ("trips.csv", "route_id", "routes.csv", "route_id"),
        ("stop_times.csv", "trip_id", "trips.csv", "trip_id"),
        ("stop_times.csv", "stop_id", "stops.csv", "stop_id"),
    ]

    for child_file, child_col, parent_file, parent_col in relationships:
        if child_file not in data or parent_file not in data:
            continue

        child = data[child_file]
        parent = data[parent_file]

        if child_col not in child.columns or parent_col not in parent.columns:
            add_check(
                report, city, child_file,
                f"{child_col}_relationship", 1,
                f"Missing column in {child_file} or {parent_file}"
            )
            continue

        child_values = child[child_col].astype(str).str.strip()
        parent_values = set(
            parent[parent_col].astype(str).str.strip()
        )
        parent_values.discard("")

        present = child_values.ne("")
        unmatched = present & ~child_values.isin(parent_values)

        add_check(
            report, city, child_file,
            f"{child_col}_unmatched_values",
            int(unmatched.sum()),
            f"Expected matching IDs in {parent_file}.{parent_col}"
        )


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = []

    for city in CITIES:
        validate_city(city, report)

    report_df = pd.DataFrame(report)
    output_file = REPORT_DIR / "final_validation_report.csv"
    report_df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print(report_df.to_string(index=False))
    print(f"\nReport saved to: {output_file}")


if __name__ == "__main__":
    main()
