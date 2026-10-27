
import pandas as pd
from pathlib import Path

source = Path("data/raw/TELANGANA/stop_times.txt")
output = Path("reports/TELANGANA_schedule_audit.csv")

df = pd.read_csv(source, dtype=str)


def gtfs_seconds(value):
    """Convert a GTFS HH:MM:SS time to seconds."""
    try:
        hours, minutes, seconds = value.split(":")
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)

        if hours < 0 or not (0 <= minutes < 60):
            return None

        if not (0 <= seconds < 60):
            return None

        return hours * 3600 + minutes * 60 + seconds

    except (ValueError, AttributeError):
        return None


df["arrival_seconds"] = df["arrival_time"].map(gtfs_seconds)
df["departure_seconds"] = df["departure_time"].map(gtfs_seconds)

# Use the later of arrival and departure as the event time.
df["event_seconds"] = df[
    ["arrival_seconds", "departure_seconds"]
].max(axis=1)

# Sort stops numerically by their sequence.
df["sequence_number"] = pd.to_numeric(
    df["stop_sequence"], errors="coerce"
)

records = []

for trip_id, group in df.groupby("trip_id", sort=False):
    group = group.sort_values("sequence_number")
    times = group["event_seconds"]
    valid_times = times.dropna()

    if valid_times.empty:
        first_time = None
        last_time = None
        duration_hours = None
        backwards_steps = 0
        max_gap_hours = None

    else:
        first_time = valid_times.iloc[0]
        last_time = valid_times.iloc[-1]

        duration_hours = (last_time - first_time) / 3600

        # Check consecutive valid event times.
        gaps = valid_times.diff().dropna()
        backwards_steps = int((gaps < 0).sum())

        nonnegative_gaps = gaps[gaps >= 0]

        if nonnegative_gaps.empty:
            max_gap_hours = 0
        else:
            max_gap_hours = nonnegative_gaps.max() / 3600

    # Basic time-sequence status.
    if duration_hours is None:
        audit_status = "Invalid or missing time"
    elif backwards_steps > 0:
        audit_status = "Review: time decreases"
    else:
        audit_status = "Time sequence passes basic checks"

    # Duration screening flag.
    if duration_hours is None:
        duration_flag = "Missing duration"
    elif duration_hours > 24:
        duration_flag = "Over 24 hours"
    elif duration_hours > 4:
        duration_flag = "Over 4 hours"
    else:
        duration_flag = "Within duration thresholds"

    # General gap screening flag.
    if max_gap_hours is None:
        gap_flag = "Missing gap data"
    elif max_gap_hours > 2:
        gap_flag = "Gap over 2 hours"
    else:
        gap_flag = "Within gap threshold"

    # Additional extreme-gap screening flag.
    if max_gap_hours is None:
        extreme_gap_flag = "Missing gap data"
    elif max_gap_hours > 4:
        extreme_gap_flag = "Extreme gap over 4 hours"
    else:
        extreme_gap_flag = "No extreme gap"

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
        "max_gap_hours": (
            round(max_gap_hours, 2)
            if max_gap_hours is not None else None
        ),
        "audit_status": audit_status,
        "duration_flag": duration_flag,
        "gap_flag": gap_flag,
        "extreme_gap_flag": extreme_gap_flag,
    })


audit = pd.DataFrame(records)

# Ensure the report directory exists.
output.parent.mkdir(parents=True, exist_ok=True)

audit.to_csv(output, index=False)

print("Telangana schedule audit created.")
print("Trips audited:", len(audit))

print("\nAudit status:")
print(audit["audit_status"].value_counts().to_string())

print("\nDuration flags:")
print(audit["duration_flag"].value_counts().to_string())

print("\nGap flags:")
print(audit["gap_flag"].value_counts().to_string())

print("\nExtreme-gap flags:")
print(audit["extreme_gap_flag"].value_counts().to_string())

print("\nLongest trips:")
print(
    audit.nlargest(10, "duration_hours")[
        [
            "trip_id",
            "stop_count",
            "duration_hours",
            "max_gap_hours",
            "backwards_time_steps",
            "audit_status",
            "duration_flag",
            "gap_flag",
            "extreme_gap_flag",
        ]
    ].to_string(index=False)
)

print(
    "\nTrips with gaps over 2 hours:",
    int((audit["max_gap_hours"] > 2).sum())
)

print(
    "Trips with extreme gaps over 4 hours:",
    int((audit["max_gap_hours"] > 4).sum())
)

print("\nSaved:", output)
