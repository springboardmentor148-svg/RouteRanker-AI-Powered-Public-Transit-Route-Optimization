
from pathlib import Path
import pandas as pd

# Folder containing your eight city folders
DATA_DIR = Path("data/raw")

required_files = [
    "routes.txt",
    "trips.txt",
    "stops.txt",
    "stop_times.txt",
]

calendar_files = [
    "calendar.txt",
    "calendar_dates.txt",
]

print("ROUTERANKER - GTFS DATA VALIDATION")
print("=" * 45)

if not DATA_DIR.exists():
    print(f"ERROR: Folder not found: {DATA_DIR.resolve()}")
    print("Check your project folder structure.")
else:
    city_folders = sorted(
        folder for folder in DATA_DIR.iterdir()
        if folder.is_dir()
    )

    print(f"City folders found: {len(city_folders)}")

    if not city_folders:
        print("No city folders found. Check data/raw/.")

    for city in city_folders:
        print(f"\nCITY: {city.name}")
        print("-" * 35)

        for filename in required_files:
            file_path = city / filename

            if not file_path.exists():
                print(f"MISSING: {filename}")
                continue

            try:
                df = pd.read_csv(file_path, low_memory=False)
                print(
                    f"OK: {filename} | "
                    f"{len(df):,} rows | "
                    f"{len(df.columns)} columns"
                )

            except Exception as error:
                print(f"ERROR: {filename} | {error}")

        has_calendar = any(
            (city / filename).exists()
            for filename in calendar_files
        )

        if has_calendar:
            print("Service calendar file: FOUND")
        else:
            print("CHECK: No service calendar file found")

print("\nValidation check complete.")
