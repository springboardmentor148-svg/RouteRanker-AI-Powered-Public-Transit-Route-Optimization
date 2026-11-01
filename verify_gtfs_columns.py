from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

cities = ["Banglore", "Delhi", "Hyderabad", "Mumbai", "Pune"]

required_columns = {
	"routes.txt": ["route_id"],
	"trips.txt": ["route_id", "service_id", "trip_id"],
	"stop_times.txt": [
		"trip_id",
		"arrival_time",
		"departure_time",
		"stop_id",
		"stop_sequence",
	],
	"stops.txt": ["stop_id", "stop_name"],
	"calendar.txt": [
		"service_id",
		"monday",
		"tuesday",
		"wednesday",
		"thursday",
		"friday",
		"saturday",
		"sunday",
		"start_date",
		"end_date",
	],
}

results = []

for city in cities:
	print(f"\n========== {city} ==========")
	city_folder = DATA_DIR / city

	for filename, columns in required_columns.items():
		file_path = city_folder / filename

		if not file_path.exists():
			print(f"{filename}: FILE NOT FOUND")
			results.append(
				{
					"City": city,
					"File": filename,
					"Status": "FILE NOT FOUND",
					"Missing Columns": "File missing",
				}
			)
			continue

		df = pd.read_csv(file_path, nrows=5, low_memory=False)
		available = list(df.columns)
		missing = [column for column in columns if column not in available]
		status = "PASS" if not missing else "MISSING COLUMNS"

		print(f"{filename}: {status}")
		if missing:
			print("Missing:", missing)
		else:
			print("All required columns are available.")

		results.append(
			{
				"City": city,
				"File": filename,
				"Status": status,
				"Missing Columns": ", ".join(missing),
			}
		)

report = pd.DataFrame(results)

output_dir = PROJECT_DIR / "data" / "processed" / "module1"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "all_cities_gtfs_column_verification.csv"
report.to_csv(output_file, index=False)

print("\n================================")
print("COLUMN VERIFICATION COMPLETED")
print("Report saved at:", output_file)
print("================================")
print(report.to_string(index=False))
