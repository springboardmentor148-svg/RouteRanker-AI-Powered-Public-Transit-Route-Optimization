\# RouteRanker – AI-Powered Public Transit Route Optimization



\## About the Project



RouteRanker is a public transit analytics project designed to help identify inefficient bus routes and support data-driven route optimization across Indian cities.



The project uses General Transit Feed Specification (GTFS) data to validate transit datasets, assess data quality, and prepare information for future route-performance analysis and AI-assisted optimization.



\## Objectives



\- Collect and organize GTFS datasets from multiple cities.

\- Validate transit data and check relationships between tables.

\- Generate data-quality reports.

\- Prepare data for feature engineering.

\- Explore ways to identify underperforming routes and improve transit services.



\## Project Structure



```text

PROJECT AIROUTE OPTIMIZER/

├── data/

│   └── raw/

├── reports/

│   └── data\_quality\_report.csv

├── check\_gtfs\_relationships.py

├── quality.py

├── validate-gtfs.py

├── .gitignore

└── README.md

```



\## GTFS Data



Common GTFS files include:



\- `routes.txt` – transit route information.

\- `trips.txt` – scheduled trips.

\- `stops.txt` – stop information.

\- `stop\_times.txt` – stop sequences and scheduled times.

\- `calendar.txt` – recurring service schedules, when available.

\- `calendar\_dates.txt` – service-date exceptions, when available.



Each city's dataset should be stored in its own folder under `data/raw/`.



\## Current Features



\- GTFS dataset validation.

\- GTFS relationship checking.

\- Data-quality analysis.

\- CSV data-quality reporting.



\## Running the Scripts



Run commands from the project root:



```bash

python validate-gtfs.py

python check\_gtfs\_relationships.py

python quality.py

```



These example commands may need adjustment if a script requires additional arguments or configuration.



\## Planned Improvements



\- Validate datasets across all selected cities.

\- Improve GTFS consistency checks.

\- Engineer time-based and route-level features.

\- Analyze route frequency and service patterns.

\- Develop route-performance indicators.

\- Explore machine-learning methods for route optimization.

\- Build a Streamlit dashboard for analysis and recommendations.



\## Technology



\- Python

\- GTFS transit data

\- CSV data analysis

\- Git and GitHub



\## Project Status



In development — currently focused on data validation and quality assessment before progressing to feature engineering and route optimization.



\## Author



Lee Rangwani

