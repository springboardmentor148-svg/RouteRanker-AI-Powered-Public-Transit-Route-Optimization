"""Module 5 - clustering (KMeans, DBSCAN) and a supervised diagnostic (Random Forest, XGBoost) on the Module-4 data.

Clusters group routes by SIMILAR SCHEDULED SERVICE. They are not performance categories and not recommendations.
No passenger or performance label exists in GTFS, so no such label is created; the only supervised task uses a real
label that is in the data: the city a route belongs to (a diagnostic of how comparable the feeds are).
"""
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import (accuracy_score, adjusted_rand_score, confusion_matrix, davies_bouldin_score,
                             precision_recall_fscore_support, silhouette_score)
from sklearn.neighbors import NearestNeighbors

IDS = ["city", "route_id", "route_name"]
D4 = "data/processed/module4"


def load_module4(d=D4):
    tr, va = pd.read_csv(f"{d}/train_preprocessed.csv", dtype={"route_id": str, "route_name": str}), pd.read_csv(f"{d}/validation_preprocessed.csv", dtype={"route_id": str, "route_name": str})
    return tr, va, [c for c in tr.columns if c not in IDS]


# ------------------------------------------------------------------ KMeans
def kmeans_sweep(X, ks=range(2, 11), seed=42, sil_sample=6000):
    rows = []
    for k in ks:
        km = KMeans(k, n_init=10, random_state=seed).fit(X)
        rows.append(dict(k=k, inertia=km.inertia_, silhouette=silhouette_score(X, km.labels_, sample_size=min(sil_sample, len(X)), random_state=seed),
                         davies_bouldin=davies_bouldin_score(X, km.labels_), smallest_cluster_share=np.bincount(km.labels_).min() / len(X)))
    return pd.DataFrame(rows)


def elbow_k(sweep):
    """Point of the inertia curve farthest from the straight line between its two ends (simple 'knee' rule)."""
    x, y = sweep.k.values.astype(float), sweep.inertia.values
    xn, yn = (x - x.min()) / (x.max() - x.min()), (y - y.min()) / (y.max() - y.min())
    d = np.abs(xn + yn - 1) / np.sqrt(2)           # line from (0,1) to (1,0)
    return int(x[d.argmax()])


def choose_k(sweep, lo=3, hi=8, min_share=0.02):
    """Highest silhouette for k in [lo, hi] where no cluster is smaller than 2% of the routes (avoids tiny splinter clusters)."""
    c = sweep[(sweep.k >= lo) & (sweep.k <= hi) & (sweep.smallest_cluster_share >= min_share)]
    c = c if len(c) else sweep[(sweep.k >= lo) & (sweep.k <= hi)]
    return int(c.loc[c.silhouette.idxmax(), "k"])


def kmeans_stability(X, k, seeds=(1, 2, 3, 4, 5)):
    base = KMeans(k, n_init=10, random_state=0).fit(X).labels_
    return [adjusted_rand_score(base, KMeans(k, n_init=10, random_state=s).fit(X).labels_) for s in seeds]


# ------------------------------------------------------------------ DBSCAN
def kdistance(X, k):
    nn = NearestNeighbors(n_neighbors=k + 1).fit(X)
    return np.sort(nn.kneighbors(X)[0][:, k])


def dbscan_grid(X, eps_list, min_samples_list, sil_sample=5000, seed=42):
    rows = []
    for ms in min_samples_list:
        for eps in eps_list:
            lab = DBSCAN(eps=eps, min_samples=ms).fit_predict(X)
            core = lab >= 0
            ncl = len(set(lab[core]))
            sil = np.nan
            if ncl >= 2 and core.sum() > 50:
                idx = np.where(core)[0]
                idx = np.random.RandomState(seed).choice(idx, min(sil_sample, len(idx)), replace=False)
                sil = silhouette_score(X[idx], lab[idx])
            rows.append(dict(eps=eps, min_samples=ms, clusters=ncl, noise_pct=round(100 * (~core).mean(), 1),
                             largest_cluster_share=round(np.bincount(lab[core]).max() / len(X), 3) if ncl else 0.0, silhouette_non_noise=sil))
    return pd.DataFrame(rows)


def choose_dbscan(grid, noise_lo=1.0, noise_hi=15.0):
    """Among settings with >= 2 clusters and 1-15% noise, the best silhouette of the non-noise routes. None if nothing qualifies."""
    c = grid[(grid.clusters >= 2) & (grid.noise_pct >= noise_lo) & (grid.noise_pct <= noise_hi)].dropna(subset=["silhouette_non_noise"])
    return None if c.empty else c.loc[c.silhouette_non_noise.idxmax()]


def dbscan_assign(model, X_new):
    """DBSCAN has no predict(): a new route joins the cluster of its nearest core point if that is within eps, else it is noise (-1)."""
    nn = NearestNeighbors(n_neighbors=1).fit(model.components_)
    d, i = nn.kneighbors(X_new)
    core_labels = model.labels_[model.core_sample_indices_]
    lab = core_labels[i[:, 0]].copy()
    lab[d[:, 0] > model.eps] = -1
    return lab


# ------------------------------------------------------------------ interpretation helpers
def cluster_profile(raw, labels, cols):
    return raw.assign(cluster=labels).groupby("cluster")[cols].median().round(2).assign(routes=pd.Series(labels).value_counts().sort_index().values)


def top_features(Xdf, labels, feats, n=3):
    """For each cluster the features whose mean (in standardised units) is farthest from the overall mean of 0."""
    z = Xdf[feats].groupby(labels).mean()
    return {c: [(f, round(float(z.loc[c, f]), 2)) for f in z.loc[c].abs().sort_values(ascending=False).index[:n]] for c in z.index}


# ------------------------------------------------------------------ supervised diagnostic
def class_metrics(y_true, y_pred, classes):
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=range(len(classes)), zero_division=0)
    per = pd.DataFrame({"class": classes, "precision": p, "recall": r, "f1": f, "support": s}).round(3)
    pm, rm, fm, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return dict(accuracy=accuracy_score(y_true, y_pred), precision_macro=pm, recall_macro=rm, f1_macro=fm), per, confusion_matrix(y_true, y_pred, labels=range(len(classes)))
