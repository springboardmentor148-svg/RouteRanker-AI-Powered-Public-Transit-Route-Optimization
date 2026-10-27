
import pandas as pd
from pathlib import Path

input_path = Path("reports/combined_route_features.csv")
output_path = Path("reports/route_priority_ranking.csv")

df = pd.read_csv(
    input_path,
    dtype={"city": str, "route_id": str}
)

# Convert expected numeric columns safely.
numeric_columns = [
    "scheduled_trip_count",
    "trips_flagged_for_review",
    "extreme_schedule_trip_count",
    "shapes_with_large_gaps",
    "distance_available",
]

for column in numeric_columns:
    if column == "distance_available":
        df[column] = df[column].fillna(False).astype(bool)
    else:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

# Compare service volume within each city, not across cities.
df["trip_volume_percentile"] = (
    df.groupby("city")["scheduled_trip_count"]
    .rank(pct=True)
    .mul(100)
    .round(2)
)

# Transparent investigation score; not a measure of true inefficiency.
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

    if not row["distance_available"]:
        reasons.append("Distance unavailable")

    return "; ".join(reasons) if reasons else "No major screening signal"

df["priority_reasons"] = df.apply(explain_priority, axis=1)

df["priority_level"] = pd.cut(
    df["priority_score"],
    bins=[-1, 24.99, 49.99, 74.99, 100],
    labels=["Low", "Moderate", "High", "Very High"]
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
                "priority_reasons",
            ]
        ].head(5).to_string(index=False)
    )

print("\nSaved:", output_path)
