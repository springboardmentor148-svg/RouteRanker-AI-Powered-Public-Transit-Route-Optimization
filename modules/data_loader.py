"""Loading of the project's EXISTING data and outputs (Modules 2-6) for the dashboard. No new dataset is introduced and nothing is hard-coded:
every table shown in the app is read from the files that the run_module*.py scripts wrote."""
import os
import pandas as pd
import streamlit as st

from src import inference as inf, preprocessing as pp

PROC = "data/processed"
CITIES = ["ahmedabad", "bengaluru", "chennai", "delhi", "hyderabad", "kochi", "pune"]
EXCLUDED_FEEDS = list(pp.EXCLUDE_FEEDS)                      # feeds that are not comparable with the others (Module 4)
REQUIRED = {
    "route features (Module 2)": f"{PROC}/all_cities_route_features.csv",
    "hourly features (Module 2)": f"{PROC}/pune/route_hour_features.csv",
    "stop usage (Module 2)": f"{PROC}/pune/stop_usage.csv",
    "preprocessed data (Module 4)": f"{PROC}/module4/train_preprocessed.csv",
    "KMeans model (Module 5)": "models/kmeans_model.joblib",
    "DBSCAN model (Module 5)": "models/dbscan_model.joblib",
    "XGBoost model (Module 5)": "models/xgboost_city_diagnostic.joblib",
    "Random Forest model (Module 5)": "models/random_forest_city_diagnostic.joblib",
    "cluster profile (Module 5)": "reports/tables/module5_kmeans_cluster_profile.csv",
    "predictions (Module 6)": "data/inference/inference_predictions.csv",
    "simulated network (Module 6)": "data/simulated/simulated_network.csv",
    "scenario metrics (Module 6)": "reports/tables/module6_current_vs_simulated_metrics.csv",
}
RUN_HINT = {"Module 2": "python run_module2.py", "Module 4": "python run_module4.py", "Module 5": "python run_module5.py", "Module 6": "python run_module6.py"}


def missing_files():
    return {k: v for k, v in REQUIRED.items() if not os.path.exists(v)}


@st.cache_data(show_spinner=False)
def load_routes():
    return pp.load_features(f"{PROC}/all_cities_route_features.csv")


@st.cache_data(show_spinner=False)
def load_route_hours(city=None):
    cities = [city] if city else CITIES
    parts = []
    for c in cities:
        p = f"{PROC}/{c}/route_hour_features.csv"
        if os.path.exists(p):
            parts.append(pd.read_csv(p, dtype={"route_id": str}).assign(city=c))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_stops(city):
    p = f"{PROC}/{city}/stop_usage.csv"
    return pd.read_csv(p, dtype={"stop_id": str}) if os.path.exists(p) else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_predictions():
    return pd.read_csv("data/inference/inference_predictions.csv", dtype={"route_id": str, "route_name": str})


@st.cache_data(show_spinner=False)
def load_table(name):
    p = f"reports/tables/{name}"
    return pd.read_csv(p, dtype={"route_id": str, "absorbed_route_id": str, "target_route_id": str}) if os.path.exists(p) else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_simulated():
    return pd.read_csv("data/simulated/simulated_network.csv", dtype={"route_id": str})


@st.cache_data(show_spinner=False)
def load_module4_validation():
    return pd.read_csv(f"{PROC}/module4/validation_preprocessed.csv", dtype={"route_id": str, "route_name": str})


@st.cache_resource(show_spinner=False)
def load_models():
    return inf.load_models()
