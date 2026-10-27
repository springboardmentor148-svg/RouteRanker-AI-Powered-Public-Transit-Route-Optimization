
import pandas as pd
from pathlib import Path

reports_dir = Path("reports")

# Load all eight route-feature reports.
route_files = sorted(reports_dir.glob("*_route_features.csv"))

if not route_files:
    raise FileNotFoundError(
        "No *_route_features.csv files found in reports/"
    )

route_frames = []

for file_path in route_files:
    frame = pd.read_csv(
        file_path,
        dtype={"city": str, "route_id": str}
    )
    route_frames.append(frame)

routes = pd.concat(route_frames, ignore_index=True)

# Load the shape-based route-distance report.
distances = pd.read_csv(
    reports_dir / "route_distance_features.csv",
    dtype={"city": str, "route_id": str}
)

# Confirm each city/route combination is unique before joining.
keys = ["city", "route_id"]

if routes.duplicated(keys).any():
    raise ValueError("Duplicate city/route IDs in route features.")

if distances.duplicated(keys).any():
    raise ValueError("Duplicate city/route IDs in distance features.")

# Keep every route, even when its distance is unavailable.
combined = routes.merge(
    distances,
    on=keys,
    how="left",
    validate="one_to_one"
)

# Clearly distinguish missing geometry from calculated distances.
combined["distance_available"] = (
    combined["median_shape_distance_km"].notna()
)

combined["distance_status"] = combined["distance_available"].map(
    {True: "Available", False: "Unavailable"}
)

output_path = reports_dir / "combined_route_features.csv"
combined.to_csv(output_path, index=False)

print("Combined route-feature report created.")
print("Route-feature rows:", len(routes))
print("Combined rows:", len(combined))
print("Routes with distance:", int(
    combined["distance_available"].sum()
))
print("Routes without distance:", int(
    (~combined["distance_available"]).sum()
))
print("\nDistance availability by city:")
print(
    combined.groupby("city")["distance_available"]
    .agg(["count", "sum"])
    .to_string()
)
print("\nSaved:", output_path)

