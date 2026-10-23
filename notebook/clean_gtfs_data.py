
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

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned"

# Columns that should contain numeric values.
NUMERIC_COLUMNS = {
    "stops.csv": ["stop_lat", "stop_lon"],
    "stop_times.csv": ["stop_sequence", "shape_dist_traveled"],
    "routes.csv": ["route_type"],
    "trips.csv": ["direction_id", "block_id"],
}


def clean_city(city):
    source_dir = PROCESSED_DIR / city
    output_dir = CLEANED_DIR / city

    if not source_dir.exists():
        print(f"[SKIP] {city}: processed folder not found.")
        return

    csv_files = list(source_dir.glob("*.csv"))

    if not csv_files:
        print(f"[WARNING] {city}: no CSV files found.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for csv_file in csv_files:
        try:
            df = pd.read_csv(
                csv_file,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
                low_memory=False,
            )

            # Standardize column names and remove surrounding whitespace.
            df.columns = [column.strip().lower() for column in df.columns]

            for column in df.columns:
                if df[column].dtype == object:
                    df[column] = df[column].str.strip()
                    df[column] = df[column].replace("", pd.NA)

            # Convert selected fields to numeric.
            numeric_columns = NUMERIC_COLUMNS.get(csv_file.name.lower(), [])

            for column in numeric_columns:
                if column in df.columns:
                    df[column] = pd.to_numeric(
                        df[column], errors="coerce"
                    )

            # Invalid coordinates become missing, not fabricated.
            if csv_file.name.lower() == "stops.csv":
                if "stop_lat" in df.columns:
                    invalid_lat = ~df["stop_lat"].between(-90, 90)
                    df.loc[invalid_lat, "stop_lat"] = pd.NA

                if "stop_lon" in df.columns:
                    invalid_lon = ~df["stop_lon"].between(-180, 180)
                    df.loc[invalid_lon, "stop_lon"] = pd.NA

            # Remove exact duplicate rows only.
            before = len(df)
            df = df.drop_duplicates()
            removed = before - len(df)

            output_file = output_dir / csv_file.name
            df.to_csv(output_file, index=False, encoding="utf-8-sig")

            print(
                f"[OK] {city}/{csv_file.name}: "
                f"{len(df)} rows; exact duplicates removed: {removed}"
            )

        except Exception as error:
            print(f"[ERROR] {city}/{csv_file.name}: {error}")


def main():
    for city in CITIES:
        clean_city(city)

    print("\nGTFS cleaning finished.")


if __name__ == "__main__":
    main()
