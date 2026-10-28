
from pathlib import Path
import pandas as pd

processed_dir = Path("data/processed")

files = sorted(processed_dir.glob("*_trip_headway_features.csv"))

if not files:
    print("No headway files found.")
else:
    for file in files:
        df = pd.read_csv(file)

        headway = pd.to_numeric(
            df["headway_minutes"], errors="coerce"
        )

        print(f"\nCity file: {file.name}")
        print(f"Total rows: {len(df)}")
        print(f"Missing headways: {headway.isna().sum()}")
        print(f"Zero headways: {(headway == 0).sum()}")
        print(f"Negative headways: {(headway < 0).sum()}")
        print(f"Positive headways: {(headway > 0).sum()}")
        groups = df.groupby(
            ["route_id", "service_id"], dropna=False
        ).ngroups

        missing = headway.isna().sum()

        print(f"Route/service groups: {groups}")
        print(f"Missing values match group count: {groups == missing}")

print("\nHeadway validation finished.")
