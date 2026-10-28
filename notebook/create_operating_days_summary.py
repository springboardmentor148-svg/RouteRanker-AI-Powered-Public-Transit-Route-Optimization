
from pathlib import Path
import pandas as pd

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

cities = ["ahmedabad", "chennai", "hyderabad", "mumbai", "pune"]

all_summaries = []

day_columns = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

for city in cities:
    print(f"Processing {city}...")

    calendar_file = RAW_DIR / city / "calendar.txt"

    if not calendar_file.exists():
        print(f"WARNING: calendar.txt not found for {city}; skipping.")
        continue

    calendar = pd.read_csv(calendar_file, dtype=str)

    required_columns = [
        "service_id",
        *day_columns,
        "start_date",
        "end_date",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in calendar.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{city}: calendar.txt is missing columns: {missing_columns}"
        )

    # Convert service-day flags into numeric values
    for day in day_columns:
        calendar[day] = pd.to_numeric(
            calendar[day], errors="coerce"
        ).fillna(0).astype(int)

    # Count scheduled operating days per service
    calendar["scheduled_operating_days_per_week"] = (
        calendar[day_columns].sum(axis=1)
    )

    # Create a readable list of scheduled operating days
    calendar["scheduled_operating_days"] = calendar.apply(
        lambda row: ", ".join(
            day.title()
            for day in day_columns
            if row[day] == 1
        ) or "No scheduled operating days",
        axis=1,
    )

    # Add city and keep the important fields
    calendar["city"] = city

    summary_columns = [
        "city",
        "service_id",
        *day_columns,
        "scheduled_operating_days",
        "scheduled_operating_days_per_week",
        "start_date",
        "end_date",
    ]

    summary = calendar[summary_columns].copy()
    all_summaries.append(summary)

if not all_summaries:
    raise RuntimeError("No operating-day summaries were generated.")

final_summary = pd.concat(all_summaries, ignore_index=True)

output_file = PROCESSED_DIR / "operating_days_summary.csv"
final_summary.to_csv(output_file, index=False)

print("\nOperating-days summary created successfully!")
print(f"Total service records: {len(final_summary)}")
print(f"Cities processed: {final_summary['city'].nunique()}")
print(f"Saved to: {output_file}")

print("\nFirst 10 records:")
print(final_summary.head(10).to_string(index=False))

print("\nScheduled operating days per city:")
print(
    final_summary.groupby("city")[
        "scheduled_operating_days_per_week"
    ].describe().round(2).to_string()
)
