"""Module 6 - model inference on new / unseen routes with the models and preprocessing objects saved in Modules 4 and 5.

Nothing is re-fitted here: the fitted RoutePreprocessor (medians, skew decisions, mean/std, categories), the KMeans model, the DBSCAN
model (core points) and the XGBoost / Random Forest diagnostics are loaded and applied to the new routes as they are.
Outputs are MODEL PREDICTIONS about scheduled service. They are not facts about passengers or route performance.
"""
import warnings
import joblib
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

from . import preprocessing as pp

warnings.filterwarnings("ignore", message=".*InconsistentVersionWarning.*")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")


def load_models(model_dir="models", prep_path="data/processed/module4/preprocessor.joblib"):
    return dict(prep=joblib.load(prep_path), kmeans=joblib.load(f"{model_dir}/kmeans_model.joblib"), dbscan=joblib.load(f"{model_dir}/dbscan_model.joblib"),
                xgb=joblib.load(f"{model_dir}/xgboost_city_diagnostic.joblib"), rf=joblib.load(f"{model_dir}/random_forest_city_diagnostic.joblib"))


def check_columns(df):
    derived = {c for c in pp.NUMERIC if c.startswith("share_")}            # created by add_derived from the trips_<period> columns
    needed = (set(pp.NUMERIC) - derived) | set(pp.ID_COLS) | {"peak_hour", "length_method", "trips_morning", "trips_afternoon", "trips_evening", "trips_night"}
    missing = sorted(needed - set(df.columns))
    if missing:
        raise ValueError(f"The new route table lacks required Module-2 feature columns: {missing}")


def prepare_new(df, prep):
    """Same transformations as in training: derived columns, then the FITTED preprocessor (no new scaler / encoder is fitted)."""
    check_columns(df)
    d = pp.add_derived(df)
    return d, prep.transform(d)


def dbscan_infer(db, X):
    """New route -> cluster of its nearest core point if that point is within eps, else noise (-1). Also returns that distance."""
    nn = NearestNeighbors(n_neighbors=1).fit(db.components_)
    dist, idx = nn.kneighbors(X)
    lab = db.labels_[db.core_sample_indices_][idx[:, 0]].copy()
    lab[dist[:, 0] > db.eps] = -1
    return lab, dist[:, 0]


def name_clusters(prof):
    """Plain-language description of each KMeans cluster from its median profile (Module 5 table). Descriptions are of scheduled service only."""
    names = {}
    q75 = prof.n_trips.quantile(.75)
    for c, r in prof.iterrows():
        p = []
        if r.n_trips <= 2: p.append("very few scheduled trips")
        elif r.n_trips >= q75: p.append("relatively many scheduled trips")
        for per in ("morning", "afternoon", "evening"):
            if r[f"share_{per}"] >= .6: p.append(f"mostly {per} departures")
        if r.n_unique_stops <= 6: p.append("very short route (few stops)")
        names[c] = "; ".join(p) if p else "mixed-day, mid-range service"
    return names


def run_inference(df, models, cluster_names):
    d, X = prepare_new(df, models["prep"])
    feats = list(X.columns)
    Xv = X.values
    km = models["kmeans"]
    dist_c = km.transform(Xv)
    out = d[["city", "route_id", "route_name"]].copy()
    out["kmeans_cluster"] = dist_c.argmin(axis=1)
    out["kmeans_cluster_description"] = out.kmeans_cluster.map(cluster_names)
    out["dist_to_centroid"] = dist_c.min(axis=1).round(3)
    out["dbscan_label"], out["dist_to_nearest_core"] = dbscan_infer(models["dbscan"], Xv)
    out["dist_to_nearest_core"] = out.dist_to_nearest_core.round(3)
    classes = sorted(pd.read_csv("data/processed/module4/train_preprocessed.csv", usecols=["city"]).city.unique())
    proba = models["xgb"].predict_proba(Xv)
    out["closest_known_feed"] = np.array(classes)[proba.argmax(axis=1)]
    out["closest_feed_probability"] = proba.max(axis=1).round(3)
    return d, X, out
