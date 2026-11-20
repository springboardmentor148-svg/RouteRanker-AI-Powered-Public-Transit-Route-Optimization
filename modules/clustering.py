"""Cluster results of Module 5 (KMeans, DBSCAN) as applied to all routes in Module 6 - read from the saved outputs, nothing is hard-coded."""
import pandas as pd
import streamlit as st
from sklearn.decomposition import PCA

from src import inference as inf
from . import data_loader as dl

FEATURES = ["n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "avg_speed_kmh", "max_stop_overlap",
            "share_morning", "share_afternoon", "share_evening", "share_night"]


@st.cache_data(show_spinner="Projecting the routes with the saved preprocessor ...")
def embedding():
    """One row per route: features, KMeans cluster, DBSCAN label (from the Module-6 predictions) and a 2-D PCA projection of the 25 model features."""
    raw, models, pred = dl.load_routes(), dl.load_models(), dl.load_predictions()
    d, X = inf.prepare_new(raw, models["prep"])
    meta = raw[["city", "route_id"]].merge(pred.drop(columns=["route_name"]), on=["city", "route_id"], how="left").reset_index(drop=True)
    train = meta.data_role.fillna("").str.startswith("train").values
    pca = PCA(2, random_state=0).fit(X.values[train])
    P = pca.transform(X.values)
    out = d[["city", "route_id", "route_name"] + FEATURES].reset_index(drop=True).copy()
    out = pd.concat([out, meta.drop(columns=["city", "route_id"])], axis=1)
    out["pc1"], out["pc2"] = P[:, 0], P[:, 1]
    out["dbscan_group"] = out.dbscan_label.map(lambda x: "noise" if x == -1 else f"cluster {int(x)}")
    out.attrs["explained"] = float(pca.explained_variance_ratio_.sum())
    return out


@st.cache_data(show_spinner=False)
def kmeans_profile():
    prof = dl.load_table("module5_kmeans_cluster_profile.csv").set_index("cluster")
    names = inf.name_clusters(prof)
    prof.insert(0, "description", pd.Series(names))
    return prof


def cluster_summary(emb, role=None):
    d = emb if role is None else emb[emb.data_role == role]
    return d.groupby("kmeans_cluster").agg(routes=("route_id", "size"), median_trips=("n_trips", "median"), median_stops=("n_unique_stops", "median"),
                                           median_length_km=("length_km", "median"), median_span_h=("service_span_h", "median")).round(2)


def dbscan_summary(emb):
    return emb.groupby("data_role").agg(routes=("route_id", "size"), noise_routes=("dbscan_label", lambda s: int((s == -1).sum())),
                                        noise_pct=("dbscan_label", lambda s: round(100 * (s == -1).mean(), 1))).reset_index()
