import pandas as pd
from pathlib import Path

input_path = Path("reports/combined_route_features.csv")
output_path = Path("reports/city_summary.csv")

df = pd.read_csv(
    input_path,
    dtype={"city": str, "route_id": str}
)

summary = df.groupby("city").agg(
    total_routes=("route_id", "nunique"),
    total_scheduled_trips=("scheduled_trip_count", "sum"),
    routes_with_distance=("distance_available", "sum"),
    routes_flagged_for_duration=(
        "route_duration_quality",
        lambda values: values.astype(str).str.contains(
            "Review", case=False
        ).sum()
    ),
    routes_with_extreme_schedules=(
        "extreme_schedule_trip_count",
        lambda values: (values > 0).sum()
    )
).reset_index()

summary["distance_coverage_percent"] = (
    summary["routes_with_distance"]
    / summary["total_routes"] * 100
).round(2)

summary.to_csv(output_path, index=False)

print("City summary created.")
print(summary.to_string(index=False))
print("\nSaved:", output_path)