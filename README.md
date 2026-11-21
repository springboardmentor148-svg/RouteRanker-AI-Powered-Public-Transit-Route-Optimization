# RouteRanker Dashboard

## Overview

RouteRanker is a Streamlit dashboard for exploring the project GTFS datasets, route and hourly trip patterns, clustering results, Random Forest predictions, optimization recommendations, and simulated before/after metrics.

## Installation

```bash
python -m pip install -r requirements.txt
```

## Run

From the project directory:

```bash
python -m streamlit run app.py
```

Open the local URL printed by Streamlit.

## Upload GTFS data

In **Dataset Overview**, provide a ZIP archive containing these five files:

- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `stops.txt`
- `calendar.txt`

The files can be at the ZIP root or inside a city-named folder. Enter the city name in the dashboard. The app cleans duplicates and whitespace, converts supported numeric fields, calculates route trip frequency and hourly frequency when source columns are available, and displays downloadable integrated CSV outputs.

## Dashboard sections

- Home
- Dataset Overview
- Exploratory Data Analysis
- Route Analysis
- K-Means and DBSCAN Clustering
- Random Forest Prediction Results
- Route Optimization Recommendations
- Current vs. Simulated Metrics
- About and Limitations

## Data and model files

The dashboard loads the existing CSV data and saved `routeranker_rf_model.pkl` and `routeranker_scaler.pkl` artifacts from the project directory.

Generated clustering labels and route metrics are recomputed in the dashboard from existing data. The saved Random Forest model accepts:

1. Total scheduled trips
2. Peak-hour ratio

No XGBoost model artifact is currently stored in the workspace, so XGBoost is reported as unavailable rather than represented with fabricated results.

## Important limitations

Clusters are descriptive and must not be interpreted as confirmed efficient or inefficient routes. Optimization recommendations are proposals or simulations, not validated operational changes. Additional passenger-demand and stop-coverage evidence is required before implementation.
