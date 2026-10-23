
from pathlib import Path
import pandas as pd

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

results = []

def valid_gtfs_time(value):
    if pd.isna(value):
        return False

    parts = str(value).strip().split(":")

    if len(parts) != 3:
        return False

    try:
        hours, minutes, seconds = map(int, parts)
    except ValueError:
        return False

    return hours >= 0 and 0 <= minutes <= 59 and 0 <= seconds <= 59

for city in cities:
    path = PROCESSED_DIR / city / "stop_times.csv"

    if not path.exists():
        print(f"{city}: stop_times.csv not found")
        continue

    df = pd.read_csv(path, low_memory=False)

    row = {
        "city": city,
        "total_rows": len(df)
    }

    for column in ["arrival_time", "departure_time"]:
        if column not in df.columns:
            row[f"{column}_missing"] = "COLUMN NOT FOUND"
            row[f"{column}_invalid"] = "COLUMN NOT FOUND"
            continue

        values = df[column]
        row[f"{column}_missing"] = int(values.isna().sum())
        row[f"{column}_invalid"] = int(
            (~values.map(valid_gtfs_time) & values.notna()).sum()
        )

    results.append(row)

result_df = pd.DataFrame(results)
output_path = REPORT_DIR / "time_quality_report.csv"
result_df.to_csv(output_path, index=False)

print(result_df.to_csv(index=False))
print(f"Report saved to: {output_path}")
