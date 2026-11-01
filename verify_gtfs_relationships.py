from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

cities = ["Banglore", "Delhi", "Hyderabad", "Mumbai", "Pune"]

results = []

for city in cities:
	print(f"\n========== {city} ==========")
	folder = DATA_DIR / city

	routes = pd.read_csv(folder / "routes.txt", usecols=["route_id"])
	trips = pd.read_csv(
		folder / "trips.txt",
		usecols=["trip_id", "route_id", "service_id"]
	)
	stops = pd.read_csv(folder / "stops.txt", usecols=["stop_id"])
	stop_times = pd.read_csv(
		folder / "stop_times.txt",
		usecols=["trip_id", "stop_id"]
	)

	checks = {
		"Trips route IDs": trips["route_id"].isin(routes["route_id"]).all(),
		"Stop times trip IDs": stop_times["trip_id"].isin(trips["trip_id"]).all(),
		"Stop times stop IDs": stop_times["stop_id"].isin(stops["stop_id"]).all()
	}

	for check_name, passed in checks.items():
		status = "PASS" if passed else "FAIL"
		print(f"{check_name}: {status}")

		results.append({
			"City": city,
			"Relationship": check_name,
			"Status": status
		})

	print("Trips:", len(trips))
	print("Stop times:", len(stop_times))

report = pd.DataFrame(results)

output_dir = PROJECT_DIR / "data" / "processed" / "module1"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "all_cities_gtfs_relationship_verification.csv"
report.to_csv(output_file, index=False)

print("\nRelationship verification completed!")
print("Report saved:", output_file)
print(report.to_string(index=False))
