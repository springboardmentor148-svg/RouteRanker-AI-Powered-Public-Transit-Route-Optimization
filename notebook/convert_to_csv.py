
from pathlib import Path
import pandas as pd

# RouteRanker project folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CITIES = [
    "ahmedabad",
    "chennai",
    "mumbai",
    "pune",
    "hyderabad",
]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def convert_city(city):
    raw_city_dir = RAW_DIR / city
    output_city_dir = PROCESSED_DIR / city

    if not raw_city_dir.exists():
        print(f"[SKIP] {city}: raw folder not found.")
        return

    output_city_dir.mkdir(parents=True, exist_ok=True)
    txt_files = list(raw_city_dir.glob("*.txt"))

    if not txt_files:
        print(f"[WARNING] {city}: no .txt files found in {raw_city_dir}")
        return

    for txt_file in txt_files:
        try:
            # Read GTFS text files as strings to preserve IDs and leading zeros.
            df = pd.read_csv(
                txt_file,
                dtype=str,
                keep_default_na=False,
                encoding="utf-8-sig",
                low_memory=False,
            )

            output_file = output_city_dir / f"{txt_file.stem.lower()}.csv"
            df.to_csv(output_file, index=False, encoding="utf-8-sig")

            print(
                f"[OK] {city}/{txt_file.name}: "
                f"{len(df)} rows, {len(df.columns)} columns"
            )

        except Exception as error:
            print(f"[ERROR] Could not convert {txt_file}: {error}")


def main():
    for city in CITIES:
        convert_city(city)

    print("\nTXT-to-CSV conversion finished.")


if __name__ == "__main__":
    main()
