
import pandas as pd
from pathlib import Path

source = Path("data/raw/TELANGANA/stop_times.txt")
output = Path("reports/TELANGANA_schedule_audit.csv")

df = pd.read_csv(source, dtype=str)

def gtfs_seconds(value):
    try:
        hours, minutes, seconds = value.split(":")
        return (
            int(hours) * 3600
            + int(minutes) * 60
            + int(seconds)
        )
    except (ValueError, AttributeError):
        return None

df["arrival_seconds"] = df["arrival_time"].map(gtfs_seconds)
df["departure_seconds"] = df["departure_time"].map(gtfs_seconds)

df["event_seconds"] = df[
    ["arrival_seconds", "departure_seconds"]
].max(axis=1)

# Preserve source row order while auditing each trip.
df["source_order"] = range(len(df))

records = []

for trip_id, group in df.groupby("trip_id", sort=False):
    group = group.sort_values("source_order")
    times = group["event_seconds"].dropna()

    if times.empty:
        duration_hours = None
        first_time = None
        last_time = None
        backwards_steps = 0
    else:
        first_time = times.iloc[0]
        last_time = times.iloc[-1]
        duration_hours = (last_time - first_time) / 3600
        backwards_steps = int((times.diff().dropna() < 0).sum())

    if duration_hours is None:
        status = "Invalid or missing time"
    elif backwards_steps > 0:
        status = "Review: time decreases"
    elif duration_hours > 24:
        status = "Review: over 24 hours"
    elif duration_hours > 4:
        status = "Review: over 4 hours"
    else:
        status = "Within 4-hour screening threshold"

    records.append({
        "trip_id": trip_id,
        "stop_count": len(group),
        "first_time_seconds": first_time,
        "last_time_seconds": last_time,
        "duration_hours": (
            round(duration_hours, 2)
            if duration_hours is not None else None
        ),
        "backwards_time_steps": backwards_steps,
        "audit_status": status,
    })

audit = pd.DataFrame(records)
audit.to_csv(output, index=False)

print("Telangana schedule audit created.")
print("Trips audited:", len(audit))
print("\nAudit categories:")
print(audit["audit_status"].value_counts().to_string())
print("\nLongest trips:")
print(
    audit.nlargest(10, "duration_hours")[
        ["trip_id", "stop_count", "duration_hours",
         "backwards_time_steps", "audit_status"]
    ].to_string(index=False)
)
print("\nSaved:", output)
