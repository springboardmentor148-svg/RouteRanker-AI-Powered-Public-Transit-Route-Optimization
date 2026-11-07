"""Module 5 runner: KMeans + DBSCAN clustering and a Random Forest / XGBoost supervised diagnostic.

    python run_module5.py
Reads data/processed/module4/*.csv (Module 4). Writes models/, reports/figures/module5/, reports/tables/module5_*.csv and reports/module5_*.md.
Clusters group routes by SIMILAR SCHEDULED SERVICE; they are not performance categories. No passenger/performance label is created:
the supervised task predicts the CITY of a route (a real label) as a diagnostic of how comparable the feeds are.
"""
import datetime, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import joblib
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, f1_score, silhouette_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier
from src import modeling as m, preprocessing as pp


def md_table(df, floatfmt="{:,.2f}"):
    """Markdown table; integers stay integers (rows are not up-cast to float)."""
    if df.empty:
        return "_none_\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.astype(object).iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else (floatfmt.format(v) if isinstance(v, float) else str(v)) for v in r) + " |")
    return "\n".join(out) + "\n"

FIG, TAB, REP, MOD = "reports/figures/module5", "reports/tables", "reports", "models"
PROFILE = ["n_trips", "n_unique_stops", "length_km", "service_span_h", "trips_per_active_hour", "median_headway_min", "avg_speed_kmh",
           "max_stop_overlap", "mean_routes_per_stop", "share_morning", "share_afternoon", "share_evening"]
SEED = 42
sns.set_theme(style="whitegrid")


def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{FIG}/{name}.png", dpi=110); plt.close(fig)


def main():
    for d in (FIG, TAB, MOD):
        os.makedirs(d, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    tr, va, feats = m.load_module4()
    Xtr, Xva = tr[feats].values, va[feats].values
    raw = pp.add_derived(pp.load_features())
    trr = tr[["city", "route_id"]].merge(raw, on=["city", "route_id"], how="left")
    var = va[["city", "route_id"]].merge(raw, on=["city", "route_id"], how="left")
    pca = PCA(2, random_state=SEED).fit(Xtr)
    P_tr, P_va = pca.transform(Xtr), pca.transform(Xva)

    # ===================================================================== KMEANS
    sweep = m.kmeans_sweep(Xtr, range(2, 11), SEED)
    sweep.to_csv(f"{TAB}/module5_kmeans_k_sweep.csv", index=False)
    k_elbow, k_best = m.elbow_k(sweep), m.choose_k(sweep)
    stab = {k: m.kmeans_stability(Xtr, k) for k in sorted({3, k_elbow, k_best})}
    km = KMeans(k_best, n_init=10, random_state=SEED).fit(Xtr)
    lab_tr, lab_va = km.labels_, km.predict(Xva)
    sil_tr = silhouette_score(Xtr, lab_tr, sample_size=6000, random_state=SEED)
    sil_va = silhouette_score(Xva, lab_va)
    db_tr, db_va = davies_bouldin_score(Xtr, lab_tr), davies_bouldin_score(Xva, lab_va)
    joblib.dump(km, f"{MOD}/kmeans_model.joblib")
    prof = m.cluster_profile(trr, lab_tr, PROFILE); prof.index.name = "cluster"
    prof.to_csv(f"{TAB}/module5_kmeans_cluster_profile.csv")
    topf = m.top_features(tr, lab_tr, feats, 3)
    comp = pd.crosstab(tr.city, lab_tr, normalize="columns").round(3)
    comp.to_csv(f"{TAB}/module5_kmeans_city_composition.csv")
    # figures
    f, ax = plt.subplots(1, 3, figsize=(14, 3.8))
    ax[0].plot(sweep.k, sweep.inertia, "o-"); ax[0].axvline(k_elbow, color="crimson", ls="--", label=f"elbow K={k_elbow}"); ax[0].set(title="Elbow method", xlabel="K", ylabel="within-cluster sum of squares (inertia)"); ax[0].legend()
    ax[1].plot(sweep.k, sweep.silhouette, "o-", color="#2a9d8f"); ax[1].axvline(k_best, color="crimson", ls="--", label=f"chosen K={k_best}"); ax[1].set(title="Silhouette score (higher = better separated)", xlabel="K", ylabel="silhouette"); ax[1].legend()
    ax[2].plot(sweep.k, sweep.davies_bouldin, "o-", color="#e76f51"); ax[2].set(title="Davies-Bouldin index (lower = better)", xlabel="K", ylabel="Davies-Bouldin")
    save(f, "m5_01_kmeans_k_selection")
    rs = np.random.RandomState(SEED); idx = rs.choice(len(P_tr), 5000, replace=False)
    f, ax = plt.subplots(figsize=(7, 5.5)); sc = ax.scatter(P_tr[idx, 0], P_tr[idx, 1], c=lab_tr[idx], cmap="tab10", s=8, alpha=.6)
    ax.set(title=f"KMeans clusters (K={k_best}) of training routes, projected to 2 PCA components ({pca.explained_variance_ratio_.sum():.0%} of variance)", xlabel="PCA 1", ylabel="PCA 2")
    ax.legend(*sc.legend_elements(), title="cluster", loc="best", fontsize=8); save(f, "m5_02_kmeans_pca_clusters")
    f, ax = plt.subplots(1, 2, figsize=(13, 4))
    pd.Series(lab_tr).value_counts().sort_index().plot.bar(ax=ax[0], color="#457b9d"); ax[0].set(title="Number of training routes per KMeans cluster", xlabel="cluster", ylabel="routes")
    comp.T.plot.bar(stacked=True, ax=ax[1], colormap="tab20", width=.8); ax[1].set(title="Which cities make up each cluster (share of the cluster)", xlabel="cluster", ylabel="share"); ax[1].legend(fontsize=7, ncol=2)
    save(f, "m5_03_kmeans_sizes_and_cities")
    z = tr[feats].groupby(lab_tr).mean()
    f, ax = plt.subplots(figsize=(11, 4.5)); sns.heatmap(z[[c for c in feats if not c.startswith(("length_method", "peak_period"))]], cmap="coolwarm", center=0, annot=True, fmt=".1f", annot_kws={"size": 7}, ax=ax)
    ax.set(title="KMeans cluster profile: mean of each (standardised) feature per cluster - red = above average, blue = below", xlabel="", ylabel="cluster"); plt.xticks(rotation=40, ha="right"); save(f, "m5_04_kmeans_profile_heatmap")

    # ===================================================================== DBSCAN
    ms_list, eps_list = [5, 10, 20], [0.8, 1.0, 1.3, 1.6, 2.0, 2.5, 3.0]
    grid = m.dbscan_grid(Xtr, eps_list, ms_list, seed=SEED); grid.to_csv(f"{TAB}/module5_dbscan_parameter_grid.csv", index=False)
    pick = m.choose_dbscan(grid)
    if pick is None:                                        # nothing qualified: fall back to the lowest-noise setting with >= 2 clusters
        pick = grid[grid.clusters >= 2].sort_values("noise_pct").iloc[0]
    eps, msamp = float(pick.eps), int(pick.min_samples)
    db = DBSCAN(eps=eps, min_samples=msamp).fit(Xtr)
    dl_tr, dl_va = db.labels_, m.dbscan_assign(db, Xva)
    joblib.dump(db, f"{MOD}/dbscan_model.joblib")
    n_cl = len(set(dl_tr[dl_tr >= 0])); noise_tr, noise_va = (dl_tr == -1).mean(), (dl_va == -1).mean()
    core = dl_tr >= 0
    ids_ = np.where(core)[0]; ids_ = np.random.RandomState(SEED).choice(ids_, min(5000, len(ids_)), replace=False)
    sil_db = silhouette_score(Xtr[ids_], dl_tr[ids_]) if n_cl >= 2 else np.nan
    dbi_db = davies_bouldin_score(Xtr[core], dl_tr[core]) if n_cl >= 2 else np.nan
    f, ax = plt.subplots(figsize=(6.5, 4))
    for ms in ms_list: ax.plot(m.kdistance(Xtr, ms), label=f"k = {ms}")
    ax.axhline(eps, color="crimson", ls="--", label=f"chosen eps = {eps}"); ax.set(title="DBSCAN k-distance plot (distance to the k-th nearest route)", xlabel="routes sorted by distance", ylabel="distance"); ax.legend(); save(f, "m5_05_dbscan_kdistance")
    f, ax = plt.subplots(1, 2, figsize=(12, 3.8))
    for a, col, ttl in [(ax[0], "noise_pct", "% of routes labelled noise"), (ax[1], "clusters", "number of clusters found")]:
        sns.heatmap(grid.pivot(index="min_samples", columns="eps", values=col), annot=True, fmt=".0f" if col == "clusters" else ".1f", cmap="viridis", ax=a); a.set_title(f"DBSCAN: {ttl}")
    save(f, "m5_06_dbscan_parameter_grid")
    f, ax = plt.subplots(figsize=(7, 5.5))
    ax.scatter(P_tr[idx, 0], P_tr[idx, 1], c="#adb5bd", s=6, alpha=.5, label="in a cluster")
    nz = np.where(dl_tr[idx] == -1)[0]; ax.scatter(P_tr[idx][nz, 0], P_tr[idx][nz, 1], c="crimson", s=14, label="noise (-1)")
    ax.set(title=f"DBSCAN (eps={eps}, min_samples={msamp}): noise routes in the same 2-D projection", xlabel="PCA 1", ylabel="PCA 2"); ax.legend(); save(f, "m5_07_dbscan_noise_pca")
    # noise analysis
    allr = pd.concat([trr.assign(split="train", dbscan=dl_tr, kmeans=lab_tr), var.assign(split="validation", dbscan=dl_va, kmeans=lab_va)], ignore_index=True)
    Xall = pd.concat([tr[feats], va[feats]], ignore_index=True)
    noise = allr[allr.dbscan == -1]
    noise_city = (allr.assign(noise=allr.dbscan == -1).groupby("city").noise.agg(["sum", "mean"]).rename(columns={"sum": "noise_routes", "mean": "share"}).round(3)).reset_index()
    cmp_ = pd.DataFrame({"noise routes (median)": noise[PROFILE].median(), "other routes (median)": allr[allr.dbscan != -1][PROFILE].median()}).round(2)
    nz_feats = Xall[(allr.dbscan == -1).values][[c for c in feats if not c.startswith(("length_method", "peak_period"))]].mean().sort_values(key=abs, ascending=False).head(5).round(2)
    noise[["split", "city", "route_id", "route_name", "kmeans"] + PROFILE].to_csv(f"{TAB}/module5_dbscan_noise_routes.csv", index=False)
    cmp_.to_csv(f"{TAB}/module5_dbscan_noise_vs_other.csv")
    # ===================================================================== SUPERVISED DIAGNOSTIC (label = city, a real label)
    le = LabelEncoder().fit(tr.city); classes = list(le.classes_)
    ytr, yva = le.transform(tr.city), le.transform(va.city)
    groups = (tr.city + "|" + tr.route_name).values
    variants = {"all features": feats, "without length_method flags": [c for c in feats if not c.startswith("length_method")]}
    cv = list(GroupKFold(3).split(Xtr, ytr, groups))
    rf_grid = [dict(n_estimators=200, max_depth=d, min_samples_leaf=2) for d in (8, 16, None)]
    xgb_grid = [dict(n_estimators=200, max_depth=4, learning_rate=.1), dict(n_estimators=200, max_depth=6, learning_rate=.1), dict(n_estimators=400, max_depth=6, learning_rate=.05)]

    def make(kind, p): return RandomForestClassifier(class_weight="balanced_subsample", random_state=SEED, n_jobs=-1, **p) if kind == "RF" else XGBClassifier(random_state=SEED, n_jobs=-1, eval_metric="mlogloss", **p)

    def fit(model, X, y):
        model.fit(X, y, **({"sample_weight": compute_sample_weight("balanced", y)} if isinstance(model, XGBClassifier) else {})); return model
    results, per_tables, cms, imps, tuning, fitted = [], {}, {}, {}, [], {}
    base_acc = np.bincount(yva).max() / len(yva)
    for vname, cols in variants.items():
        ix = [feats.index(c) for c in cols]
        for kind, grid_ in (("RF", rf_grid), ("XGB", xgb_grid)):
            best, bs = None, -1
            for p in grid_:
                s = np.mean([f1_score(ytr[b], fit(make(kind, p), Xtr[a][:, ix], ytr[a]).predict(Xtr[b][:, ix]), average="macro") for a, b in cv])
                tuning.append(dict(variant=vname, model=kind, params=str(p), cv_macro_f1=round(s, 3)))
                if s > bs: best, bs = p, s
            mod = fit(make(kind, best), Xtr[:, ix], ytr)
            mt, per, cmx = m.class_metrics(yva, mod.predict(Xva[:, ix]), classes)
            results.append(dict(variant=vname, model={"RF": "Random Forest", "XGB": "XGBoost"}[kind], best_params=str(best), cv_macro_f1=round(bs, 3), **{k: round(v, 3) for k, v in mt.items()}))
            per_tables[(vname, kind)], cms[(vname, kind)] = per, cmx
            imps[(vname, kind)] = pd.Series(mod.feature_importances_, index=cols).sort_values(ascending=False)
            fitted[(vname, kind)] = mod
    res = pd.DataFrame(results); res.to_csv(f"{TAB}/module5_classification_results.csv", index=False)
    pd.DataFrame(tuning).to_csv(f"{TAB}/module5_classification_tuning.csv", index=False)
    for (v, k), p in per_tables.items(): p.to_csv(f"{TAB}/module5_classification_per_class_{'all' if v == 'all features' else 'no_length_method'}_{k}.csv", index=False)
    joblib.dump(fitted[("all features", "RF")], f"{MOD}/random_forest_city_diagnostic.joblib", compress=3)
    joblib.dump(fitted[("all features", "XGB")], f"{MOD}/xgboost_city_diagnostic.joblib", compress=3)
    f, ax = plt.subplots(2, 2, figsize=(12, 10))
    for a, ((v, k), cmx) in zip(ax.ravel(), cms.items()):
        sns.heatmap(cmx, annot=True, fmt="d", cmap="Blues", xticklabels=classes, yticklabels=classes, ax=a, cbar=False)
        a.set(title=f"{'Random Forest' if k == 'RF' else 'XGBoost'} - {v}", xlabel="predicted city", ylabel="actual city")
    save(f, "m5_08_confusion_matrices")
    f, ax = plt.subplots(1, 2, figsize=(13, 5.5))
    for a, k in zip(ax, ("RF", "XGB")):
        imps[("all features", k)].head(12).iloc[::-1].plot.barh(ax=a, color="#457b9d"); a.set_title(f"{'Random Forest' if k == 'RF' else 'XGBoost'}: most used features (all features)"); a.set_xlabel("importance")
    save(f, "m5_09_feature_importance")

    # ===================================================================== REPORTS
    def desc_cluster(c):
        r = prof.loc[c]
        tf = ", ".join(f"{n} ({'+' if v > 0 else ''}{v})" for n, v in topf[c])
        return dict(cluster=c, routes=int(r.routes), share_of_train=f"{100 * r.routes / len(tr):.1f}%", median_trips=r.n_trips, median_stops=r.n_unique_stops, median_length_km=r.length_km,
                    median_span_h=r.service_span_h, most_distinctive_features_z=tf)
    cl_tbl = pd.DataFrame([desc_cluster(c) for c in prof.index])
    sw = sweep.round(3)
    cr = [f"# Module 5 - Clustering report (KMeans and DBSCAN)\n\n_Generated {stamp}._ Data: Module-4 preprocessed routes ({len(tr):,} training, {len(va):,} validation; {len(feats)} standardised features; Hyderabad excluded in Module 4). "
          "**A cluster is a group of routes with similar *scheduled* service - not a performance class and not an optimisation recommendation.** GTFS has no passenger data, so nothing here says that a route is overcrowded or underutilised.\n",
          "## How the algorithms work (short)\n",
          "* **KMeans:** choose K; place K centroids; assign each route to its nearest centroid; move each centroid to the mean of its routes; repeat until assignments stop changing. Needs scaled features (done in Module 4) because it uses Euclidean distance.",
          "* **DBSCAN:** a route is a *core point* if at least `min_samples` routes lie within distance `eps`; clusters grow by connecting core points and their neighbours; routes that belong to no dense region are *noise* (-1). No K is needed.\n",
          "## KMeans\n", f"### Choosing K (training routes, K = 2..10)\n", md_table(sw),
          f"\n![k selection](figures/module5/m5_01_kmeans_k_selection.png)\n",
          f"* **Elbow method:** the inertia curve bends most at K = {k_elbow}.",
          f"* **Silhouette:** the values are low for every K ({sweep.silhouette.min():.2f}-{sweep.silhouette.max():.2f}); the highest is K = {int(sweep.loc[sweep.silhouette.idxmax(), 'k'])}. Low scores mean the routes form a continuum rather than clearly separated groups.",
          f"* **Davies-Bouldin:** lowest (best) at K = {int(sweep.loc[sweep.davies_bouldin.idxmin(), 'k'])} ({sweep.davies_bouldin.min():.2f}).",
          f"* **Decision:** K = **{k_best}** (best silhouette for K in 3-8 with no cluster smaller than 2% of the routes). The elbow K = {k_elbow} and K = 3 (the mentor's example) give similar quality, so the choice is a convenience for interpretation, not a sharp optimum.",
          "* **Stability** (adjusted Rand index between runs with different random starts, 1 = identical): " + ", ".join(f"K={k}: {np.mean(v):.2f}" for k, v in stab.items()) + ".\n",
          f"### Final KMeans (K = {k_best})\n",
          f"Silhouette: training {sil_tr:.3f}, validation {sil_va:.3f}. Davies-Bouldin: training {db_tr:.2f}, validation {db_va:.2f}. Validation routes are assigned to the nearest training centroid, so a similar validation score means the clusters generalise to routes they were not built on.\n",
          "![pca](figures/module5/m5_02_kmeans_pca_clusters.png)\n",
          "*Each dot is a route; the 25 features are projected to 2 dimensions only for drawing, so clusters that overlap in the picture can still differ in other features.*\n",
          "### What each cluster looks like (medians in original units)\n", md_table(prof.reset_index()),
          "\nMost distinctive features of each cluster (mean standardised value; + = above the overall average):\n", md_table(cl_tbl[["cluster", "routes", "share_of_train", "most_distinctive_features_z"]]),
          "\n![profile](figures/module5/m5_04_kmeans_profile_heatmap.png)\n", "![sizes](figures/module5/m5_03_kmeans_sizes_and_cities.png)\n",
          "*Cluster composition by city shows whether a cluster is a real service pattern or mostly one feed: " + "; ".join(f"cluster {c}: {comp[c].idxmax()} {100 * comp[c].max():.0f}%" for c in comp.columns) + ".*\n",
          "## DBSCAN\n", f"### Parameter experiments (eps x min_samples)\n", md_table(grid.round(3)),
          "\n![grid](figures/module5/m5_06_dbscan_parameter_grid.png)\n", "![kdist](figures/module5/m5_05_dbscan_kdistance.png)\n",
          "*Small eps labels most routes as noise (many tiny clusters); large eps merges nearly everything into one cluster. The k-distance plot shows the distance scale of the data: the 'knee' marks where routes stop having close neighbours.*\n",
          f"**Decision:** eps = **{eps}**, min_samples = **{msamp}** (best silhouette of the non-noise routes among settings with at least 2 clusters and 1-15% noise).\n",
          f"### Final DBSCAN\n", f"* Clusters found: **{n_cl}**; the largest holds {100 * np.bincount(dl_tr[core]).max() / len(tr):.0f}% of the training routes.",
          f"* Noise: **{100 * noise_tr:.1f}%** of training routes and **{100 * noise_va:.1f}%** of validation routes (validation routes are noise when no training core point is within eps).",
          f"* Silhouette of the non-noise routes: {sil_db:.3f}; Davies-Bouldin: {dbi_db:.2f}." if n_cl >= 2 else "* Fewer than 2 clusters: silhouette not defined.",
          "* **Reading:** with these features DBSCAN finds one large dense region plus a few small groups, so it is not a good *segmentation* tool here; its value is **finding unusual routes**.\n",
          "### Noise-point analysis (noise is not an error)\n", md_table(noise_city), "\nMedian features of noise routes versus all other routes:\n", md_table(cmp_.reset_index().rename(columns={"index": "feature"})),
          "\nFeatures that push routes out of the dense region (mean standardised value of noise routes): " + ", ".join(f"{k} ({v:+.1f})" for k, v in nz_feats.items()) + ".\n",
          "![noise](figures/module5/m5_07_dbscan_noise_pca.png)\n",
          f"All {len(noise):,} noise routes (training and validation) are listed in `tables/module5_dbscan_noise_routes.csv`. Before calling any of them wrong, check whether it is (a) a data problem (e.g. invalid speed - {int((noise.avg_speed_kmh.isna()).sum())} noise routes have no valid scheduled speed), (b) a special service (very long or very many stops) or (c) just a rare combination of normal values.\n"]
    open(f"{REP}/module5_clustering_report.md", "w", encoding="utf-8").write("\n".join(cr))

    r_all = res[res.variant == "all features"]; r_no = res[res.variant != "all features"]
    pc = per_tables[("all features", "XGB")]
    cls = [f"# Module 5 - Classification report (Random Forest and XGBoost)\n\n_Generated {stamp}._\n",
           "## Why the target is the city, and why not a performance label\n",
           "Classification needs labels. GTFS contains no passenger data, so any label like 'overcrowded', 'underutilised' or 'high demand' would be an assumption, and the mentor's rules forbid unsupported labels. **No such label was created.** "
           "The only real, observed label in the data is the **city** a route belongs to. Predicting it is a *diagnostic*: if routes of different cities can easily be told apart from their scheduled-service features alone, the feeds have their own 'signature' (different data sources, conventions or generated timetables) and are **not directly comparable**. This says nothing about route performance.\n",
           "## Setup\n",
           f"* Training: {len(tr):,} routes; validation: {len(va):,} routes (the grouped 80:20 split of Module 4, so variants of one bus line never sit on both sides). Classes: {', '.join(classes)}.",
           "* Features: the 25 Module-4 features (no identifiers, city is only the target). Because `length_method` mostly records whether a feed has shapes.txt (a property of the feed), a second run **without** the length_method columns is reported too.",
           "* Imbalance (Bengaluru is the largest class, Pune the smallest): class weights (Random Forest) and balanced sample weights (XGBoost); the main score is **macro F1**, which treats every city equally.",
           "* Tuning: small grids evaluated with 3-fold grouped cross-validation on the training routes only; the validation set was used once, for the final numbers (no leakage).",
           f"* Baseline: always predicting the largest city gives accuracy {base_acc:.3f} and macro F1 near 0.\n",
           "## Results on the validation routes\n", md_table(res),
           "\nBest parameters were chosen by cross-validated macro F1 (see `tables/module5_classification_tuning.csv`).\n",
           "### Per-city precision, recall and F1 (XGBoost, all features)\n", md_table(pc),
           "\n![cm](figures/module5/m5_08_confusion_matrices.png)\n",
           "*Rows = actual city, columns = predicted city. Numbers off the diagonal are routes the model confused; they show which feeds look alike.*\n",
           "![imp](figures/module5/m5_09_feature_importance.png)\n",
           "*Feature importance shows which features the trees used most to separate the cities.*\n",
           "## Reading the results\n",
           f"* With all features, Random Forest reaches accuracy {r_all[r_all.model == 'Random Forest'].accuracy.iloc[0]:.2f} (macro F1 {r_all[r_all.model == 'Random Forest'].f1_macro.iloc[0]:.2f}) and XGBoost {r_all[r_all.model == 'XGBoost'].accuracy.iloc[0]:.2f} (macro F1 {r_all[r_all.model == 'XGBoost'].f1_macro.iloc[0]:.2f}), far above the majority baseline of {base_acc:.2f}.",
           f"* Without the length_method flags, accuracy is {r_no[r_no.model == 'Random Forest'].accuracy.iloc[0]:.2f} (Random Forest) and {r_no[r_no.model == 'XGBoost'].accuracy.iloc[0]:.2f} (XGBoost), so the cities are distinguishable even from the service features alone, i.e. **the feeds carry their own fingerprint**.",
           "* Consequence for the project: pooling all cities in one clustering is only partly meaningful; clusters should be checked per city (the cluster composition chart in the clustering report) and conclusions should not compare raw trip counts across cities.",
           "* A high score here is *not* a sign of a good route model. It is a sign that the cities differ in how their schedules are written.\n",
           "## Limitations\n",
           "* The target is not a transport-planning quantity; the models are not usable to judge routes.", "* Small classes (Pune, Kochi) have few validation routes, so their per-city scores vary a lot.", "* Feature importance of trees shows use, not cause."]
    open(f"{REP}/module5_classification_report.md", "w", encoding="utf-8").write("\n".join(cls))

    big = prof.sort_values("routes", ascending=False)
    sparse = prof[prof.n_trips <= 2]; overl = prof[prof.max_stop_overlap >= prof.max_stop_overlap.quantile(.75)]
    sug = [f"# Module 5 - Algorithm comparison, observations and possible planning use\n\n_Generated {stamp}._\n",
           "## Comparison\n", md_table(pd.DataFrame([
               ["KMeans", "unsupervised", f"{k_best} clusters", "0% (every route assigned)", f"{sil_tr:.2f} / {sil_va:.2f}", f"{db_tr:.2f} / {db_va:.2f}", "Gives a complete grouping of routes by scheduled-service pattern; needs K; clusters are weakly separated"],
               ["DBSCAN", "unsupervised", f"{n_cl} clusters", f"{100 * noise_tr:.1f}% noise (train), {100 * noise_va:.1f}% (validation)", f"{sil_db:.2f} (non-noise)", f"{dbi_db:.2f} (non-noise)", "Finds unusual routes; one dominant dense region, so weak as a segmentation"],
               ], columns=["algorithm", "type", "result", "noise", "silhouette (train / validation)", "Davies-Bouldin (train / validation)", "role in this project"])),
           "\n*DBSCAN's silhouette is computed on the non-noise routes only and nearly all of them sit in one large cluster, so its higher value is **not** evidence that DBSCAN groups routes better than KMeans.*\n",
           "\n" + md_table(res[["variant", "model", "accuracy", "precision_macro", "recall_macro", "f1_macro"]]),
           "\n*Clustering and classification cannot be compared with each other: clustering has no ground truth (internal measures only), classification was run on a different, real label (the city).* Random Forest and XGBoost: see the classification report; both separate the cities well, with XGBoost "
           + ("slightly better" if res[res.variant == "all features"].set_index("model").f1_macro.get("XGBoost", 0) >= res[res.variant == "all features"].set_index("model").f1_macro.get("Random Forest", 0) else "slightly worse") + " on macro F1 with all features.\n",
           "## Main observations\n",
           f"1. The training routes do **not** form clearly separated groups (silhouette {sweep.silhouette.min():.2f}-{sweep.silhouette.max():.2f} for every K); scheduled service varies along a continuum, so any K is a convenient partition rather than a natural one.",
           f"2. The largest KMeans clusters hold {', '.join(f'{int(r.routes):,} routes (cluster {c})' for c, r in big.head(3).iterrows())}.",
           f"3. DBSCAN marks about {100 * noise_tr:.0f}% of routes as noise; these unusual routes are the most useful DBSCAN output.",
           "4. The cities can be told apart from schedule features alone (classification diagnostic), so clusters partly reflect how each feed is written.",
           "5. No cluster, noise flag or classifier output says anything about passengers, crowding or efficiency.\n",
           "## Possible uses for route planning (candidates to investigate, not recommendations)\n",
           "A cluster is not an optimisation recommendation. The groups below tell planners **where to look first**; ridership data and operator knowledge are needed before any change.\n",
           f"* **Review the noise routes first** ({len(noise):,} routes, `tables/module5_dbscan_noise_routes.csv`): check whether each is a data problem, a special service or a genuinely unusual route.",
           ("* **Very sparse service groups:** KMeans clusters " + ", ".join(str(c) for c in sparse.index) + f" have a median of at most 2 scheduled trips ({int(sparse.routes.sum()):,} routes). With ridership data, planners could check whether these are variants that could be consolidated with a main route or are intentional limited services.") if len(sparse) else "* No KMeans cluster is made of very sparse routes.",
           ("* **High shared-stop groups:** clusters " + ", ".join(str(c) for c in overl.index) + " have the highest stop overlap with other routes; corridors served by many similar routes are candidates for timetable coordination studies - again only after checking passenger flows.") if len(overl) else "",
           "* **Compare within, not across, feeds:** use clusters per city, because the feeds are not directly comparable.\n",
           "## Limitations\n",
           "* Scheduled data only; no ridership, occupancy, capacity or delay data.", "* Several feeds are community-made or old; Hyderabad was excluded in Module 4 and Delhi/Kochi/Pune show near-constant scheduled speeds.",
           "* Weak cluster separation: results depend on K, eps and min_samples and should be read as exploratory.", "* DBSCAN has no native predict function; validation routes were assigned by their nearest core point within eps.",
           "* The supervised task uses the city as target and does not measure route quality.\n",
           "## Next module\nTurn the model outputs into route-planning suggestions and integrate the pipeline, once the mentor confirms what real ridership or performance data (if any) can be used."]
    open(f"{REP}/module5_comparison_and_suggestions.md", "w", encoding="utf-8").write("\n".join(sug))
    print(f"done | KMeans K={k_best} sil {sil_tr:.3f}/{sil_va:.3f} | DBSCAN eps={eps} ms={msamp} clusters={n_cl} noise {100*noise_tr:.1f}%/{100*noise_va:.1f}% | "
          + " | ".join(f"{r.model} ({r.variant}) acc {r.accuracy} f1 {r.f1_macro}" for r in res.itertuples()))


if __name__ == "__main__":
    main()
