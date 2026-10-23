
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = (
    BASE_DIR / "data" / "processed" / "chennai" / "stop_times.csv"
)
OUTPUT_DIR = BASE_DIR / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def to_seconds(value):
    if pd.isna(value):
        return None

    try:
        h, m, s = map(int, str(value).strip().split(":"))
        if h < 0 or not 0 <= m <= 59 or not 0 <= s <= 59:
            return None
        return h * 3600 + m * 60 + s
    except (ValueError, TypeError):
        return None


df = pd.read_csv(INPUT_PATH, low_memory=False)

df["arrival_seconds"] = df["arrival_time"].map(to_seconds)
df["departure_seconds"] = df["departure_time"].map(to_seconds)
df["stop_sequence_numeric"] = pd.to_numeric(
    df["stop_sequence"], errors="coerce"
)

# Issue 1: departure earlier than arrival at the same stop
same_stop_issue = (
    df["arrival_seconds"].notna()
    & df["departure_seconds"].notna()
    & (df["departure_seconds"] < df["arrival_seconds"])
)

# Sort by trip and stop sequence for Issue 2
ordered = df.dropna(
    subset=[
        "trip_id", "stop_sequence_numeric",
        "arrival_seconds", "departure_seconds"
    ]
).sort_values(["trip_id", "stop_sequence_numeric"]).copy()

ordered["previous_trip_id"] = ordered["trip_id"].shift(1)
ordered["previous_stop_sequence"] = (
    ordered["stop_sequence_numeric"].shift(1)
)
ordered["previous_stop_id"] = ordered["stop_id"].shift(1)
ordered["previous_departure_seconds"] = (
    ordered["departure_seconds"].shift(1)
)

same_trip = ordered["trip_id"].eq(ordered["previous_trip_id"])

between_stop_issue = (
    same_trip
    & (ordered["arrival_seconds"] < ordered["previous_departure_seconds"])
)

columns = [
    "trip_id", "stop_id", "stop_sequence",
    "arrival_time", "departure_time"
]

same_stop_report = df.loc[same_stop_issue, columns].copy()
same_stop_report.insert(0, "issue", "departure_before_arrival")

between_report = ordered.loc[
    between_stop_issue,
    columns + [
        "previous_stop_id",
        "previous_stop_sequence",
        "previous_departure_seconds"
    ]
].copy()
between_report.insert(0, "issue", "arrival_before_previous_departure")

report = pd.concat(
    [same_stop_report, between_report],
    ignore_index=True,
    sort=False
)

output_path = OUTPUT_DIR / "chennai_time_issues_details.csv"
report.to_csv(output_path, index=False)

print("Same-stop timing issues:", int(same_stop_issue.sum()))
print("Between-stop timing issues:", int(between_stop_issue.sum()))
print("\nFirst 20 issue records:")
print(report.head(20).to_string(index=False))
print(f"\nDetailed report saved to: {output_path}")
