# RouteRanker – AI-Powered Public Transit Route Optimization

## 1. Project Overview

RouteRanker is an AI-powered public transit route optimization project. It aims to study public transportation route structures and scheduled services to identify possible inefficiencies, such as overlapping routes, differences in service frequency, and potential underutilization.

The project uses General Transit Feed Specification (GTFS) datasets to understand routes, trips, stops, and scheduled timings.

## 2. Project Objective

The main objectives are:

- Collect and understand GTFS datasets from selected Indian cities.
- Study the relationships between routes, trips, stops, and scheduled timings.
- Identify possible public transit service inefficiencies.
- Prepare datasets for feature engineering and exploratory data analysis.
- Support subsequent machine learning and route optimization activities.

## 3. Cities Covered

The current project dataset covers five Indian cities:

1. Bangalore (project folder: `Banglore`)
2. Hyderabad
3. Delhi
4. Mumbai
5. Pune

**Dataset Source:** Mobility Database.

## 4. GTFS Dataset Files

The following main GTFS files were collected and inspected for all five cities:

| File | Description |
|---|---|
| `routes.txt` | Contains public transportation route information. |
| `trips.txt` | Contains scheduled trip information. |
| `stop_times.txt` | Contains scheduled arrival and departure times at stops. |
| `stops.txt` | Contains stop names, IDs, and available location information. |
| `calendar.txt` | Contains scheduled service days and date ranges. |

The optional GTFS files were also checked for availability. Files not supplied in a city dataset are documented in the inventory.

## 5. Module 1: Data Collection and Dataset Understanding

Module 1 focused on collecting and understanding GTFS datasets.

The completed activities include:

- Collecting GTFS datasets for five cities.
- Organizing the raw datasets city-wise.
- Loading GTFS text files using Python and Pandas.
- Inspecting file names, columns, record counts, and file sizes.
- Understanding relationships between GTFS files.
- Checking duplicate IDs and missing values in important columns.
- Checking relationships between routes, trips, and stops.
- Preparing data inventory and data quality reports.

## 6. Data Quality Findings

Initial data quality checks were performed for all five cities.

The following issues were investigated:

- Duplicate route IDs.
- Duplicate trip IDs.
- Duplicate stop IDs.
- Missing values in important columns.
- Invalid references between GTFS files.

**Delhi dataset finding:**

Eight duplicate trip IDs were identified in Delhi's `trips.txt`, involving 16 rows. All eight duplicate extra rows were confirmed as exact duplicate records.

The original raw dataset has been preserved without modification. These duplicate records will be handled during the data preprocessing stage.

## 7. Project Folder Structure

```text
routeranker-upload/
│
├── data/
│   ├── raw/
│   │   ├── Banglore/
│   │   ├── Hyderabad/
│   │   ├── Delhi/
│   │   ├── Mumbai/
│   │   └── Pune/
│   │
│   └── processed/
│
├── notebooks/
│   └── module1_data_collection.ipynb
│
├── reports/
│   ├── assumptions_and_limitations.md
│   ├── module1_final_verification.csv
│   ├── module1_data_inventory.csv
│   ├── module1_city_inventory_summary.csv
│   ├── module1_data_quality_report.csv
│   ├── delhi_duplicate_trip_details.csv
│   ├── delhi_duplicate_trip_investigation.csv
│   └── module1_dataset_understanding.md
│
└── README.md
```

## 8. Reports and Deliverables

The `reports` folder contains:

- `module1_final_verification.csv` – verification of required GTFS files.
- `module1_data_inventory.csv` – detailed information about available GTFS files, records, columns, and file sizes.
- `module1_city_inventory_summary.csv` – city-wise dataset summary.
- `module1_data_quality_report.csv` – initial data quality checking results.
- `delhi_duplicate_trip_details.csv` – details of duplicate Delhi trip records.
- `delhi_duplicate_trip_investigation.csv` – investigation of duplicate trip IDs and their stop-times records.
- `module1_dataset_understanding.md` – GTFS file descriptions and relationships.
- `assumptions_and_limitations.md` – project assumptions and identified limitations.

## 9. Technologies Used

- Python
- Pandas
- Jupyter Notebook
- Visual Studio Code
- GTFS datasets
- Git and GitHub

## 10. Next Project Stages

The project will continue with the following stages:

1. Feature Engineering
2. Exploratory Data Analysis (EDA)
3. Data Preprocessing
4. Machine Learning
5. Public Transit Route Optimization

## 11. Conclusion

Module 1 established the foundation for the RouteRanker project by collecting and inspecting GTFS datasets from five Indian cities.

The datasets were organized city-wise, their structures and relationships were studied, and initial data quality checks were completed. The identified Delhi duplicate trip records have been documented for future preprocessing.

These datasets will support the next stages of feature engineering, data analysis, and public transit route optimization.
