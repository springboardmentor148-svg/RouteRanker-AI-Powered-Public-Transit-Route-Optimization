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

results = []

for city in cities:
	folder = DATA_DIR / city
	print(f"\n========== {city} ==========")

	for filename in required_files + ["calendar_dates.txt"]:
		path = folder / filename

		if path.exists():
			df = pd.read_csv(path, low_memory=False)
			status = "AVAILABLE" if len(df) > 0 else "EMPTY"

			print(f"{filename}: {status} | Records: {len(df)}")

			results.append(
				{
					"City": city,
					"File": filename,
					"Status": status,
					"Records": len(df),
				}
			)
		else:
			status = "MISSING"

			print(f"{filename}: MISSING")

			results.append(
				{
					"City": city,
					"File": filename,
					"Status": status,
					"Records": 0,
				}
			)

report = pd.DataFrame(results)

output_dir = PROJECT_DIR / "data" / "processed" / "module1"
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "module1_data_quality_check.csv"
report.to_csv(output_file, index=False)

print("\nQUALITY CHECK COMPLETED")
print("Saved:", output_file)
print(report.to_string(index=False))
