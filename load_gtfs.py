from pathlib import Path
import pandas as pd

# Folder containing the Hyderabad GTFS files
DATA_FOLDER = Path("data/raw/Hyderabad")

# Required GTFS files
file_names = [
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "stops.txt",
    "calendar.txt"
]

# Store loaded DataFrames here
gtfs_data = {}

print("ROUTERANKER - GTFS DATA LOADING")
print("=" * 45)

for file_name in file_names:
    file_path = DATA_FOLDER / file_name

    if file_path.exists():
        df = pd.read_csv(file_path, low_memory=False)
        gtfs_data[file_name.replace(".txt", "")] = df

        print(f"\nFile: {file_name}")
        print("Shape (rows, columns):", df.shape)
        print("Columns:", df.columns.tolist())
        print(df.head(3))
    else:
        print(f"\nMISSING FILE: {file_path}")

print("\n" + "=" * 45)
print("DATA LOADING CHECK COMPLETED")
print("Files loaded:", len(gtfs_data), "out of", len(file_names))

