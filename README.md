# RouteRanker

AI-powered public transit route analysis and optimization using GTFS data.

## Project Overview

RouteRanker analyzes public transit schedule data to identify route patterns and support data-driven service planning.

## Study Cities

- Ahmedabad
- Chennai
- Hyderabad
- Mumbai
- Pune

## Module 1: Data Preprocessing and Analysis

The current pipeline includes:

1. GTFS conversion to CSV.
2. Data cleaning and preprocessing.
3. Missing-value and data-quality analysis.
4. GTFS relationship validation.
5. Stop-sequence and timing checks.
6. Route-level indicator generation.
7. Exploratory data analysis (EDA).
8. K-Means route clustering.

## Project Structure

- `notebook/` - Python scripts for preprocessing, validation, EDA, and clustering.
- `reports/` - Validation reports, route indicators, analysis summaries, and clustering outputs.
- `data/` - Local GTFS datasets, excluded from Git tracking.

## Data

GTFS datasets are kept locally and are not included in this repository because of their size. Obtain the datasets from their original providers and place them in the expected `data/raw/` folders before running the scripts.

## Important Limitations

- GTFS schedules describe planned service, not actual passenger counts.
- Cluster labels indicate algorithmic groupings, not confirmed overcrowding or underutilization.
- Routes without scheduled trips require further review; they should not automatically be considered inactive.
- Timing anomalies should be checked against the source data before corrections are made.

## Current Status

Module 1: GTFS preprocessing, data-quality checks, route indicators, EDA, and initial K-Means clustering completed.

## Technologies

Python, pandas, scikit-learn, Matplotlib, and GTFS data.
