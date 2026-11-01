from pathlib import Path
import pandas as pd

# Project folder is the folder containing this Python file
PROJECT_DIR = Path(__file__).resolve().parent

# GTFS data location
DATA_DIR = PROJECT_DIR / "data" / "raw"

cities = {
	"Banglore": "Banglore",
	"Delhi": "Delhi",
	"Hyderabad": "Hyderabad",
	"Mumbai": "Mumbai",
	"Pune": "Pune",
}

required_files = [
	"routes.txt",
	"trips.txt",
	"stop_times.txt",
	"stops.txt",
	"calendar.txt",
]

for city_name, folder_name in cities.items():
	print(f"\n========== {city_name} ==========")
	city_folder = DATA_DIR / folder_name

	if not city_folder.exists():
		print("CITY FOLDER NOT FOUND:", city_folder)
		continue

	for filename in required_files:
		file_path = city_folder / filename

		if file_path.exists():
			df = pd.read_csv(file_path, low_memory=False)
			print(f"{filename}: FOUND | Records: {len(df)}")
		else:
			print(f"{filename}: NOT FOUND")
