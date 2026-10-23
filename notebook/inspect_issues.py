
from pathlib import Path
import pandas as pd

project = Path(__file__).resolve().parent.parent
data = project / "data" / "processed"

checks = [
    ("ahmedabad", "trips.csv", ["trip_id"]),
    ("bengaluru", "routes.csv", ["route_id"]),
    ("bengaluru", "stop_times.csv", ["trip_id", "stop_sequence"]),
    ("bengaluru", "trips.csv", ["trip_id"]),
    ("bengaluru", "stops.csv", ["stop_id"]),
]

for city, filename, keys in checks:
    path = data / city / filename

    print("\n" + "=" * 60)
    print(f"{city.upper()} - {filename}")
    print("=" * 60)

    if not path.exists():
        print("File not found:", path)
        continue

    df = pd.read_csv(path, dtype=str)
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    print("\nMissing values by column:")
    print(df.isna().sum().to_string())

    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    if all(key in df.columns for key in keys):
        repeated = df[df.duplicated(subset=keys, keep=False)]

        print(f"\nRepeated key groups: {len(repeated)} affected rows")
        if not repeated.empty:
            print(repeated[keys].head(10).to_string(index=False))

print("\nInspection completed.")
