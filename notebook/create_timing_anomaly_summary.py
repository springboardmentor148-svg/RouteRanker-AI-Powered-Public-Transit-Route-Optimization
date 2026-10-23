
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_PATH = BASE_DIR / "reports" / "chennai_time_issues_details.csv"
OUTPUT_PATH = BASE_DIR / "reports" / "timing_anomaly_summary.csv"

if not INPUT_PATH.exists():
    raise FileNotFoundError(
        f"Input report not found: {INPUT_PATH}"
    )

df = pd.read_csv(INPUT_PATH, low_memory=False)

summary = (
    df.groupby("issue", dropna=False)
    .agg(
        affected_records=("trip_id", "size"),
        affected_trips=("trip_id", "nunique")
    )
    .reset_index()
)

summary["city"] = "chennai"
summary["status"] = "Needs source verification"
summary["action"] = "Retain original times; do not auto-correct"

summary = summary[
    [
        "city",
        "issue",
        "affected_records",
        "affected_trips",
        "status",
        "action",
    ]
]

summary.to_csv(OUTPUT_PATH, index=False)

print(summary.to_string(index=False))
print(f"\nReport saved to: {OUTPUT_PATH}")
