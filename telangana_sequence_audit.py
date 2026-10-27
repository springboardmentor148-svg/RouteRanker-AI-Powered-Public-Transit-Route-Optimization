import pandas as pd
from pathlib import Path

source = Path("data/raw/TELANGANA/stop_times.txt")
output = Path("reports/TELANGANA_sequence_audit.csv")

df = pd.read_csv(
    source,
    dtype=str,
    usecols=[
        "trip_id",
        "stop_sequence",
        "arrival_time",
        "departure_time",
    ],
)

df["stop_sequence"] = pd.to_numeric(
    df["stop_sequence"], errors="coerce"
)


def gtfs_seconds(value):
    try:
        h, m, s = value.split(":")
        return int(h) * 3600 + int(m) * 60 + int(s)
    except (ValueError, AttributeError):
        return None


df["arrival"] = df["arrival_time"].map(gtfs_seconds)
df["departure"] = df["departure_time"].map(gtfs_seconds)

df = df.sort_values(["trip_id", "stop_sequence"])

# Use the later of arrival/departure at each stop.
df["event"] = df[["arrival", "departure"]].max(axis=1)

# Compare consecutive events within each trip.
df["previous_event"] = df.groupby("trip_id")["event"].shift(1)
df["backwards_step"] = (
    (df["event"] < df["previous_event"])
    & df["event"].notna()
    & df["previous_event"].notna()
)

summary = df.groupby("trip_id").agg(
    stop_count=("stop_sequence", "size"),
    first_time=("event", "first"),
    last_time=("event", "last"),
    backwards_time_steps=("backwards_step", "sum"),
)

summary["duration_hours"] = (
    summary["last_time"] - summary["first_time"]
) / 3600

summary = summary.reset_index()
summary["duration_hours"] = summary["duration_hours"].round(2)

summary.to_csv(output, index=False)

print("Sequence audit complete.")
print("Trips audited:", len(summary))
print(
    "Trips with decreasing timestamps:",
    int((summary["backwards_time_steps"] > 0).sum()),
)
print(
    "Trips over 24 hours:",
    int((summary["duration_hours"] > 24).sum()),
)
print(
    "Trips over 48 hours:",
    int((summary["duration_hours"] > 48).sum()),
)
print("\nLongest trips:")
print(
    summary.nlargest(10, "duration_hours")[
        ["trip_id", "stop_count", "duration_hours",
         "backwards_time_steps"]
    ].to_string(index=False)
)
print("\nSaved:", output)