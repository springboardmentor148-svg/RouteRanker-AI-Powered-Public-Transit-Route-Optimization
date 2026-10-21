# RouteRanker – AI-Powered Public Transit Route Optimization

## Project Overview

RouteRanker is a project focused on analyzing public transportation routes across major Indian cities to identify potential inefficiencies in public transit networks.

The project aims to study route overlaps, scheduled service frequency, stop locations, and service patterns to support future data-driven public transportation analysis and route optimization.

## Objectives

- Collect publicly available General Transit Feed Specification (GTFS) datasets for Indian cities.
- Understand the structure and relationships between transit data files.
- Inspect routes, trips, stops, schedules, and service calendars.
- Prepare datasets for future data cleaning, exploratory data analysis (EDA), feature engineering, and route optimization.

## Current Module: Module 1 – Data Collection and Dataset Understanding

This module establishes the data foundation for the RouteRanker project.

### Tasks

1. Identify and collect suitable GTFS datasets.
2. Organize the raw datasets city-wise.
3. Load GTFS text files into Pandas DataFrames using Python.
4. Inspect column names, dataset dimensions, and sample records.
5. Understand relationships between routes, trips, stops, and service calendars.

## Technologies Used

- **Python** – Data loading and inspection
- **Pandas** – Tabular data processing
- **Visual Studio Code** – Development environment
- **Git and GitHub** – Version control and collaboration
- **GTFS** – Standard format for public transportation data

## GTFS Dataset Structure

The project uses the following core GTFS files:

| File | Description |
|---|---|
| `routes.txt` | Defines transit routes and route identifiers |
| `trips.txt` | Contains trips associated with routes and services |
| `stop_times.txt` | Contains scheduled arrival and departure times at stops |
| `stops.txt` | Contains stop identifiers, names, and location information |
| `calendar.txt` | Defines regular service operating days and date ranges |

*Note: Some GTFS feeds may use additional files or `calendar_dates.txt` for service exceptions.*

## Project Folder Structure

```text
RouteRanker/
├── data/
│   └── raw/
│       ├── Hyderabad/
│       ├── Bangalore/
│       ├── Delhi/
│       ├── Mumbai/
│       └── Pune/
├── load_gtfs.py
├── README.md
└── .gitignore
```

Each city folder is intended to contain the available GTFS text files. The actual files may vary depending on the dataset source.

## Loading GTFS Files with Python

Install Pandas:

```bash
python -m pip install pandas
```

Run the data loading script from the project directory:

```bash
python load_gtfs.py
```

The script reads available GTFS files into Pandas DataFrames and displays dataset dimensions, column names, and sample records.

Ensure that the file paths in the script match the actual folder structure on your computer.

## Expected Outcomes

- A structured collection of GTFS datasets.
- Initial understanding of the available transit data.
- Inspection of rows, columns, and sample records.
- Identification of missing files and potential data quality issues.
- A foundation for subsequent analysis and route optimization tasks.

## Future Work

Future project stages may include:

- Data cleaning and preprocessing
- Exploratory data analysis
- Route overlap analysis
- Service frequency analysis
- Feature engineering
- Machine learning-based analysis
- Public transit route optimization

These activities will be undertaken in subsequent modules.

## Dataset Sources

GTFS datasets should be obtained from official transit agencies or trusted public transit data repositories, such as [Mobility Database](https://mobilitydatabase.org/), subject to dataset availability and licensing.

Raw datasets are not necessarily included in this repository. Consult the source feed's documentation and license before redistribution.

## Contribution

This project is developed collaboratively as part of the RouteRanker project. Contributions should follow the team's GitHub branching and review process.

## License

Add the applicable project license and dataset attribution requirements once they have been confirmed by the project maintainers.
