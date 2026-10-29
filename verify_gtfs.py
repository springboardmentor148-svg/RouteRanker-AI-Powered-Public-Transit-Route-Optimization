
from pathlib import Path
import pandas as pd

DATA = Path("data/raw")

cities = [
    "Hyderabad", "Mumbai", "Pune",
    "Chennai", "Ahmedabad", "Rajkot"
]

required = [
    "routes.txt",
    "trips.txt",
    "stop_times.txt",
    "stops.txt"
]

for city in cities:
    folder = DATA / city
    print("\nCity:", city)

    for filename in required:
        path = folder / filename

        if path.is_file():
            try:
                df = pd.read_csv(path, nrows=5)
                print(filename, "- FOUND")
                print("Columns:", df.columns.tolist())
            except Exception as e:
                print(filename, "- READ ERROR:", e)
        else:
            print(filename, "- NOT FOUND")

    
    calendar = folder / "calendar.txt"
    dates = folder / "calendar_dates.txt"

    if calendar.is_file():
        df = pd.read_csv(calendar, nrows=5)
        print("calendar.txt - FOUND")
        print("Columns:", df.columns.tolist())

    elif dates.is_file():
        df = pd.read_csv(dates, nrows=5)
        print("calendar_dates.txt - FOUND")
        print("Columns:", df.columns.tolist())

    else:
        print("Calendar - NOT FOUND")
