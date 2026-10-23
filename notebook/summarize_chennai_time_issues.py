
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "reports" / "chennai_time_issues_details.csv"

df = pd.read_csv(INPUT_PATH, low_memory=False)

print("Issues grouped by type:")
print(df["issue"].value_counts().to_string())

print("\nAffected trips:")
print(df["trip_id"].dropna().unique())

print("\nIssue records:")
print(df.to_string(index=False))
