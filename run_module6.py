"""Module 6 runner: inference with the saved Module-5 models, investigation candidates, optimisation suggestions and a simulated network.

    python run_module6.py                         # all routes of data/processed/all_cities_route_features.csv
    python run_module6.py --input new_routes.csv  # any table with the Module-2 route_features columns (e.g. a new city from run_module2.py)
Original data is never changed: simulated results go to data/simulated/. Everything describes SCHEDULED service; suggestions are candidates to verify.
"""
import datetime, os, shutil, sys
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA
from src import inference as inf, optimization as opt, preprocessing as pp

FIG, TAB, REP = "reports/figures/module6", "reports/tables", "reports"
ROLE_TR, ROLE_VA, ROLE_NEW = "train (seen by the models)", "validation (unseen routes)", "unseen feed (not in Module-4 training set)"
sns.set_theme(style="whitegrid")


def md_table(df, floatfmt="{:,.2f}"):
    if df.empty:
        return "_none_\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.astype(object).iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else (("{:,.0f}".format(v) if float(v).is_integer() else floatfmt.format(v)) if isinstance(v, float) else str(v)) for v in r) + " |")
    return "\n".join(out) + "\n"


def save(fig, name):
    fig.tight_layout(); fig.savefig(f"{FIG}/{name}.png", dpi=110); plt.close(fig)


def main(input_path=None):
    for d in (FIG, TAB, "data/inference", "data/simulated", "models"):
        os.makedirs(d, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    raw = pp.load_features(input_path) if input_path else pp.load_features()
    key = lambda d: d.city + "|" + d.route_id
    d4 = "data/processed/module4"
    tr_ids = set(key(pd.read_csv(f"{d4}/train_preprocessed.csv", usecols=["city", "route_id"], dtype=str)))
    va = pd.read_csv(f"{d4}/validation_preprocessed.csv", dtype={"route_id": str, "route_name": str})
    va_ids = set(key(va))
    raw["data_role"] = np.where(key(raw).isin(tr_ids), ROLE_TR, np.where(key(raw).isin(va_ids), ROLE_VA, ROLE_NEW))
    unseen = raw[raw.data_role != ROLE_TR]
    unseen.to_csv("data/inference/unseen_routes.csv", index=False)
    shutil.copy(f"{d4}/preprocessor.joblib", "models/preprocessor.joblib")

    # ---------------- 1. inference with the SAVED models and the SAVED preprocessor
    models = inf.load_models()
    prof = pd.read_csv(f"{TAB}/module5_kmeans_cluster_profile.csv", index_col=0)
    names = inf.name_clusters(prof)
    vv = raw[raw.data_role == ROLE_VA].merge(va[["city", "route_id"]], on=["city", "route_id"])
    max_diff = 0.0
    if len(vv):        # consistency: the saved preprocessor must reproduce the stored Module-4 validation table
        _, Xchk = inf.prepare_new(vv, models["prep"])
        saved = va.set_index(["city", "route_id"]).loc[list(zip(vv.city, vv.route_id)), Xchk.columns]
        max_diff = float(np.abs(Xchk.values - saved.values).max())
        assert max_diff < 1e-9, "saved preprocessor does not reproduce the Module-4 validation table"
    d, X, out = inf.run_inference(raw, models, names)
    out["data_role"] = raw.data_role.values
    out.to_csv("data/inference/inference_predictions.csv", index=False)
    by_role = out.groupby("data_role").agg(routes=("route_id", "size"), dbscan_noise_pct=("dbscan_label", lambda s: round(100 * (s == -1).mean(), 1)),
                                           mean_distance_to_centroid=("dist_to_centroid", "mean"), mean_closest_feed_probability=("closest_feed_probability", "mean")).round(2)
    by_role.to_csv(f"{TAB}/module6_inference_summary_by_role.csv")
    new_feed = out[out.data_role == ROLE_NEW]
    gv = lambda role, col: by_role.loc[role, col] if role in by_role.index else "n/a"
    # figures
    f, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    mix = pd.crosstab(out.data_role, out.kmeans_cluster, normalize="index")
    mix.plot.bar(stacked=True, ax=ax[0], colormap="tab10", width=.7); ax[0].set(title="Share of routes per KMeans cluster", ylabel="share", xlabel=""); ax[0].legend(title="cluster", fontsize=7); ax[0].tick_params(axis="x", rotation=15, labelsize=7)
    by_role.dbscan_noise_pct.plot.bar(ax=ax[1], color="crimson"); ax[1].set(title="Share labelled noise by DBSCAN (%)", ylabel="%", xlabel=""); ax[1].tick_params(axis="x", rotation=15, labelsize=7)
    by_role.mean_distance_to_centroid.plot.bar(ax=ax[2], color="#457b9d"); ax[2].set(title="Mean distance to the nearest KMeans centroid", ylabel="standardised units", xlabel=""); ax[2].tick_params(axis="x", rotation=15, labelsize=7)
    save(f, "m6_01_inference_by_data_role")
    pca = PCA(2, random_state=0).fit(X.loc[(raw.data_role == ROLE_TR).values].values); P = pca.transform(X.values)
    rs = np.random.RandomState(0); f, ax = plt.subplots(figsize=(7.5, 5.5))
    for role, col, sz in [(ROLE_TR, "#ced4da", 5), (ROLE_VA, "#2a9d8f", 9), (ROLE_NEW, "crimson", 9)]:
        idx = np.where(raw.data_role.values == role)[0]; idx = rs.choice(idx, min(2500, len(idx)), replace=False)
        ax.scatter(P[idx, 0], P[idx, 1], s=sz, alpha=.6, c=col, label=role)
    ax.set(title="Where unseen routes fall relative to the training routes (2-D PCA of the 25 features)", xlabel="PCA 1", ylabel="PCA 2"); ax.legend(fontsize=7); save(f, "m6_02_pca_unseen_routes")

    # ---------------- 2. investigation candidates (comparable feeds only, multi-evidence)
    dd = pd.concat([d.reset_index(drop=True), out[["kmeans_cluster", "kmeans_cluster_description", "dbscan_label", "closest_known_feed"]].reset_index(drop=True)], axis=1)
    excl = pp.EXCLUDE_FEEDS
    comp = dd[~dd.city.isin(excl)].reset_index(drop=True)
    sparse = list(prof.index[prof.n_trips <= 2])
    ev, flags = opt.evidence_flags(comp, sparse)
    label = {"ev_dbscan_noise": "unusual for DBSCAN (noise)", "ev_sparse_cluster": "in a KMeans cluster of very few trips", "ev_high_stop_overlap": f"shares >= {int(opt.MERGE_JACCARD * 100)}% of its stops with another route",
             "ev_low_trips_for_length": "few trips compared with routes of similar length"}
    ev["why_listed"] = ev[flags].apply(lambda r: "; ".join(label[f] for f in flags if r[f]), axis=1)
    cand = ev[ev.n_evidence >= 2].sort_values(["n_evidence", "city"], ascending=[False, True])
    cols = ["city", "route_id", "route_name", "n_evidence", "why_listed", "kmeans_cluster", "n_trips", "n_unique_stops", "length_km", "max_stop_overlap", "data_check_first"]
    cand[cols].to_csv(f"{TAB}/module6_investigation_candidates.csv", index=False)
    ev_city = pd.crosstab(ev.city, ev.n_evidence)
    f, ax = plt.subplots(figsize=(8, 4.2)); (ev_city.div(ev_city.sum(axis=1), axis=0)).plot.bar(stacked=True, ax=ax, colormap="YlOrRd", width=.75)
    ax.set(title="Share of routes by number of independent evidence flags (0-4)", ylabel="share of routes", xlabel=""); ax.legend(title="flags", fontsize=8); save(f, "m6_03_evidence_flags_by_city")

    # ---------------- 3. suggestions
    mg = opt.merge_candidates(ev); sp = opt.split_candidates(ev); fq = opt.frequency_candidates(ev)
    mg["reason"] = mg.apply(lambda r: f"stop sets {r.stop_overlap_jaccard:.0%} similar; '{r.absorbed_route}' has {r.trips_absorbed} scheduled trips vs {r.trips_target} on '{r.target_route}'; lengths {r.length_absorbed_km:.0f} vs {r.length_target_km:.0f} km", axis=1)
    mg["must_verify_first"] = "passenger demand on both routes, vehicle capacity, travel time, coverage of the unshared stops, whether the routes serve different purposes"
    sp["reason"] = sp.apply(lambda r: f"long ({r.length_km:.0f} km, {r.length_method}) and complex ({r.stops} stops) route", axis=1)
    sp["must_verify_first"] = "passenger journey lengths, transfer point and burden, travel time, connectivity between the two parts"
    fq["reason"] = fq.apply(lambda r: f"only {r.departures_in_peak_hour} departure in its busiest hour ({r.peak_hour}:00) although it has {r.trips} scheduled trips", axis=1)
    fq["must_verify_first"] = "reliable demand evidence for the period, fleet availability; reductions are NOT suggested (no demand data)"
    mg.to_csv(f"{TAB}/module6_merge_suggestions.csv", index=False); sp.to_csv(f"{TAB}/module6_split_suggestions.csv", index=False); fq.to_csv(f"{TAB}/module6_frequency_suggestions.csv", index=False)
    f, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    ax[0].scatter(mg.trips_target, mg.trips_absorbed, c=mg.stop_overlap_jaccard, cmap="viridis", s=14, alpha=.7); ax[0].set(xscale="log", title="Merge candidates: trips of the target route vs the route to be merged into it", xlabel="scheduled trips of the target route", ylabel="scheduled trips of the absorbed route")
    ax[1].scatter(sp.length_km, sp.stops, c=pd.factorize(sp.city)[0], cmap="tab10", s=14, alpha=.7); ax[1].set(title="Split candidates: length vs stops (colour = city)", xlabel="estimated length (km)", ylabel="distinct stops")
    save(f, "m6_04_merge_split_candidates")

    # ---------------- 4. simulation on copies
    cur = ev[opt.SIMCOLS + ["status"] if "status" in ev else opt.SIMCOLS].copy()
    scen = {"current network": cur, "merge only": opt.simulate(ev, mg, sp, fq, "merge"), "split only": opt.simulate(ev, mg, sp, fq, "split"),
            "frequency standard only": opt.simulate(ev, mg, sp, fq, "frequency"), "combined": opt.simulate(ev, mg, sp, fq, "combined")}
    comb = scen["combined"]
    comb.to_csv("data/simulated/simulated_network.csv", index=False)
    cur_out = ev[["city", "route_id", "route_name", "n_trips", "n_unique_stops", "length_km", "peak_hour_trips"]]
    rows = []
    for sname, df in scen.items():
        for city, g in list(df.groupby("city")) + [("ALL CITIES", df)]:
            rows.append(dict(scenario=sname, city=city, **opt.metrics(g)))
    met = pd.DataFrame(rows)
    # 'busiest hour' is only well defined for the current network and the frequency scenario (merging / splitting change what it means)
    met.loc[~met.scenario.isin(["current network", "frequency standard only"]), "routes_with_under_2_departures_in_peak_hour"] = np.nan
    met.to_csv(f"{TAB}/module6_current_vs_simulated_metrics.csv", index=False)
    tot = met[met.city == "ALL CITIES"].set_index("scenario").drop(columns="city").astype(float)
    base = tot.loc["current network"]
    pcols = ["routes", "scheduled_trips", "est_route_distance_km", "avg_route_length_km", "scheduled_trip_km", "avg_trips_per_route"]
    pct = (tot[pcols].div(base[pcols]) - 1) * 100
    f, ax = plt.subplots(figsize=(10, 3.8)); sns.heatmap(pct.drop(index="current network"), annot=True, fmt=".1f", cmap="coolwarm", center=0, ax=ax)
    ax.set(title="Simulated change versus the current network, all cities (%) - a change is not automatically an improvement", ylabel=""); plt.xticks(rotation=20, ha="right"); save(f, "m6_05_current_vs_simulated_total")
    c_city = met[met.scenario.isin(["current network", "combined"]) & (met.city != "ALL CITIES")].pivot(index="city", columns="scenario", values="routes")
    f, ax = plt.subplots(1, 2, figsize=(12, 4))
    c_city.plot.bar(ax=ax[0], color=["#2a9d8f", "#adb5bd"]); ax[0].set(title="Number of routes: current vs combined simulation", ylabel="routes", xlabel="")
    d_city = met[met.scenario.isin(["current network", "combined"]) & (met.city != "ALL CITIES")].pivot(index="city", columns="scenario", values="est_route_distance_km")
    d_city.plot.bar(ax=ax[1], color=["#2a9d8f", "#adb5bd"]); ax[1].set(title="Estimated total route distance (km)", ylabel="km", xlabel=""); save(f, "m6_06_current_vs_simulated_by_city")

    # ---------------- 5. reports
    legend = md_table(pd.DataFrame([
        ["Actual data", "route_features.csv values (trips, stops, headway ...), taken from the GTFS schedule", "scheduled; not passenger data"],
        ["Model predictions", "KMeans cluster, DBSCAN label (cluster / noise), closest known feed (XGBoost)", "outputs of models trained in Module 5; not facts"],
        ["Estimates", "route length from stops or shapes, evidence flags, 'unshared length' after a merge", "derived with stated rules"],
        ["Simulated results", "everything in data/simulated/ and in the current-vs-simulated tables", "what-if scenarios under stated assumptions"]],
        columns=["kind", "examples", "status"]))
    inr = [f"# Module 6 - Inference report\n\n_Generated {stamp}._ Inference = applying the **already trained** Module-5 models to routes, with the **same preprocessing objects** that were fitted in Module 4 (nothing is re-fitted).\n",
           "## What is what\n", legend,
           "\n## Workflow\n", "1. Load the saved models (`models/`) and preprocessing objects (`models/preprocessor.joblib`).", "2. Take new / unseen route records (`data/inference/unseen_routes.csv`; any table with the Module-2 route feature columns works: `python run_module6.py --input <file>`); the columns are checked.",
           "3. Apply the fitted preprocessor (derived columns, median imputation, log, standardisation, one-hot) - **no new scaler or encoder is fitted**.", "4. KMeans: nearest centroid. DBSCAN: nearest core point within eps, otherwise noise (-1). XGBoost: closest known feed.", "5. Analyse the outputs (below) and generate suggestions (next report).\n",
           f"**Consistency check:** the saved preprocessor re-applied to the {len(vv):,} validation routes reproduces the stored Module-4 validation table (largest difference {max_diff:.1e}), so inference uses exactly the training-time preprocessing.\n",
           "## Unseen data used\n", f"* **Validation routes ({(raw.data_role == ROLE_VA).sum():,})** were held out in Module 4 and never used to fit the models.", f"* **An unseen feed:** Hyderabad ({(raw.data_role == ROLE_NEW).sum():,} routes) was excluded from the Module-4 training set because its trips look like whole vehicle duties.", "* The training routes are scored too, only as a reference (they were seen by the models).\n",
           "## Results by data role\n", md_table(by_role.reset_index()),
           "\n![roles](figures/module6/m6_01_inference_by_data_role.png)\n", "![pca](figures/module6/m6_02_pca_unseen_routes.png)\n",
           f"* **Validation routes behave like the training routes:** the same share is noise ({gv(ROLE_VA, 'dbscan_noise_pct')}% vs {gv(ROLE_TR, 'dbscan_noise_pct')}%) and the distance to the nearest centroid is almost identical, so the models generalise to routes they did not see.",
           f"* **The unseen feed does not fit:** {gv(ROLE_NEW, 'dbscan_noise_pct')}% of Hyderabad routes are DBSCAN noise (training: {gv(ROLE_TR, 'dbscan_noise_pct')}%) and their mean distance to a centroid is {gv(ROLE_NEW, 'mean_distance_to_centroid')} (training: {gv(ROLE_TR, 'mean_distance_to_centroid')}). This supports the Module-3/4 finding that this feed is **not comparable** with the others; it is **not** evidence that its routes are inefficient or wrong. Its routes are therefore **not used for suggestions**.",
           f"* XGBoost's 'closest known feed' for Hyderabad is {', '.join(f'{k} ({v})' for k, v in new_feed.closest_known_feed.value_counts().items())}; the label only says which known feed's schedule features they resemble most.\n",
           "## What the KMeans clusters mean (scheduled service only)\n", md_table(pd.DataFrame({"cluster": list(names), "description (from the Module-5 median profile)": list(names.values())})),
           "\nCluster numbers are not rankings. Clusters 1, 3, 4 and 6 are groups of routes with very few scheduled trips; that is a description of the timetable, not a verdict.\n",
           "## Files\n", "* `data/inference/unseen_routes.csv` - the unseen route records.", "* `data/inference/inference_predictions.csv` - one row per route: KMeans cluster and description, distance to centroid, DBSCAN label and distance to nearest core point, closest known feed and probability.\n"]
    open(f"{REP}/module6_inference_report.md", "w", encoding="utf-8").write("\n".join(inr))

    strong = cand[cand.n_evidence >= 3]
    inv = [f"# Module 6 - Routes to investigate and optimisation suggestions\n\n_Generated {stamp}._ **Candidates, not conclusions.** No passenger demand, capacity or crowding data exists in GTFS, so no route is called inefficient. "
           "Suggestions come from schedule and geography (shared stops) only and each lists what must be verified first.\n",
           "## 1. Routes that may need further investigation\n",
           f"A route is listed only when **at least two independent pieces of evidence** agree (never one feature or one cluster alone). Evidence: {', '.join(label.values())}. "
           f"Routes of the unseen feed ({', '.join(excl)}) are excluded because the feed is not comparable.\n",
           md_table(ev_city.reset_index().rename(columns={"index": "city"})), "\n![flags](figures/module6/m6_03_evidence_flags_by_city.png)\n",
           f"* **{len(cand):,} routes** have at least 2 flags and **{len(strong):,}** have 3 or 4 (`tables/module6_investigation_candidates.csv`, with the reasons for each). These are where a planner should look first - together with ridership data.",
           f"* **{int(ev.data_check_first.sum()):,} routes** have an impossible scheduled speed (length or timetable unreliable): check the **data** before anything else.\n",
           "Examples with the most evidence:\n", md_table(strong.head(8)[["city", "route_name", "n_evidence", "why_listed", "n_trips", "n_unique_stops", "length_km"]]),
           "\n## 2. Route merging\n",
           f"**Rule:** route r is a merge candidate into its best partner p when (a) they have **different line names** and are not opposite directions, (b) their **stop sets are >= {int(opt.MERGE_JACCARD * 100)}% similar** (shared stops = geographical connectivity), (c) r is **lightly scheduled** (<= {int(opt.MERGE_LOW_Q * 100)}th percentile of its city) and (d) their lengths differ by at most {opt.MERGE_LEN_RATIO}x. Each route is used in at most one merge.\n",
           f"**{len(mg):,} candidate merges** (`tables/module6_merge_suggestions.csv`): " + ", ".join(f"{c} {n}" for c, n in mg.groupby('city').size().items()) + ". Examples:\n", md_table(mg.head(6)[["city", "absorbed_route", "target_route", "stop_overlap_jaccard", "trips_absorbed", "trips_target", "length_absorbed_km", "length_target_km"]]),
           ("\nNo merge candidates in: " + ", ".join(sorted(set(ev.city) - set(mg.city))) + " - in these feeds the scheduled trip counts are so uniform (for example frequency-template feeds) that no route is lightly scheduled relative to its peers.\n") if set(ev.city) - set(mg.city) else "",
           "\n**Must be verified before merging:** passenger demand on both routes, vehicle capacity, travel time, whether the unshared stops stay covered (the simulation keeps them on the merged route), and whether the routes have different purposes (e.g. express vs local).\n",
           "## 3. Route splitting\n",
           f"**Rule:** a route is a split candidate when it is **long** (>= {opt.SPLIT_MIN_KM:.0f} km and in the top {int((1 - opt.SPLIT_LEN_Q) * 100)}% of its city) and **complex** (>= {opt.SPLIT_MIN_STOPS} stops) and its scheduled speed is plausible. "
           f"**{len(sp):,} candidates** (`tables/module6_split_suggestions.csv`): " + ", ".join(f"{c} {n}" for c, n in sp.groupby('city').size().items()) + ". Longest examples:\n", md_table(sp.sort_values("length_km", ascending=False).head(6)[["city", "route", "length_km", "length_method", "stops", "trips"]]),
           "\nLengths from stop coordinates are straight-line lower bounds, so those routes may be even longer. **Must be verified before splitting:** passenger journeys along the route, where the transfer would be and its burden, travel time, connectivity between the parts.\n",
           "## 4. Trip-frequency adjustment\n",
           f"**What the data supports:** a *service-standard* check, not a demand-based one. Routes with at least {opt.FREQ_MIN_TRIPS} scheduled trips but **fewer than {opt.FREQ_NEED} departures in their busiest hour** have a headway above {opt.FREQ_HEADWAY_STANDARD} minutes even at their own peak. "
           f"**{len(fq):,} routes** qualify (`tables/module6_frequency_suggestions.csv`); adding one departure in the busiest hour would bring each to a {opt.FREQ_HEADWAY_STANDARD}-minute headway ({int(fq.trips_to_add.sum()):,} trips in total).\n",
           "**What it does not support:** the 30-minute standard is **our assumption**, not an operator rule, and nothing here shows that passengers need these trips. **No trip reductions or redistributions are suggested**: without reliable demand data we cannot know which trips are unnecessary, and minimum service levels must be kept.\n",
           "## Limitations\n", "* Scheduled data only; no ridership, capacity, delays or operating cost.", "* Stop-based overlap and straight-line lengths approximate geography; shapes were not used for the suggestions.", "* Thresholds (80% overlap, 25th percentile, 40 km, 30 stops, 30-minute standard) are stated rules of thumb and change the counts.", "* Hyderabad is excluded; Delhi, Kochi and Pune have near-constant scheduled speeds, so their durations are model timetables."]
    open(f"{REP}/module6_route_investigation_and_suggestions.md", "w", encoding="utf-8").write("\n".join(inv))

    mt = tot
    cmpr = [f"# Module 6 - Current versus simulated network\n\n_Generated {stamp}._ The simulation changes **a copy** of the route table (`data/simulated/simulated_network.csv`); the original data is untouched. "
            "Current and simulated metrics use the **same definitions and the same schedule period**. All simulated numbers are **what-if results, not forecasts**.\n",
            "## Assumptions of the simulation\n",
            "* **Merge:** the absorbed route's departures are **kept** (no trips removed); the merged route gets the unshared part of the absorbed route (length x (1 - shared-stop share)) and its stops; the absorbed route disappears.",
            "* **Split:** the route is cut at its middle stop into two routes of half the length; **each part keeps all original departures**, so scheduled trip-km stays the same while the number of trip records doubles; transfer burden is ignored.",
            "* **Frequency:** trips are added until the busiest hour has 2 departures (a 30-minute headway standard).",
            "* **Combined:** all three, with precedence merge > split > frequency (a route is changed once).",
            "* The unique stops served do not change in any scenario (every stop stays on some route), so **stop coverage is preserved by construction**; geographical coverage and passenger access could not be measured.\n",
            "## Network metrics (all comparable cities)\n", md_table(mt.reset_index()),
            "\n*Metric definitions:* routes = number of routes; scheduled trips = number of scheduled trips (trip records); est. route distance = sum of estimated route lengths; scheduled trip-km = sum of trips x route length (scheduled vehicle-kilometres); "
            "the last column counts routes with >= 6 trips but < 2 departures in their busiest hour (only meaningful for the current network and the frequency scenario, because merging and splitting change what 'busiest hour' means).\n",
            "![total](figures/module6_placeholder)\n".replace("figures/module6_placeholder", "figures/module6/m6_05_current_vs_simulated_total.png"), "![city](figures/module6/m6_06_current_vs_simulated_by_city.png)\n",
            "## Reading the comparison\n",
            f"* **Merging** reduces the number of routes by {int(base.routes - tot.loc['merge only', 'routes']):,} ({100 * (tot.loc['merge only', 'routes'] / base.routes - 1):.1f}%) and the estimated route distance by {-100 * (tot.loc['merge only', 'est_route_distance_km'] / base.est_route_distance_km - 1):.1f}%, with scheduled trips unchanged. Because the merged route is longer and runs all departures, scheduled trip-km rises by {100 * (tot.loc['merge only', 'scheduled_trip_km'] / base.scheduled_trip_km - 1):.1f}%.",
            f"* **Splitting** leaves the estimated total distance and the scheduled trip-km unchanged, adds {int(tot.loc['split only', 'routes'] - base.routes):,} routes and {int(tot.loc['split only', 'scheduled_trips'] - base.scheduled_trips):,} trip records, and cuts the number of routes longer than 40 km from {int(base.routes_over_40km):,} to {int(tot.loc['split only', 'routes_over_40km']):,}. Its benefit (shorter routes, easier management) is operational and cannot be measured here.",
            f"* **The frequency standard** adds {int(tot.loc['frequency standard only', 'scheduled_trips'] - base.scheduled_trips):,} scheduled trips ({100 * (tot.loc['frequency standard only', 'scheduled_trips'] / base.scheduled_trips - 1):.1f}%) and brings routes with fewer than 2 departures in the busiest hour from {int(base.routes_with_under_2_departures_in_peak_hour):,} to {int(tot.loc['frequency standard only', 'routes_with_under_2_departures_in_peak_hour']):,}.",
            f"* **Combined:** {int(tot.loc['combined', 'routes']):,} routes (from {int(base.routes):,}), {int(tot.loc['combined', 'scheduled_trips']):,} scheduled trips (from {int(base.scheduled_trips):,}), estimated distance {tot.loc['combined', 'est_route_distance_km']:,.0f} km (from {base.est_route_distance_km:,.0f} km).\n",
            "**Important:** fewer routes or less distance does **not** mean a better network. Passenger access, geographical coverage, travel times and demand were not measured; the table shows only what these *assumptions* do to the *schedule*.\n",
            "## What would be needed to judge the impact\n", "* Boardings per route, stop and time period, matched to the GTFS route ids and dates.", "* Vehicle capacity and fleet availability.", "* Travel-time data and transfer volumes (for splits), and the operator's purpose for each route.", "* Validated route shapes for every route to measure real overlap and coverage.\n",
            "## By city\n", md_table(met[met.scenario.isin(["current network", "combined"]) & (met.city != "ALL CITIES")][["scenario", "city", "routes", "scheduled_trips", "est_route_distance_km", "avg_route_length_km", "scheduled_trip_km", "avg_trips_per_route"]].sort_values(["city", "scenario"]))]
    open(f"{REP}/module6_current_vs_simulated_comparison.md", "w", encoding="utf-8").write("\n".join(cmpr))
    print(f"done | inference check diff {max_diff:.1e} | roles {by_role.routes.to_dict()} | new-feed noise {gv(ROLE_NEW, 'dbscan_noise_pct')}% | candidates >=2 flags {len(cand)} (>=3: {len(strong)}) | merges {len(mg)} splits {len(sp)} freq {len(fq)} | "
          f"routes {int(base.routes)} -> {int(tot.loc['combined', 'routes'])}")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--input") + 1] if "--input" in sys.argv else None)
