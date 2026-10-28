
from pathlib import Path
import pandas as pd

# Project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "consolidated_data_quality_report.csv"

if not PROCESSED_DIR.exists():
    raise FileNotFoundError(
        f"Processed data folder not found: {PROCESSED_DIR}"
    )

report_rows = []

# Review existing processed CSV files.
# Exclude the report currently being generated.
csv_files = sorted(
    file for file in PROCESSED_DIR.rglob("*.csv")
    if file.resolve() != OUTPUT_FILE.resolve()
)

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in {PROCESSED_DIR}"
    )

for file_path in csv_files:
    print(f"Checking: {file_path.name}")

    try:
        df = pd.read_csv(file_path, low_memory=False)

        missing_cells = int(df.isna().sum().sum())
        duplicate_rows = int(df.duplicated().sum())

        # Summarize findings without automatically changing data.
        if missing_cells == 0 and duplicate_rows == 0:
            observation = (
                "No missing cells or exact duplicate rows detected "
                "in this file."
            )
        else:
            findings = []

            if missing_cells > 0:
                findings.append(
                    f"{missing_cells} missing cells"
                )

            if duplicate_rows > 0:
                findings.append(
                    f"{duplicate_rows} exact duplicate rows"
                )

            observation = "; ".join(findings) + (
                ". Review before deciding whether any action is needed."
            )

        report_rows.append({
            "category": "Processed CSV inspection",
            "city": "Multiple or not identified",
            "file_name": str(file_path.relative_to(PROCESSED_DIR)),
            "record_count": len(df),
            "column_count": len(df.columns),
            "missing_cell_count": missing_cells,
            "duplicate_row_count": duplicate_rows,
            "observation": observation,
        })

    except Exception as error:
        report_rows.append({
            "category": "File inspection error",
            "city": "Not identified",
            "file_name": str(file_path.relative_to(PROCESSED_DIR)),
            "record_count": None,
            "column_count": None,
            "missing_cell_count": None,
            "duplicate_row_count": None,
            "observation": f"Could not inspect file: {error}",
        })

# Add documented project-level limitations.
limitations = [
    (
        "Passenger data",
        "All cities",
        "Passenger counts and occupancy are unavailable. "
        "Scheduled trip counts must not be treated as passenger demand."
    ),
    (
        "Geographic route distance",
        "All cities",
        "shapes.txt is unavailable. Actual shape-based route distance "
        "cannot be calculated from the current datasets."
    ),
    (
        "Service exceptions",
        "All cities",
        "calendar_dates.txt is unavailable. Date-specific service "
        "additions and removals are not included in calendar summaries."
    ),
    (
        "Timing anomalies",
        "Chennai",
        "Previously identified timing anomalies require source "
        "verification. Do not automatically correct scheduled times."
    ),
    (
        "Headway interpretation",
        "All cities",
        "Missing headways can occur for first departures. Zero headways "
        "can indicate simultaneous scheduled departures; investigate "
        "context before classifying them as errors."
    ),
]

for topic, city, explanation in limitations:
    report_rows.append({
        "category": "Documented limitation or review note",
        "city": city,
        "file_name": "Project documentation",
        "record_count": None,
        "column_count": None,
        "missing_cell_count": None,
        "duplicate_row_count": None,
        "observation": f"{topic}: {explanation}",
    })

report = pd.DataFrame(report_rows)

report.to_csv(OUTPUT_FILE, index=False)

print("\nConsolidated data-quality report created!")
print(f"CSV files inspected: {len(csv_files)}")
print(f"Total report entries: {len(report)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nProcessed CSV inspection summary:")
inspection = report[
    report["category"] == "Processed CSV inspection"
]

print(
    inspection[
        [
            "file_name",
            "record_count",
            "missing_cell_count",
            "duplicate_row_count",
        ]
    ].to_string(index=False)
)

print(
    "\nNote: Missing cells and duplicate rows are indicators "
    "for review, not automatic proof of incorrect data."
)
