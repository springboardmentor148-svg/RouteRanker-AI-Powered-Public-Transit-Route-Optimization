import pandas as pd
from pathlib import Path

# Project folder
folder = Path(__file__).parent

# CSV files for each city
city_files = {
    "Bengaluru": "bengaluru_routes_integrated.csv",
    "Chennai": "chennai_routes_integrated.csv",
    "Delhi": "delhi_routes_integrated.csv",
    "Hyderabad": "hyderabad_routes_integrated.csv",
    "Kolkata": "kolkata_routes_integrated.csv",
    "Mumbai": "mumbai_routes_integrated.csv",
}

for city, filename in city_files.items():

    input_file = folder / filename

    # Check whether the input file exists
    if not input_file.exists():
        print(f"\n{city}: CSV file not found: {filename}")
        continue

    # Loa the correct city's data
    df = pd.read_csv(input_file)

    print(f"\n{city} dataset loaded successfully!")
    print("Rows:", len(df))
    print("Columns:", len(df.columns))
    print(df.head(3).to_string(index=False))

    # Export to Excel
    output_file = folder / f"{city.lower()}_routes_integrated.xlsx"

    df.to_excel(output_file, index=False)

    print(f"Excel file created: {output_file.name}")

print("\nProcessing completed!")
