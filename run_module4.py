"""Module 4 runner: preprocess the route features for the planned unsupervised models (KMeans, DBSCAN).

    python run_module4.py                      # default: Hyderabad excluded from the pooled modelling set
    python run_module4.py --include-all       # keep every feed (flagged), e.g. if the mentor says so
Writes data/processed/module4/*.csv, preprocessor.joblib and reports/module4_*.md. Raw and Module-2 files are not modified.
"""
import datetime, os, sys
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from src import preprocessing as pp
from run_module2 import md_table

OUT, REP = "data/processed/module4", "reports"
INPUT = "data/processed/all_cities_route_features.csv"
UNUSED = {  # column of route_features.csv -> why it is not a model feature
    "city, route_id, route_name": "identifiers / grouping (kept as ID columns, never used as numbers; city is not a feature so clusters do not simply copy city)",
    "overlap_partner, overlap_partner_name": "identifiers of another route (text)",
    "route_type": "constant (all routes are buses after Module 2)",
    "median_trip_duration_min": "almost the same information as avg_trip_duration_min; one of the pair is enough",
    "trips_morning, trips_afternoon, trips_evening, trips_night": "replaced by period shares (trips in a period / n_trips) so the time-of-day pattern is not just n_trips again",
    "first_departure_h, last_departure_h": "summarised by service_span_h",
    "peak_hour, peak_hour_trips": "peak_hour is circular (23 is next to 0) -> replaced by the categorical peak_period; peak_hour_trips follows n_trips",
    "trips_monday .. trips_sunday, avg_trips_per_weekday, avg_trips_per_weekend_day": "equal to n_trips whenever every service runs every day (true in most feeds); no weekday/weekend information",
    "weekend_to_weekday_ratio": "candidate feature but dropped automatically: 1.0 for almost every route (near-constant, no information)",
    "n_service_ids, n_directions, trips_from_frequency": "properties of how a feed was written (missing for whole feeds or only in Kochi), not of the route",
    "length_km_stops, length_km_shape": "components of length_km (its length_method is kept as a categorical feature)",
    "overlap_share_of_route": "max_stop_overlap already describes the overlap",
    "has_time_backwards_trip, speed_implausible, sparse_schedule": "data-quality / descriptive flags (speed_implausible is handled through the invalid-speed rule; sparse_schedule is derived from n_trips)",
}


def main(include_all=False):
    os.makedirs(OUT, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    raw = pp.load_features(INPUT)
    d = pp.add_derived(raw)
    exclude = {} if include_all else pp.EXCLUDE_FEEDS
    d, ex = pp.split_exclusions(d, exclude)
    ex.to_csv(f"{OUT}/excluded_routes.csv", index=False)
    miss_before = pp.missing_report(d, pp.NUMERIC)
    # ---- investigate WHY headway is missing
    h = d.median_headway_min.isna()
    ev = pd.DataFrame({"routes": [int((d.n_trips <= 1).sum()), int((d.n_trips >= 2).sum())],
                       "missing_headway": [int(h[d.n_trips <= 1].sum()), int(h[d.n_trips >= 2].sum())]}, index=["routes with 1 trip", "routes with 2+ trips"])
    ev["share_missing_%"] = (100 * ev.missing_headway / ev.routes).round(1)
    # ---- invalid speed
    inv_city = d.groupby("city").speed_invalid.agg(["sum", "mean"]).rename(columns={"sum": "invalid_speed_routes", "mean": "share"}).round(3)
    low = int((raw.loc[d.index, "avg_speed_kmh"] < pp.SPEED_RANGE[0]).sum()); high = int((raw.loc[d.index, "avg_speed_kmh"] > pp.SPEED_RANGE[1]).sum())
    # ---- split + fit on training only
    tr, va = pp.train_validation_split(d)
    P = pp.RoutePreprocessor().fit(tr)
    Xtr, Xva = P.transform(tr), P.transform(va)
    assert not Xtr.isna().any().any() and not Xva.isna().any().any() and np.isfinite(Xtr.values).all() and np.isfinite(Xva.values).all()
    ids = ["city", "route_id", "route_name"]
    pd.concat([tr[ids].reset_index(drop=True), Xtr.reset_index(drop=True)], axis=1).to_csv(f"{OUT}/train_preprocessed.csv", index=False)
    pd.concat([va[ids].reset_index(drop=True), Xva.reset_index(drop=True)], axis=1).to_csv(f"{OUT}/validation_preprocessed.csv", index=False)
    joblib.dump(P, f"{OUT}/preprocessor.joblib")
    # ---- feature list
    roles = []
    for f in P.feature_names:
        role = "missing/invalid indicator (0/1, unscaled)" if f.endswith("_was_missing") else "one-hot (0/1)" if "__" in f else \
            ("log1p + standardised" if f in P.log_cols else "standardised")
        roles.append(dict(feature=f, treatment=role))
    pd.DataFrame(roles).to_csv(f"{OUT}/feature_list.csv", index=False)
    # ---- suitability sanity check (NOT a Module-5 result)
    rs = np.random.RandomState(0)
    sub = Xtr.iloc[rs.choice(len(Xtr), min(4000, len(Xtr)), replace=False)]
    km = KMeans(4, n_init=10, random_state=0).fit(sub)
    sil_tr = silhouette_score(sub, km.labels_)
    va_sub = Xva.iloc[rs.choice(len(Xva), min(2000, len(Xva)), replace=False)]
    sil_va = silhouette_score(va_sub, km.predict(va_sub))
    dist = pd.DataFrame({"split": ["train", "validation"], "routes": [len(tr), len(va)]})
    city_bal = pd.concat([tr.city.value_counts(normalize=True).rename("train"), va.city.value_counts(normalize=True).rename("validation")], axis=1).round(3).fillna(0)
    city_bal.insert(0, "city", city_bal.index)

    inv_tbl = inv_city.reset_index()
    # ================= reports
    mv = [f"# Module 4 - Missing values summary\n\n_Generated {stamp}._ Input: `data/processed/all_cities_route_features.csv` (Module 2), {len(raw):,} routes"
          + (f"; {len(ex):,} routes of {', '.join(sorted(ex.city.unique()))} excluded (see decisions report) -> {len(d):,} routes modelled." if len(ex) else ", all feeds kept.") + "\n",
          "## Columns with missing or invalid values (candidate features only)\n", md_table(miss_before),
          "\n## Why the values are missing - investigation\n",
          "**`median_headway_min`.** Headway needs at least two scheduled departures of the same route and service. The table shows where it is missing:\n", md_table(ev.reset_index().rename(columns={"index": "group"})),
          "\nEvery missing value belongs to a route with exactly one scheduled trip, and no route with two or more trips is affected. With a single departure there is no gap between two departures, so the value is **undefined in the source**: it cannot be recovered from the GTFS files, and it is not zero.\n",
          f"**`avg_speed_kmh`.** Scheduled speed = estimated route length / scheduled duration. {low} routes have a speed below {pp.SPEED_RANGE[0]} km/h and {high} above {pp.SPEED_RANGE[1]} km/h, which no bus schedule can mean; the length (a straight-line estimate for many feeds) or the timetable is unreliable. Both inputs come from the source, so the speed cannot be recovered. By city:\n", md_table(inv_tbl),
          "\n**Other columns:** `length_km_shape` (missing wherever a feed has no shapes) and `n_directions` (missing where a feed has no direction_id) are not model features; `overlap_partner` (missing for routes with no overlap partner) is an identifier. No route was removed for missing values.\n",
          "\n## Methods and justification\n",
          "| Column | Method | Why |", "|---|---|---|",
          "| median_headway_min | median imputation (median of the **training** routes) + a 0/1 column `median_headway_min_was_missing` | The median is robust to the very skewed headways; the indicator keeps the information that the route has no repeating service, so the filled value is not mistaken for a real headway. Zero would mean a bus every 0 minutes. |",
          "| avg_speed_kmh | impossible values set to missing, then median imputation + `avg_speed_kmh_was_missing` | An invalid value is not a measurement; deleting the route would lose its other valid features. |",
          "\nAfter preprocessing, the number of missing or infinite values in the modelling tables is **0** (checked by the runner). The original files are unchanged.\n"]
    open(f"{REP}/module4_missing_values_summary.md", "w", encoding="utf-8").write("\n".join(mv))

    sk = P.skew_before.round(2).rename("skewness (train, after imputation)").reset_index().rename(columns={"index": "feature"})
    sk["log1p applied"] = sk.feature.isin(P.log_cols).map({True: "yes", False: "no"})
    es = [f"# Module 4 - Categorical encoding and feature scaling\n\n_Generated {stamp}._ Planned next models: KMeans and DBSCAN, both **distance based**.\n",
          "## Categorical features and encoding\n", md_table(pd.DataFrame([
              ["length_method", "how the route length was obtained (shapes.txt / stop coordinates / shape failed sanity check)", "one-hot", "unordered labels, so a single 1-2-3 column would invent an order and distances between them"],
              ["peak_period", "time period of the route's busiest hour (morning / afternoon / evening / night)", "one-hot", "unordered labels; recomputed from peak_hour with the Module-2 period rules; hour 23 and hour 0 are not far apart, which a plain number would claim"]],
              columns=["feature", "meaning", "encoding", "why"])),
          "\n**Not encoded as numbers:** `route_id`, `route_name`, `city` (identifiers/groups, kept beside the features, never inside them). Label encoding was not used because none of the categorical features has a natural order. The one-hot encoder is fitted on training data and ignores unknown categories at validation time.\n",
          "## Scaling\n",
          "* **Method: standardisation (z-score)**, fitted on the training routes: (x - mean) / standard deviation. KMeans and DBSCAN use Euclidean distance, so a feature measured in large units (e.g. trips, up to hundreds) would dominate one in small units (e.g. a 0-1 share). Standardisation gives every numeric feature mean 0 and standard deviation 1.",
          "* **Why not min-max:** a few very long or very frequent routes would squeeze all other routes into a tiny part of 0-1, and DBSCAN's distance threshold depends on that spread.",
          "* **Skew first:** counts and lengths are strongly right-skewed (seen in Module 3). Features with training skewness above " + str(pp.SKEW_LIMIT) + " get `log1p` **before** standardisation so a few extreme routes do not stretch the scale.\n",
          md_table(sk),
          "\n* **Not scaled:** the 0/1 one-hot columns and missing-indicator columns (already on a 0-1 scale).\n",
          "\n## Verification\n", md_table(Xtr.describe().loc[["mean", "std"]].T.reset_index().rename(columns={"index": "feature"}).round(3).head(len(P.num_final))),
          "\nTraining means are 0 and standard deviations 1 by construction; the validation set is transformed with the **training** mean and standard deviation, so its values are not exactly 0 / 1 - this is intended.\n"]
    open(f"{REP}/module4_encoding_and_scaling.md", "w", encoding="utf-8").write("\n".join(es))

    sp = [f"# Module 4 - Training / validation split and evaluation strategy\n\n_Generated {stamp}._\n",
          "## There is no supervised target\n",
          "Classification would need a valid label such as 'overcrowded' or 'underutilised'. GTFS has no passenger data, so such a label can only be an assumption and the mentor's rules forbid unsupported performance labels. **No target was created.** For KMeans and DBSCAN no target is needed. If real ridership data becomes available, a supervised task can be added later.\n",
          "## The split\n",
          f"* **80:20 split, {len(tr):,} training and {len(va):,} validation routes** (`random_state=42`, reproducible).",
          "* **Grouped by city and route name:** many routes are the up/down/variant patterns of one bus line and look almost identical. A purely random split would put near-copies on both sides and make validation look better than it is, so all routes with the same name in a city stay on the same side.",
          "* **Fit on training only:** medians, skewness decisions, means/standard deviations, category lists and the constant/correlation filters are learned from the training routes and applied unchanged to the validation routes (no leakage).\n",
          "City balance of the split (share of routes):\n", md_table(city_bal.reset_index(drop=True), floatfmt="{:.3f}"),
          "\n## Evaluation strategy for the next module (clustering)\n",
          "No accuracy can be computed without ground truth. Clusters will be judged by:\n",
          "1. **Internal measures** on the training data (silhouette score; for DBSCAN the share of noise routes) to choose k / eps.",
          "2. **Generalisation:** validation routes are assigned to the training clusters and the silhouette is compared with the training value; a large drop means the clusters are not stable.",
          "3. **Stability:** repeat with different random seeds and compare cluster assignments.",
          "4. **Interpretation:** cluster profiles (median trips, stops, length, periods) per city; clusters are *groups of similar scheduled service*, not 'good' or 'bad' routes.\n",
          "## Suitability check (a sanity check only, not a Module 5 result)\n",
          f"A quick KMeans with k=4 on a 4,000-route training sample gives a silhouette of {sil_tr:.2f}; assigning a 2,000-route validation sample to those centres gives {sil_va:.2f}. The tables contain no missing or infinite values, so they can be used by KMeans and DBSCAN. The numbers say nothing about route quality.\n"]
    open(f"{REP}/module4_split_and_evaluation_strategy.md", "w", encoding="utf-8").write("\n".join(sp))

    used = pd.DataFrame(roles)
    fs = [f"# Module 4 - Features selected and preprocessing decisions\n\n_Generated {stamp}._\n",
          f"## Pipeline (all steps fitted on training routes)\n",
          "1. Load the Module-2 route table; **keep the original file untouched**.",
          "2. Derived columns: period shares (`trips_<period>` / `n_trips`), `peak_period`, and invalid-speed handling.",
          ("3. Exclude non-comparable feeds: " + "; ".join(f"**{c}** ({r})" for c, r in exclude.items()) + f" - {len(ex):,} routes, listed in `excluded_routes.csv`.") if exclude else "3. No feed excluded (`--include-all`).",
          "4. Split 80:20 (grouped by city + route name).",
          f"5. Drop near-constant features (> {int(pp.CONSTANT_SHARE * 100)}% one value): " + (", ".join(P.dropped_constant) or "none") + ".",
          "6. Median imputation (+ missing indicators), `log1p` for skewed features, standardisation, one-hot encoding.",
          f"7. Drop one of any pair correlated above {pp.CORR_LIMIT}: " + (", ".join(f"{b} (vs {a}, r={r})" for a, b, r in P.corr_pairs) or "none found") + ".\n",
          f"## Final feature set ({len(P.feature_names)} columns)\n", md_table(used),
          "\nThese features describe the **scheduled service** of a route: how many trips and stops, how long and how fast on paper, how spread over the day, how much it shares stops with others, and how its length was measured.\n",
          "## Columns not used as features\n", md_table(pd.DataFrame(list(UNUSED.items()), columns=["columns", "reason"])),
          "\n## Decision on non-comparable feeds\n",
          "Hyderabad's 'trips' appear to be whole vehicle duties (Module 3), so `n_trips`, headway, duration and speed mean something different there. Putting them in the same distance space as single-run trips would distort KMeans/DBSCAN. They are therefore **excluded from the pooled modelling set, not deleted**: they stay in Module 2 and in `excluded_routes.csv`, and `python run_module4.py --include-all` keeps them. This is open for the mentor to decide. Delhi, Kochi and Pune (near-constant speeds, generated-looking timetables) are kept, because their trip counts are comparable; their speeds should be read with care.\n"]
    open(f"{REP}/module4_feature_selection_and_decisions.md", "w", encoding="utf-8").write("\n".join(fs))

    al = [f"# Module 4 - Assumptions, limitations and challenges\n\n_Generated {stamp}._\n",
          "## Assumptions\n",
          f"* A speed outside {pp.SPEED_RANGE[0]}-{pp.SPEED_RANGE[1]} km/h cannot come from a real timetable and is treated as invalid.",
          f"* Skew limit {pp.SKEW_LIMIT}, near-constant limit {int(pp.CONSTANT_SHARE * 100)}% and correlation limit {pp.CORR_LIMIT} are standard rules of thumb, not tuned on results.",
          "* Median imputation assumes that a single-departure route is, for distance purposes, 'typical' in headway; the indicator column keeps the difference visible.",
          "\n## Limitations\n",
          "* **No ground truth and no passenger data:** nothing here shows which routes are overcrowded or underutilised; the next module can only group routes by similarity of scheduled service.",
          "* The features are scheduled values; several feeds are community-made or old, and some show generated-looking timetables (Delhi, Kochi, Pune).",
          "* Excluding Hyderabad is a judgement; its routes are not represented in the pooled clusters.",
          "* Route length from stop coordinates is a straight-line lower bound for most feeds; `length_method` is kept so the model can see which routes have shape-based length.",
          "* Grouping by route name keeps variants of a line together, but different lines that share stops can still be similar across the split.",
          "\n## Challenges\n",
          "* Deciding what to do with 16% missing headways without inventing a value (solved with median + indicator after showing the value is undefined).",
          "* Choosing what to do with feeds that are not comparable (excluded, documented, reversible).",
          "* Avoiding leakage between up/down variants of the same line (grouped split).",
          "* Not creating a classification target because no valid label exists.\n"]
    open(f"{REP}/module4_assumptions_limitations.md", "w", encoding="utf-8").write("\n".join(al))
    print(f"done: train {len(tr)} validation {len(va)} features {len(P.feature_names)} excluded {len(ex)} | sanity silhouette {sil_tr:.2f}/{sil_va:.2f}")


if __name__ == "__main__":
    main(include_all="--include-all" in sys.argv)
