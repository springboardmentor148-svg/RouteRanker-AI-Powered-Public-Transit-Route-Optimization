from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

cities = ["Banglore", "Delhi", "Hyderabad", "Mumbai", "Pune"]

required_files = [
	"routes.txt",
	"trips.txt",
	"stop_times.txt",
	"stops.txt",
	"calendar.txt",
]

inventory = []

for city in cities:
	city_folder = DATA_DIR / city
	print(f"\nChecking {city}")

	for filename in required_files:
		file_path = city_folder / filename

		if file_path.exists():
			df = pd.read_csv(file_path, low_memory=False)
			inventory.append(
				{
					"City": city,
					"GTFS_File": filename,
					"Status": "AVAILABLE",
					"Total_Records": len(df),
					"Total_Columns": len(df.columns),
					"Column_Names": ", ".join(df.columns),
				}
			)
			print(f"{filename}: AVAILABLE | {len(df)} records")
		else:
			inventory.append(
				{
					"City": city,
					"GTFS_File": filename,
					"Status": "MISSING",
					"Total_Records": 0,
					"Total_Columns": 0,
					"Column_Names": "",
				}
			)

report = pd.DataFrame(inventory)

output_dir = PROJECT_DIR / "data" / "processed" / "module1"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "module1_final_gtfs_inventory.csv"
report.to_csv(output_file, index=False)

print("\n===================================")
print("MODULE 1 FINAL INVENTORY COMPLETED")
print("Total checks:", len(report))
print("Available files:", (report["Status"] == "AVAILABLE").sum())
print("Missing files:", (report["Status"] == "MISSING").sum())
print("Saved at:", output_file)
print("===================================")
