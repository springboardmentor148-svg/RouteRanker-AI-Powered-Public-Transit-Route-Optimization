
from pathlib import Path
import pandas as pd

ROOT = Path("data/raw")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

days = [
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
]

results = []

for city in sorted(p for p in ROOT.iterdir() if p.is_dir()):
    calendar_file = city / "calendar.txt"
    trips_file = city / "trips.txt"

    if not calendar_file.exists() or not trips_file.exists():
        continue

    calendar = pd.read_csv(calendar_file, dtype=str)
    trips = pd.read_csv(
        trips_file, usecols=["service_id"], dtype=str
    )

    exception_file = city / "calendar_dates.txt"
    exceptions = (
        pd.read_csv(exception_file, dtype=str)
        if exception_file.exists()
        else pd.DataFrame(columns=[
            "date", "service_id", "exception_type"
        ])
    )

    trip_service_ids = set(trips["service_id"].dropna())

    for _, row in calendar.iterrows():
        service_id = row["service_id"]

        if service_id not in trip_service_ids:
            continue

        active_days = [
            day for day in days
            if str(row[day]).strip() == "1"
        ]

        start = pd.to_datetime(
            str(row["start_date"]), format="%Y%m%d",
            errors="coerce"
        )
        end = pd.to_datetime(
            str(row["end_date"]), format="%Y%m%d",
            errors="coerce"
        )

        issues = []

        if pd.isna(start) or pd.isna(end):
            issues.append("Invalid calendar date")
        elif start > end:
            issues.append("Start date after end date")

        if not active_days:
            issues.append("No regular operating weekdays")

        if not pd.isna(end) and end.year > 2050:
            issues.append("Unusually distant end date")

        if not pd.isna(end) and end < pd.Timestamp.today().normalize():
            issues.append("Historical calendar end date")

        service_exceptions = exceptions[
            exceptions["service_id"] == service_id
        ]

        results.append({
            "city": city.name,
            "service_id": service_id,
            "active_weekdays": ", ".join(active_days),
            "start_date": start.date() if not pd.isna(start) else None,
            "end_date": end.date() if not pd.isna(end) else None,
            "exception_records": len(service_exceptions),
            "quality_status": "; ".join(issues) if issues else "Review passed"
        })

report = pd.DataFrame(results)
output = REPORTS / "calendar_quality_report.csv"
report.to_csv(output, index=False)

print("Calendar quality report created:", output)
print("Service records checked:", len(report))
print("\nQuality status counts:")
print(report["quality_status"].value_counts().to_string())
print("\nReport preview:")
print(report.to_string(index=False))
