# Module 1: Data Collection and Dataset Understanding

## 1. Objective
The objective of this module was to collect GTFS (General Transit Feed Specification) datasets from five Indian cities and understand their structure and relationships.

## 2. Dataset Source
GTFS datasets were obtained from Mobility Database.

## 3. Cities Covered
- Bangalore
- Delhi
- Hyderabad
- Mumbai
- Pune

## 4. GTFS Files Collected
The following essential files were inspected for each city:
- routes.txt
- trips.txt
- stop_times.txt
- stops.txt
- calendar.txt

## 5. Data Loading
Python Pandas was used to load the GTFS text files and inspect their records.

All five required files were found in each of the five city folders, giving 25 successful file-availability checks.

## 6. Data Inspection and Validation
The project includes scripts and reports for:
- GTFS file loading and record counts.
- Required column verification.
- Route, trip and stop ID relationship verification.
- Consolidated GTFS file inventory.

The actual column and relationship verification results should be reviewed before reporting that all checks passed.

## 7. Generated Outputs
The Module 1 output folder contains:
- all_cities_gtfs_loading_summary.csv
- all_cities_gtfs_column_verification.csv
- all_cities_gtfs_relationship_verification.csv
- module1_final_gtfs_inventory.csv

## 8. Limitations
- The datasets contain scheduled transit information.
- Each city's calendar.txt was found to contain one record.
- calendar_dates.txt availability must be checked separately.
- Scheduled GTFS data does not directly provide passenger counts, occupancy or actual traffic congestion.
- calendar_dates.txt availability must be checked separately.
- calendar_dates.txt was not present in any of the five city datasets.
- Each city contains one record in calendar.txt. Additional calendar service-date validation may be required.

## 9. Conclusion
The GTFS datasets for Bangalore, Delhi, Hyderabad, Mumbai and Pune were collected and loaded successfully. Their file structures, record counts and key relationships were examined through Python and Pandas. The collected datasets provide a foundation for Module 2: Feature Engineering.
