
import pandas as pd
from pathlib import Path

DATA = Path("data/raw")

cities = [
    "Hyderabad", "Mumbai", "Pune",
    "Chennai", "Ahmedabad", "Rajkot"
]

summary = []

for city in cities:
    folder = DATA / city
    row = {"City": city}

    for name in ["routes", "trips", "stops"]:
        path = folder / (name + ".txt")

        if path.exists():
            try:
                count = 0
                for chunk in pd.read_csv(
                    path, chunksize=100000, dtype=str
                ):
                    count += len(chunk)

                row[name.capitalize()] = count
            except Exception as e:
                row[name.capitalize()] = "Error"
                print(city, name, e)
        else:
            row[name.capitalize()] = "Missing"

    summary.append(row)

result = pd.DataFrame(summary)

print("\nGTFS DATASET INVENTORY")
print(result.to_string(index=False))

result.to_csv("dataset_inventory.csv", index=False)

print("\nInventory saved successfully!")
