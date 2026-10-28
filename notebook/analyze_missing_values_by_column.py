
from pathlib import Path
import pandas as pd

# RouteRanker project folders
PROJECT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

OUTPUT_FILE = PROCESSED_DIR / "missing_values_by_column_report.csv"

# Exclude reports and dictionaries to avoid analyzing reports about reports
EXCLUDED_FILES = {
    "consolidated_data_quality_report.csv",
    "feature_dictionary.csv",
    "missing_values_by_column_report.csv",
}

results = []

for csv_file in PROCESSED_DIR.rglob("*.csv"):
    if csv_file.name in EXCLUDED_FILES:
        continue

    try:
        df = pd.read_csv(csv_file, low_memory=False)

        total_rows = len(df)

        for column in df.columns:
            missing_count = int(df[column].isna().sum())

            if missing_count > 0:
                missing_percentage = (
                    missing_count / total_rows * 100
                    if total_rows > 0
                    else 0
                )

                results.append({
                    "file": str(csv_file.relative_to(PROCESSED_DIR)),
                    "column": column,
                    "total_rows": total_rows,
                    "missing_count": missing_count,
                    "missing_percentage": round(missing_percentage, 2),
                })

    except Exception as error:
        print(f"Could not analyze {csv_file.name}: {error}")

report_columns = [
    "file",
    "column",
    "total_rows",
    "missing_count",
    "missing_percentage",
]

report = pd.DataFrame(results, columns=report_columns)

if not report.empty:
    report = report.sort_values(
        by=["missing_count", "file"],
        ascending=[False, True],
    )

report.to_csv(OUTPUT_FILE, index=False)

print("Missing-value analysis completed!")
print(f"Report saved to: {OUTPUT_FILE}")
print(f"Columns with missing values: {len(report)}")

if not report.empty:
    print("\nTop 15 missing-value results:")
    print(report.head(15).to_string(index=False))
else:
    print("No missing values were found in the analyzed CSV files.")
