
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/raw")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

issues = []


def add_issue(city, file_name, test, count, severity, details=""):
    issues.append({
        "city": city,
        "file": file_name,
        "test": test,
        "issue_count": int(count),
        "severity": severity,
        "details": details
    })


def load_table(folder, filename, city):
    path = folder / filename

    if not path.exists():
        add_issue(
            city, filename, "File exists", 1,
            "ERROR", "Required file is missing"
        )
        return None

    try:
        return pd.read_csv(
            path, dtype=str, low_memory=False
        ).fillna("")
    except Exception as exc:
        add_issue(
            city, filename, "File readable", 1,
            "ERROR", str(exc)
        )
        return None


def check_required_columns(df, city, filename, columns):
    if df is None:
        return False

    missing = [c for c in columns if c not in df.columns]

    if missing:
        add_issue(
            city, filename, "Required columns", len(missing),
            "ERROR", ", ".join(missing)
        )
        return False

    return True


def check_table(
    df, city, filename, id_column=None, required_columns=None
):
    if df is None:
        return

    if df.empty:
        add_issue(
            city, filename, "Non-empty table", 1,
            "ERROR", "File has no data rows"
        )
        return

    if required_columns:
        for col in required_columns:
            if col in df.columns:
                missing = (
                    df[col].astype(str).str.strip().eq("").sum()
                )
                if missing:
                    add_issue(
                        city, filename, f"Missing {col}",
                        missing, "WARNING",
                        "Rows with blank required values"
                    )

    if id_column and id_column in df.columns:
        blank = df[id_column].astype(str).str.strip().eq("").sum()
        duplicates = df[id_column].duplicated().sum()

        if blank:
            add_issue(
                city, filename, f"Blank {id_column}",
                blank, "ERROR", "Blank identifiers"
            )

        if duplicates:
            add_issue(
                city, filename, f"Duplicate {id_column}",
                duplicates, "ERROR", "Repeated identifiers"
            )


def run_city(city_folder):
    city = city_folder.name
    print(f"\nTesting: {city}")

    routes = load_table(city_folder, "routes.txt", city)

    # Use the cleaned Delhi trips file if available.
    cleaned_trips_path = REPORT_DIR / f"{city}_trips_cleaned.txt"

    if city == "DEHLI" and cleaned_trips_path.exists():
        trips = pd.read_csv(
            cleaned_trips_path, dtype=str, low_memory=False
        ).fillna("")
        print("Using cleaned Delhi trips file for testing.")
    else:
        trips = load_table(city_folder, "trips.txt", city)

    stops = load_table(city_folder, "stops.txt", city)
    times = load_table(city_folder, "stop_times.txt", city)

    check_table(
        routes, city, "routes.txt", "route_id",
        ["route_id"]
    )
    check_table(
        trips, city, "trips.txt", "trip_id",
        ["route_id", "service_id", "trip_id"]
    )
    check_table(
        stops, city, "stops.txt", "stop_id",
        ["stop_id", "stop_name"]
    )
    check_table(
        times, city, "stop_times.txt", None,
        [
            "trip_id", "arrival_time", "departure_time",
            "stop_id", "stop_sequence"
        ]
    )

    # Check stop coordinates.
    if stops is not None and check_required_columns(
        stops, city, "stops.txt", ["stop_lat", "stop_lon"]
    ):
        lat = pd.to_numeric(stops["stop_lat"], errors="coerce")
        lon = pd.to_numeric(stops["stop_lon"], errors="coerce")

        invalid = (
            lat.isna() | lon.isna()
            | ~lat.between(-90, 90)
            | ~lon.between(-180, 180)
        )

        if invalid.sum():
            add_issue(
                city, "stops.txt", "Invalid coordinates",
                invalid.sum(), "WARNING",
                "Missing, non-numeric or out-of-range coordinates"
            )

    # Check stop sequence values.
    if times is not None and "stop_sequence" in times.columns:
        seq = pd.to_numeric(times["stop_sequence"], errors="coerce")
        invalid = seq.isna() | (seq < 0)

        if invalid.sum():
            add_issue(
                city, "stop_times.txt", "Invalid stop_sequence",
                invalid.sum(), "WARNING",
                "Non-numeric or negative sequence values"
            )

        if "trip_id" in times.columns:
            valid = times.assign(_seq=seq).dropna(subset=["_seq"])
            duplicate_sequences = valid.duplicated(
                ["trip_id", "_seq"]
            ).sum()

            if duplicate_sequences:
                add_issue(
                    city, "stop_times.txt",
                    "Duplicate trip stop sequence",
                    duplicate_sequences, "WARNING",
                    "Repeated trip_id and stop_sequence pairs"
                )

    # Check time format, allowing GTFS times beyond 24:00.
    if times is not None:
        for col in ["arrival_time", "departure_time"]:
            if col in times.columns:
                values = times[col].astype(str).str.strip()
                pattern = values.str.extract(
                    r"^(\d{1,3}):([0-5]\d):([0-5]\d)$"
                )
                valid = pattern.notna().all(axis=1)
                blank = values.eq("")
                invalid = ~(valid | blank)

                if invalid.sum():
                    add_issue(
                        city, "stop_times.txt",
                        f"Invalid {col} format",
                        invalid.sum(), "WARNING",
                        "Expected H:MM:SS or HH:MM:SS; "
                        "hours may exceed 23"
                    )

    # Check service calendar availability.
    if not (
        (city_folder / "calendar.txt").exists()
        or (city_folder / "calendar_dates.txt").exists()
    ):
        add_issue(
            city, "calendar.txt/calendar_dates.txt",
            "Service calendar exists", 1, "WARNING",
            "Neither calendar file was found"
        )


if not DATA_DIR.exists():
    print(f"Data folder not found: {DATA_DIR.resolve()}")
else:
    city_folders = sorted(
        p for p in DATA_DIR.iterdir() if p.is_dir()
    )

    if not city_folders:
        print("No city folders found inside data/raw/")
    else:
        for folder in city_folders:
            run_city(folder)

        # Always include column headers, even if no issues are found.
        columns = [
            "city", "file", "test",
            "issue_count", "severity", "details"
        ]
        report = pd.DataFrame(issues, columns=columns)

        output = REPORT_DIR / "data_quality_report.csv"
        report.to_csv(output, index=False)

        print("\n" + "=" * 55)
        print("DATA QUALITY TESTING COMPLETE")
        print(f"Cities tested: {len(city_folders)}")
        print(f"Issues found: {len(issues)}")
        print(f"Report saved to: {output}")

        if not report.empty:
            print("\nIssues by severity:")
            print(report.groupby("severity")["issue_count"].sum())
        else:
            print("No issues were flagged by these checks.")
