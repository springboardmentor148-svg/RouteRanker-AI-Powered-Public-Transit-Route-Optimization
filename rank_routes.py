
import pandas as pd
from pathlib import Path

input_path = Path("reports/combined_route_features.csv")
output_path = Path("reports/route_priority_ranking.csv")

df = pd.read_csv(
    input_path,
    dtype={"city": str, "route_id": str}
)

# Safely convert numeric columns.
numeric_columns = [
    "scheduled_trip_count",
    "trips_flagged_for_review",
    "extreme_schedule_trip_count",
    "shapes_with_large_gaps",
    "unflagged_trip_count",
]

for column in numeric_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

# Preserve missing values rather than treating them as confirmed zeros.
df["scheduled_trip_count"] = df["scheduled_trip_count"].fillna(0)
df["trips_flagged_for_review"] = df["trips_flagged_for_review"].fillna(0)
df["extreme_schedule_trip_count"] = df["extreme_schedule_trip_count"].fillna(0)
df["unflagged_trip_count"] = df["unflagged_trip_count"].fillna(0)

df["shapes_with_large_gaps"] = pd.to_numeric(
    df["shapes_with_large_gaps"], errors="coerce"
)

# Handle distance availability explicitly.
df["distance_available"] = (
    df["distance_available"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({"true": True, "false": False})
)

# Compare scheduled trip volume within each city.
df["trip_volume_percentile"] = (
    df.groupby("city")["scheduled_trip_count"]
    .rank(pct=True)
    .mul(100)
    .round(2)
)

# Data-quality status is separate from investigation priority.
def classify_data_quality(row):
    if row["unflagged_trip_count"] == 0:
        return "Review: no unflagged trips"

    if row["trips_flagged_for_review"] > 0:
        return "Review: flagged trip durations"

    if row["extreme_schedule_trip_count"] > 0:
        return "Review: extreme schedule times"

    return "No major duration flag detected"

df["data_quality_status"] = df.apply(classify_data_quality, axis=1)

# Preliminary screening score, not a measure of inefficiency.
df["priority_score"] = (
    0.50 * df["trip_volume_percentile"]
    + 25 * (df["trips_flagged_for_review"] > 0).astype(int)
    + 15 * (df["extreme_schedule_trip_count"] > 0).astype(int)
    + 10 * (df["shapes_with_large_gaps"].fillna(0) > 0).astype(int)
).clip(upper=100).round(2)

def explain_priority(row):
    reasons = []

    if row["trip_volume_percentile"] >= 80:
        reasons.append("High scheduled trip volume within city")

    if row["trips_flagged_for_review"] > 0:
        reasons.append("Trips flagged for duration review")

    if row["extreme_schedule_trip_count"] > 0:
        reasons.append("Extreme schedule times detected")

    if pd.notna(row["shapes_with_large_gaps"]) and row["shapes_with_large_gaps"] > 0:
        reasons.append("Shape segments need review")

    if row["unflagged_trip_count"] == 0:
        reasons.append("No unflagged trips available")

    if pd.isna(row["distance_available"]):
        reasons.append("Distance availability unknown")
    elif not row["distance_available"]:
        reasons.append("Distance unavailable")

    return "; ".join(reasons) if reasons else "No major screening signal"

df["priority_reasons"] = df.apply(explain_priority, axis=1)

# Keep the priority category separate from data quality.
df["priority_level"] = pd.cut(
    df["priority_score"],
    bins=[-1, 24.99, 49.99, 74.99, 100],
    labels=["Low", "Moderate", "High", "Very High"]
)

def investigation_category(row):
    if row["data_quality_status"] != "No major duration flag detected":
        return "Data quality review"

    if pd.notna(row["shapes_with_large_gaps"]) and row["shapes_with_large_gaps"] > 0:
        return "Route geometry review"

    if row["trip_volume_percentile"] >= 80:
        return "Upper-percentile trip count: investigate"

    return "Routine screening"
df["investigation_category"] = df.apply(
    investigation_category, axis=1
)

df = df.sort_values(
    ["city", "priority_score", "scheduled_trip_count"],
    ascending=[True, False, False]
)

df.to_csv(output_path, index=False)

print("Route-priority ranking created.")
print("Total routes:", len(df))
print("Cities:", df["city"].nunique())

print("\nPriority levels:")
print(df["priority_level"].value_counts().to_string())

print("\nData-quality status:")
print(df["data_quality_status"].value_counts().to_string())

print("\nInvestigation categories:")
print(df["investigation_category"].value_counts().to_string())

print("\nTop 5 routes per city:")
for city, group in df.groupby("city", sort=True):
    print("\n" + city)
    print(
        group[
            [
                "route_id",
                "scheduled_trip_count",
                "priority_score",
                "priority_level",
                "data_quality_status",
                "investigation_category",
            ]
        ].head(5).to_string(index=False)
    )

print("\nSaved:", output_path)
