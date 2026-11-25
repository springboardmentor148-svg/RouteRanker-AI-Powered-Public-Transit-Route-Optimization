# RouteRanker Module 6 Report: Out-of-Sample Model Inference & Optimization Simulation (Chennai MTC)

**Project:** RouteRanker — AI-Based Public Transit Route Analysis for Indian Cities  
**Training Scope:** 8 Indian Bus Transit Networks (`Ahmedabad`, `Bengaluru`, `Davangere`, `Delhi`, `HDBRT`, `Mumbai`, `Pune`, `Rajkot`)  
**Unseen Inference Target:** Chennai Metropolitan Transport Corporation (`MTC`) GTFS (`NEW CITY/GTFS/`)  
**Notebook & Pipeline Artifacts:** [`module6_inference.ipynb`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/module6_inference.ipynb), [`src/feature_pipeline.py`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/src/feature_pipeline.py)  
**Date:** November 25, 2026 | **Random Seed:** `42`

> **Provenance Labeling Key Used Throughout This Report**  
> * **`[ACTUAL DATA]`** — Directly observed counts, timetables, coordinates, or ratios from published GTFS feeds.  
> * **`[ESTIMATE]`** — Approximations derived where physical road geometry (`shapes.txt`) is missing (`stop_straight_line_estimate`).  
> * **`[MODEL PREDICTION]`** — Unsupervised cluster assignments, distance metrics, or novelty flags inferred from frozen training models.  
> * **`[SIMULATED RESULT]`** — Hypothetical timetable outputs computed on isolated copies (`simulation/`) under stated what-if rules.

---

## 1. End-to-End Inference & Simulation Workflow

1. **Asset Loading & Pipeline Extraction:** Verified all pre-trained artifacts (`models/kmeans_model.joblib`, `models/dbscan_model.joblib`, `processed/pipeline/feature_scaler.joblib`, `processed/pipeline/one_hot_encoder.joblib`, `processed/pipeline/length_cap.json`, `processed/pipeline/feature_list.json`). Extracted Module 2 feature engineering logic verbatim into [`src/feature_pipeline.py`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/src/feature_pipeline.py) and confirmed exact **0-difference** cell-by-cell reproduction on both **Rajkot** (`271 × 20`) and **Pune** (`628 × 20`) training feeds.
2. **Unseen Data Ingestion & Quality Audit:** Loaded Chennai's five core GTFS files (`routes.txt`, `trips.txt`, `stop_times.txt`, `stops.txt`, `calendar.txt`), prefixed all identifiers with `chennai_`, documented raw data quality checks without mutating source files, engineered the exact 20-column schema into [`inference/new_city_route_features.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_route_features.csv).
3. **Leakage-Free Preprocessing (`.transform()` Only):** Isolated `677` unscheduled catalog routes into [`inference/new_city_unserved_routes_catalog.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_unserved_routes_catalog.csv), capped route lengths at the training 99th percentile (`82.6022 km`), applied `np.log1p` and diurnal shares, transformed strictly via frozen `RobustScaler` and `OneHotEncoder`, and saved the clean `3,934 × 12` matrix to [`inference/new_city_model_input.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_model_input.csv) alongside separate IDs in [`inference/new_city_route_lookup.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_route_lookup.csv).
4. **Unsupervised Inference:** Assigned Chennai routes to K-Means clusters (`K = 5`) with distance-based certainty flags and projected Chennai onto the DBSCAN density neighborhood (`eps = 1.0`, `min_samples = 10`) using `NearestNeighbors` on the `8,344` saved training core points.
5. **Candidate Screening & Structured Suggestions:** Combined five independent operational and model indicators (`indicator_count >= 2`) to build a ranked review queue ([`inference/new_city_candidates.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_candidates.csv)), then screened topology- and peer-supported merge, split, and frequency review candidates into [`inference/optimization_suggestions.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/optimization_suggestions.csv).
6. **What-If Simulation & Evaluation:** Executed Merge Only, Split Only, Frequency Only, and Combined rules on isolated deep copies (`simulation/SIMULATED_routes_*.csv`), verified 100% stop-period conservation, and persisted unified baseline-vs-simulated deltas in [`results/current_vs_simulated.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/current_vs_simulated.csv).

---

## 2. Unseen City Data Description, Source & Differences from Training Cities

* **Source & Metadata (`ACTUAL DATA`):** Chennai MTC GTFS located in `NEW CITY/GTFS/` (Source: `https://github.com/ungalsoththu/ChennaiGTFS/blob/main/data/mtc-gtfs.zip`, Snapshot Date: `21/11/2026`). `agency.txt` identifies `MTC` (`agency_id = 69`, `Asia/Kolkata`); `feed_info.txt` indicates publisher `IthuUngalSoththu`, version `0.1`.
* **Scale & File Inventory (`ACTUAL DATA`):**
  * `routes.txt`: `4,611` catalog routes (`3,934` active scheduled routes with trips [`85.32%`]; `677` unscheduled catalog routes [`14.68%`]).
  * `trips.txt`: `47,047` distinct scheduled trips across `direction_id` `0` (`23,674`) and `1` (`23,373`).
  * `stop_times.txt`: `1,360,443` stop-time records (`0` missing, `0` bad time formats, `1,904` valid overnight timestamps $\ge$ 24:00:00 representing trips starting before midnight and finishing past midnight).
  * `stops.txt`: `5,580` catalog stops (`5,477` actively served by trips; `103` unserved), all falling within Chennai bounds (`lat` `12.6148–13.4904°N`, `lon` `79.8019–80.3358°E`).
  * `calendar.txt`: `6` rows spanning placeholder window `2024-05-01` to `2030-05-01` (`0` parse or `end < start` errors). Unreferenced artifact entries `chennai_test ` and `chennai_'/><script>alert(1)</script>` (along with `Weekend` and `Hybrid`) exist in `calendar.txt` with **0 trips** referencing them (`trips.txt` references only `Regular` [`46,973` trips] and `HSC` [`74` trips]); all raw rows were documented unchanged.

### Key Schema & Structural Differences vs. Training Cities

| Aspect | 8 Training Cities | Chennai Unseen Feed | Downstream Impact |
|---|---|---|---|
| **`shapes.txt` & `shape_id`** | Present in `bengaluru`, `pune`; absent in other 6 | **Absent** | All `3,934` active route lengths rely on `stop_straight_line_estimate` (`[ESTIMATE]`, ~15–35% lower than road distance); no GIS path geometry overlap can be claimed. |
| **`frequencies.txt`** | Absent in all 8 cities | **Absent** | Zero impact; timetables are explicitly enumerated in `stop_times.txt`. |
| **`trips.direction_id`** | Present in 6 cities; absent in `davangere`, `delhi` | **Present** (`0` and `1`) | Enables directional headway calculation without interleaving opposite directions. |
| **Optional GTFS Columns** | `trip_headsign`, `stop_headsign`, `timepoint`, `zone_id`, `parent_station` vary by city | **Absent** | **Zero impact** on the 20 engineered features or 12 ML input features. |
| **Route & Calendar Conventions** | Varies by municipal agency | Separate `route_id` per direction/variant (`2,291` shared `route_short_name`s); active trips operate 6 (`HSC`) or 7 (`Regular`) days/wk | Keeps `route_id` as strict unique key; zero Chennai routes operate exclusively weekday-only or weekend-only. |

---

## 3. Feature Engineering, Preprocessing & Training Comparability Checks

* **Pipeline Execution Verification (`ACTUAL DATA` / `ESTIMATE`):** All `3,934` active routes have complete `trip_count` (`mean 11.96`, `median 4.00`, `max 210.00`), `stop_count` (`mean 24.41`, `median 23.00`, `max 80.00`), `route_length_km [ESTIMATE]` (`mean 17.28 km`, `median 15.43 km`, `min 0.40 km`, `max 83.42 km`; `8` routes `< 0.5 km` flagged, `0` routes `> 150 km`), and `service_span_hours` (`mean 8.05 h`, `median 8.83 h`, `max 23.92 h`). `median_headway_min` is computable for `3,065` multi-trip-per-direction routes (`mean 143.85 min`, `median 65.00 min`, `max 1,305.00 min`) and remains `NaN` for `869` single-trip/single-direction active routes (`is_headway_missing = True` in lookup).
* **Imputer & Missingness Audit:** No separate imputer `.joblib` exists in `processed/pipeline/` because Module 4 handled missing operational values by isolating unscheduled routes (`677` in Chennai) and excluding `median_headway_min` from Euclidean distance calculations. After isolation and transformation, [`inference/new_city_model_input.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_model_input.csv) contains **`0` NaNs and `0` Infs**, **`0` missing columns**, and **`0` unseen categories** (`dominant_time_period`: `2,462` `morning`, `694` `afternoon`, `409` `night`, `369` `evening`). One route (`83.42 km`) was clipped to the training cap `82.6022 km`.

### Distribution Shift Check: Chennai (`N = 3,934`) vs. `X_train` (`N = 7,386`)

| Scaled Feature | Train Mean ± SD | Chennai Mean ± SD | Outside Train `[min, max]` | Beyond `±3 Train SD` | Comparability Assessment |
|---|---:|---:|---:|---:|---|
| `night_trip_share_scaled` | `1.01 ± 2.40` | `2.26 ± 4.30` | `0.00%` | **`9.63%`** | **TAIL SHIFT** (RobustScaler IQR=`0.0666` amplifies nocturnal tails) |
| `evening_trip_share_scaled` | `0.07 ± 0.83` | `0.07 ± 0.90` | `0.00%` | **`5.08%`** | **TAIL SHIFT** |
| `first_departure_hour_scaled` | `0.81 ± 2.08` | `1.29 ± 2.67` | `0.00%` | **`4.86%`** | **TAIL SHIFT** (later afternoon/evening starts) |
| `period_night` (binary dummy) | `0.03 ± 0.17` | `0.10 ± 0.31` | `0.00%` | **`10.40%`** | **PREVALENCE SHIFT** (3.5× higher night-dominant share vs `3.0%` train) |
| `period_evening` (binary dummy) | `0.08 ± 0.27` | `0.09 ± 0.29` | `0.00%` | **`9.38%`** | **PREVALENCE SHIFT** (rare dummy base rate `<10%`) |
| Remaining 7 Features | — | — | `0.00%` | `0.00%–0.36%` | **In Range** |

Across all 12 inputs, **`0.00%`** of Chennai routes exceed `[train_min, train_max]`. However, predictions on late-evening/night routes where `night_trip_share_scaled` pushes Euclidean distances outward are flagged as less certain in downstream checks.

---

## 4. Unsupervised Inference Results (`[MODEL PREDICTION]`)

### A. K-Means Inference (`K = 5`, Nearest-Centroid Assignment)
Cluster labels `0–4` denote nominal **scheduled-service archetypes**, never performance rankings. All outputs are saved with explicit `MODEL_PREDICTION` headers in [`inference/new_city_kmeans_assignments.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_kmeans_assignments.csv).

| Cluster | Scheduled-Service Pattern | Training All (`N=9,233`) | Chennai `[MODEL PREDICTION]` (`N=3,934`) | `"assignment less certain"` |
|:---:|---|---:|---:|---:|
| **0** | Midday & PM Return Feeders (`1.0` med trips, `15:00` first dep.) | `1,181` (`12.79%`) | **`571` (`14.51%`)** | `52` (`9.1%`) |
| **1** | Morning Peak Commuter Shuttles (`2.0` med trips, `100%` AM dom.) | `1,789` (`19.38%`) | **`609` (`15.48%`)** | `33` (`5.4%`) |
| **2** | Late-Evening & Nocturnal Feeders (`4.0` med trips, `72.1%` night dom.) | `315` (`3.41%`) | **`510` (`12.96%`)** | `440` (`86.3%`) |
| **3** | High-Frequency Arterial Trunk Spines (`33.0` med trips, `17.8h` span) | `866` (`9.38%`) | **`405` (`10.29%`)** | `151` (`37.3%`) |
| **4** | Standard All-Day Regular Lines (`14.0` med trips, `13.4h` span) | `5,082` (`55.04%`) | **`1,839` (`46.75%`)** | `82` (`4.5%`) |

* **Centroid Distance Uncertainty Audit:** Using the training distance 95th percentile (**$P_{95}^{\text{train}} = 3.9254$**) computed on `X_train`, **`601` Chennai routes (`15.28%`)** exceed $P_{95}^{\text{train}}$ (mean distance `2.3132`, median `1.7945` vs. train median `1.7660`), and **`196` routes (`4.98%`)** are nearly equidistant between two centroids ($d_1 / d_2 \ge 0.90$). Combined, **`758` routes (`19.27%`)** carry the `"assignment less certain"` flag—concentrated heavily in Cluster 2 (`440` of `510` routes) due to `night_trip_share_scaled`. PCA projection fitted strictly on `X_train` (`PC1=45.03%`, `PC2=31.46%`, `76.49%` variance) confirms overall manifold alignment aside from this nocturnal tail (`phase3_kmeans_pca_scatter.png`).

### B. DBSCAN Inference (`eps = 1.0`, `min_samples = 10`, Euclidean Core-Sample Proximity)
* **Method & Training Verification:** Because scikit-learn `DBSCAN` has no `.predict()` method without altering fitted clusters, `NearestNeighbors(n_neighbors=1, metric='euclidean')` was fitted strictly on the **`8,344` saved training core points** (`dbscan_model.components_`). Routes within $\le 1.0$ inherit the nearest core point's cluster; routes $> 1.0$ are marked **`unassigned`**. Verification reproduced `dbscan_model.labels_` with **`99.90%` agreement** on a `1,000`-route random sample (`seed = 42`) and **`99.97%` full agreement** across all `9,233` training routes (`3` equidistant border ties).
* **Chennai Results (`MODEL PREDICTION`):** Saved in [`inference/new_city_dbscan_assignments.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_dbscan_assignments.csv). **`3,411` routes (`86.71%`)** map within $\epsilon = 1.0$ of dense training neighborhoods (led by DBSCAN Cluster `0` [`2,250`, `57.19%`], Cluster `2` [`487`, `12.38%`], Cluster `1` [`198`, `5.03%`], Cluster `4` [`190`, `4.83%`]), while **`523` routes (`13.29%`)** are **`unassigned`** (compared to `478` noise routes = `5.18%` in training).
* **Unassigned Profile (`ACTUAL DATA` / `ESTIMATE`):** Chennai `unassigned` routes exhibit a higher night trip share (`0.40` mean / `0.33` median vs `0.11` / `0.00` assigned), earlier `first_departure_hour` (`04:00` median vs `07:00`), fewer stops (`16.0` median vs `25.0`), and shorter estimated chord lengths (`10.39 km` median `[ESTIMATE]` vs `16.01 km`). Scaled mean deviation is led overwhelmingly by `night_trip_share_scaled` (`|Δ| = 5.136`). Crucially, `unassigned` indicates an atypical timetable relative to training neighborhoods—never incorrect or poor service.

---

## 5. Multi-Indicator Candidates & Optimization Screening (`candidate for investigation`)

### A. Candidate Screening Rule (`indicator_count >= 2`)
No route is flagged on one signal alone. Combining 5 independent binary checks—(1) `ind1_dbscan_unassigned` (`523`, `13.29%`), (2) `ind2_far_from_centroid` $> 3.9254$ (`601`, `15.28%`), (3) `ind3_peer_trip_outlier` outside training cluster `[P10, P90]` (`187`, `4.75%`), (4) `ind4_long_headway` $> \max(\text{cluster P90}, 180\text{ min})$ (`774`, `19.67%`), and (5) `ind5_unusual_length_or_dq` `< 0.5 km`, capped `> 82.60 km`, `> cluster P90`, or `0.0 min` convoy headway (`262`, `6.66%`)—yields **`440` routes (`11.18%`)** labeled **`"candidate for further investigation"`** in [`inference/new_city_candidates.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/new_city_candidates.csv):
* **Tier Breakdown:** `3` routes trigger all 5 indicators (`570P`, `40A R`, `570P CT` — running `2` trips over `8.2–12.7h` spans with `490–762 min` headways on `36–44 km` `[ESTIMATE]` corridors), `36` trigger 4 indicators (including `0.40 km` `[ESTIMATE]` short shuttles `54 CT1` and `578 CT`), `83` trigger 3 indicators, and `318` trigger 2 indicators. Historical training-city screening (`2,023` single-criterion low-activity routes; `8,241` overlap pairs) was referenced solely for context.

### B. Optimization Screening Summary ([`inference/optimization_suggestions.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/optimization_suggestions.csv))

| Type | Count | Evidence Summary (`status = "candidate for investigation"`) | Specific Missing Data / Check Required |
|---|---:|---|---|
| **`merge`** | `169` | Distinct `route_short_name` pairs (`>= 10` stops) in the same K-Means cluster with `Jaccard >= 0.90`, `cov >= 0.90`, forward contiguous stop sequence `>= 80%`, shared terminus, `<= 35 km` `[ESTIMATE]` (e.g. `159 R3` + `159 R5` sharing `55/55` stops, `J = 1.0`). Details: [`merge_candidates_detail.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/merge_candidates_detail.csv). | `shapes.txt` absent (stop-order only, no street geometry check); requires passenger load, capacity, running-time buffers, and express/local fare checks. |
| **`split`** | `25` | Long multi-stop corridors (`> Training P95 = 46.87 km` `[ESTIMATE]`, `>= 45` stops `[ACTUAL]`) passing interior hubs (`20%–80%`) served by `>= 100` active routes (e.g. `500W` [`51.59 km`] via **Tambaram West Bus Stand** [`367` routes]; `512` [`60.88 km`, `80` stops] via **Anna Nagar West Depot** [`128` routes]). Details: [`split_candidates_detail.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/split_candidates_detail.csv). | Zero through-passenger O–D counts, transfer time penalties, fare-reboarding rules, or observed end-to-end travel times. |
| **`frequency`** | `287` | Scale-matched peer deviations ($\pm 30\%$ length & stops, $\ge 20$ training peers in same cluster) with `median_headway_min > max(Peer P90, 240 min)` and $\ge 2$ daytime/evening periods $\le 1$ trip vs $\ge 5$ peer median (e.g. `M27`, `114S`). Details: [`frequency_candidates_detail.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/frequency_candidates_detail.csv). | Scheduled supply vs peer benchmarks only; adding or shifting trips requires actual demand, ridership, and fleet constraints. |

* **Actions Explicitly Refused (`"not supported by available data"`, [`unsupported_optimization_categories.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/inference/unsupported_optimization_categories.csv)):** Peak-hour load/fleet reallocation (no passenger APC/load data), street turning-movement consolidation (no `shapes.txt`), vehicle layover/block synchronization (no `block_id`/AVL), and service cuts/cost optimization (no O–D demand or revenue data).

---

## 6. What-If Simulation Rules & Baseline vs. Simulated Metrics (`results/current_vs_simulated.csv`)

Simulations ran on isolated deep copies of the active network (`simulation/`), recomputing all metrics via `src/feature_pipeline.py` and logging `822` route-level changes (`SIMULATED_change_log.csv`):
* **(a) Merge Only (`110` disjoint pairs):** Absorbs secondary route; keeps all dominant trips plus non-overlapping secondary trips (`> 10 min` departure gap in same direction/day_type; `426` kept, `335` duplicate departures dropped).
* **(b) Split Only (`25` corridors):** Splits all `125/125` trips cleanly at their interior hub into `_SEG_A` and `_SEG_B` retaining the hub stop in both legs (`+25` route legs, `+125` leg runs).
* **(c) Frequency Only (`287` routes):** Sets flagged daytime/evening gap windows (`06:00–11:59`, `12:00–16:59`, `17:00–20:59`) to training cluster median headway (`20.0 min` for C3 [`31` routes]; `34.0 min` for C4 [`256` routes]), synthesizing `+6,732` hypothetical supply trips along representative stop sequences.
* **(d) Combined:** Applies Merge $\rightarrow$ Split $\rightarrow$ Frequency sequentially (`400` operations: `110` merges, `25` splits, `265` frequency adjustments).

### Network Comparison Table (`ACTUAL` + `ESTIMATE` vs. `SIMULATED RESULT`)

| Scenario | Routes ($\Delta\%$) | Daily Trips ($\Delta\%$) | Total Length `[ESTIMATE]` ($\Delta\%$) | Avg Length `[ESTIMATE]` | Mean Headway | Trips/Hr (`24h`) | AM / PM / EVE / Night Trips/Hr | Stops Served (`0` Lost) |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| **Baseline `[ACTUAL]`** | `3,934` | `47,047` | `67,966.50 km` | `17.28 km` | `143.85 min` | `1,960.29` | `2,632.9 / 2,877.0 / 2,554.0 / 502.0` | `5,477 / 5,580` |
| **Merge Only `[SIMULATED]`** | `3,824` (`-2.80%`) | `46,712` (`-0.71%`) | `65,943.15 km` (`-2.98%`) | `17.24 km` | `140.54 min` (`-2.30%`) | `1,946.33` (`-0.71%`) | `2,612.7 / 2,851.8 / 2,543.0 / 499.0` | `5,477` (`0` lost) |
| **Split Only `[SIMULATED]`** | `3,959` (`+0.64%`) | `47,172` (`+0.27%`) | `67,966.50 km` (`0.00%`) | `17.17 km` | `144.38 min` (`+0.37%`) | `1,965.50` (`+0.27%`) | `2,640.0 / 2,885.4 / 2,560.0 / 503.1` | `5,477` (`0` lost) |
| **Frequency Only `[SIMULATED]`** | `3,934` (`0.00%`) | `53,779` (`+14.31%`) | `67,966.50 km` (`0.00%`) | `17.28 km` | `100.97 min` (`-29.81%`) | `2,240.79` (`+14.31%`) | `3,048.6 / 3,375.6 / 2,886.2 / 502.0` | `5,477` (`0` lost) |
| **Combined `[SIMULATED]`** | `3,849` (`-2.16%`) | `53,121` (`+12.91%`) | `65,943.15 km` (`-2.98%`) | `17.13 km` | `100.29 min` (`-30.28%`) | `2,213.38` (`+12.91%`) | `3,003.6 / 3,323.8 / 2,869.0 / 500.1` | `5,477` (`0` lost) |

* **Stop & Geographic Conservation:** Across all 4 simulated scenarios, **`0` physical stops lose all service** (`list = []`) and **`0` stops lose period-level coverage** in Morning, Afternoon, Evening, or Night windows across identical Chennai bounds (`12.6148–13.4904°N`, `79.8019–80.3358°E`).

---

## 7. Limitations and Cautions

1. **Model Predictions Are Not Guaranteed Facts:** Both K-Means cluster assignments and DBSCAN `unassigned` flags describe statistical proximity to patterns learned from an unsupervised feature space. In particular, `19.27%` of Chennai routes carry an `"assignment less certain"` flag and `13.29%` exceed DBSCAN $\epsilon = 1.0$.
2. **8-City Training Domain vs. Unseen Chennai Differences:** The pipeline and models were trained exclusively on 8 other Indian networks (`Ahmedabad`, `Bengaluru`, `Davangere`, `Delhi`, `HDBRT`, `Mumbai`, `Pune`, `Rajkot`). Chennai differs noticeably—carrying a 3.5× larger nocturnal-dominant share (`10.40%` vs `3.0%` in training) and distinct directional `route_id` conventions—so boundary tolerances learned on those 8 cities do not represent universal standards for MTC Chennai.
3. **Schedule Data Does Not Show Passenger Demand:** GTFS specifies **planned vehicle supply** only. Zero information exists regarding ridership volumes, boarding/alighting counts, peak load factors, or unserved passenger wait times.
4. **Unassigned or Unusual Routes Are Not Necessarily Inefficient:** Routes flagged by DBSCAN, K-Means distance, or multi-indicator screening are frequently legitimate specialized services (e.g., midnight pull-outs, `04:00` factory shifts, airport/suburban links, or dedicated short-turn variants) rather than operational problems.
5. **Suggestions Are Candidates for Investigation Only:** No entry in `optimization_suggestions.csv` constitutes a recommendation or operational decision to merge, split, or re-schedule any route. Fewer routes/trips in Merge simulation do not automatically imply improvement if peak capacity is needed, and added trips in Frequency simulation do not automatically represent net gain without operating cost justification.
6. **Additional Data Required Before Any Decision:**
   * **Ridership & Demand:** Stop-level boarding/alighting counts (APC/ETM/smartcard data) and origin–destination matrices (especially across proposed split hubs).
   * **Vehicle & Fleet Capacity:** Bus seating/standing capacity per trip, vehicle type allocation (`ordinary`, `deluxe`, `AC`, `minibus`), and fleet/crew shift availability.
   * **Travel Time & Operational Constraints:** Observed GPS/AVL segment running times, intersection congestion variability, depot pull-out/deadhead blocks (`block_id`), terminal layover space, and official GIS road shapes (`shapes.txt`).

---

## 8. Visualization Index (`visualizations/inference/`)

* **Phase 2:** [`phase2_feature_distribution_comparison.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase2_feature_distribution_comparison.png)
* **Phase 3 (`MODEL PREDICTION`):** [`phase3_kmeans_pca_scatter.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase3_kmeans_pca_scatter.png), [`phase3_kmeans_cluster_distribution.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase3_kmeans_cluster_distribution.png), [`phase3_kmeans_centroid_distance_hist.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase3_kmeans_centroid_distance_hist.png)
* **Phase 4 (`MODEL PREDICTION`):** [`phase4_dbscan_pca_scatter.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase4_dbscan_pca_scatter.png), [`phase4_dbscan_core_distance_hist.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase4_dbscan_core_distance_hist.png), [`phase4_dbscan_unassigned_feature_profile.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase4_dbscan_unassigned_feature_profile.png)
* **Phase 5–6:** [`phase5_candidates_trips_vs_length.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase5_candidates_trips_vs_length.png), [`phase5_candidates_breakdown_and_headway.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase5_candidates_breakdown_and_headway.png), [`phase6_merge_and_split_topology.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase6_merge_and_split_topology.png), [`phase6_frequency_peer_comparison.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase6_frequency_peer_comparison.png)
* **Phase 7–8 (`SIMULATED`):** [`phase7_simulation_network_comparison.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase7_simulation_network_comparison.png), [`phase8_main_metrics_comparison.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase8_main_metrics_comparison.png), [`phase8_trips_per_hour_by_period.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase8_trips_per_hour_by_period.png), [`phase8_affected_routes_geo_map.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/inference/phase8_affected_routes_geo_map.png)

---

## 9. Unresolved Questions & Points of Uncertainty

1. **Feed Currency & Calendar Placeholders:** `calendar.txt` carries uniform dates `2024-05-01` to `2030-05-01`, `feed_info.txt` shows version `0.1`, and `calendar.txt` contains unused test/XSS entries (`chennai_test `, `'/><script>alert(1)</script>`). It is uncertain whether all `4,611` catalog routes (and `677` zero-trip routes) reflect active MTC operations on 21/11/2026 or partially curated community GTFS snapshots.
2. **Express vs. Ordinary / AC Branch Distinctions:** Several high-overlap merge candidate pairs (e.g., `159 R3` vs `159 R5`, `188C R` vs `188Et R`) share identical `50–55` stop lists in `stop_times.txt` (`Jaccard = 1.0`), yet their short-name suffixes (`CT`, `Et`, `X`, `R`) may encode express fare tiers, limited stops not reflected in the static export, or depot allocations that are invisible in `routes.txt`.
3. **True Road Distances vs. Straight-Line Estimates:** Because `shapes.txt` is missing, curved coastal or flyover routes (and the `8` short routes near `0.40 km`) may have systematically different true road distances than `stop_straight_line_estimate`.
4. **Operational Feasibility of Simulated Frequency Additions:** The `+6,732` what-if daytime trips assume sufficient fleet and driver availability during morning/afternoon/evening windows without altering `night` coverage or deadhead turnarounds.
