
import pandas as pd

before = pd.read_csv("data/raw/Hyderabad/routes.txt")
after = pd.read_csv(
    "data/processed/Hyderabad_routes_cleaned.csv"
)

print("Before cleaning:")
print("Rows:", len(before))
print("Missing route IDs:", before["route_id"].isna().sum())

print("\nAfter cleaning:")
print("Rows:", len(after))
print("Missing route IDs:", after["route_id"].isna().sum())
