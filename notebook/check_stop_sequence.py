
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

for city in cities:
    path = PROCESSED_DIR / city / "stop_times.csv"

    if not path.exists():
        print(f"{city}: stop_times.csv not found")
        continue

    df = pd.read_csv(path, low_memory=False)

    required = ["trip_id", "stop_sequence"]

    if not all(col in df.columns for col in required):
        print(f"{city}: required columns are missing")
        print("Available columns:", df.columns.tolist())
        continue

    df["stop_sequence_numeric"] = pd.to_numeric(
        df["stop_sequence"], errors="coerce"
    )

    missing_trip = df["trip_id"].isna().sum()
    missing_sequence = df["stop_sequence_numeric"].isna().sum()

    ordered = df.dropna(
        subset=["trip_id", "stop_sequence_numeric"]
    ).sort_values(["trip_id", "stop_sequence_numeric"])

    duplicate_sequence_rows = ordered.duplicated(
        subset=["trip_id", "stop_sequence_numeric"],
        keep=False
    ).sum()

    sequence_diff = ordered.groupby("trip_id")[
        "stop_sequence_numeric"
    ].diff()

    non_increasing_steps = (sequence_diff <= 0).sum()

    results.append({
        "city": city,
        "total_rows": len(df),
        "missing_trip_id": int(missing_trip),
        "missing_or_non_numeric_sequence": int(missing_sequence),
        "duplicate_sequence_rows": int(duplicate_sequence_rows),
        "non_increasing_sequence_steps": int(non_increasing_steps)
    })

result = pd.DataFrame(results)
output_path = REPORT_DIR / "stop_sequence_quality_report.csv"
result.to_csv(output_path, index=False)

print(result.to_csv(index=False))
print(f"Report saved to: {output_path}")
