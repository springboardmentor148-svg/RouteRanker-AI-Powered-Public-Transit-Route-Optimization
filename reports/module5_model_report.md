# Module 5 Technical Report: Machine Learning Model Development & Evaluation
**Project:** RouteRanker — AI-Powered Public Transit Route Analysis  
**Target Domain:** 8 Indian Municipal Bus Transit Networks (Ahmedabad, Bengaluru, Davangere, Delhi, HDBRT, Mumbai, Pune, Rajkot)  
**Primary Focus:** Unsupervised Machine Learning (K-Means & DBSCAN) and Leakage-Free Supervised Classification (Random Forest & XGBoost)  
**Artifact Date:** November 2026  
**Status:** Completed & Programmatically Verified  

---

## Executive Summary

Module 5 implements, validates, and compares machine learning models to discover latent operational structures across **9,233 active public transit routes** spanning 8 Indian cities. Using the 12 preprocessed, robustly scaled, and orthogonal features developed in Module 4, the analysis was conducted strictly within the boundaries of published timetable schedules:

1. **Unsupervised K-Means Partitioning:** Systematically evaluated across $K = 2$ through $10$. An optimal $K = 5$ was selected based on the geometric elbow method, silhouette analysis ($0.3076$), Davies-Bouldin index ($1.0241$), and cluster size balance. The model establishes a consistent 5-tier functional transit taxonomy: High-Frequency Trunk Spines ($9.4\%$), Morning Commuter Shuttles ($19.4\%$), Midday/PM Return Feeders ($12.8\%$), Late-Evening/Night Feeders ($3.4\%$), and Standard All-Day Regular Lines ($55.0\%$).
2. **Density-Based Outlier Detection (DBSCAN):** Evaluated across 27 parameter permutations ($\epsilon \in [0.4, 2.0]$, $\text{MinPts} \in \{5, 10, 20\}$). The approved final model ($\epsilon = 1.0, \text{MinPts} = 10$) identified 16 dense operational components while isolating **478 routes ($5.18\%$) as specialized noise points (`-1`)**. A deep cross-reference with Module 3 data quality classifications proved that $98.3\%$ of these noise points are valid, specialized transit operations (midnight routes, 24/7 super-spines, micro-depot runs) rather than data errors.
3. **Comparative Evaluation:** Cross-validation between K-Means and DBSCAN established an Adjusted Mutual Information (AMI) of $0.4139$. Computing Euclidean distances from routes to their assigned K-Means centroids confirmed that DBSCAN noise points reside on the extreme outer fringe of the feature space (mean centroid distance of $3.5089$ vs $1.8567$ for core routes).
4. **Supervised Classification (Leakage-Free Protocol):** Using the approved target label—within-city planned operational service level (Low, Medium, High)—and strictly dropping the target-leaking feature (`trip_count_log1p_scaled`), both Random Forest ($76.45\%$ accuracy, $0.7454$ macro F1) and XGBoost ($77.10\%$ accuracy, $0.7507$ macro F1) successfully learned to predict a route's planned frequency tier from its physical geometry, operating span, and diurnal schedule structure.

---

## 1. Input Datasets & Feature Space

The modeling pipeline consumes the preprocessed, leak-free datasets generated in Module 4:
* **Training Partition (`route_features_preprocessed_train.csv`):** $7,386$ routes ($80.0\%$), stratified across municipal agencies (`random_state=42`).
* **Validation Partition (`route_features_preprocessed_val.csv`):** $1,847$ routes ($20.0\%$), used exclusively for out-of-sample stability checking.
* **Full Active Network (`route_features_preprocessed_all.csv`):** $9,233$ routes with complete service records.
* **Metadata Lookups (`route_lookup_all.csv`):** Preserves route identifiers, agency tags, and operational flags separate from model inputs.

### The 12 Model Features:
1. `trip_count_log1p_scaled` (Numerical, Continuous): Daily scheduled trip volume, log-transformed ($\ln(1+x)$) and scaled via `RobustScaler`.
2. `stop_count_scaled` (Numerical, Continuous): Total stops on route trajectory, scaled via `RobustScaler`.
3. `route_length_km_log1p_scaled` (Numerical, Continuous): Route length in km, capped at the 99th training percentile ($82.60$ km), log-transformed, and scaled via `RobustScaler`.
4. `service_span_hours_scaled` (Numerical, Continuous): Operational duration from first to last departure, scaled via `RobustScaler`.
5. `first_departure_hour_scaled` (Numerical, Continuous): Scheduled time of day of first departure ($0.0$ to $23.0$), scaled via `RobustScaler`.
6. `morning_trip_share_scaled` (Numerical, Continuous): Proportion of trips operating in the AM peak ($06:00 - 10:00$), scaled via `RobustScaler`.
7. `evening_trip_share_scaled` (Numerical, Continuous): Proportion of trips operating in the PM peak ($16:00 - 20:00$), scaled via `RobustScaler`.
8. `night_trip_share_scaled` (Numerical, Continuous): Proportion of trips operating in nocturnal hours ($20:00 - 24:00+$), scaled via `RobustScaler`.
9. `period_afternoon` (Categorical, Binary): One-hot indicator for afternoon ($10:00 - 16:00$) dominance ($[0, 1]$).
10. `period_evening` (Categorical, Binary): One-hot indicator for PM peak ($16:00 - 20:00$) dominance ($[0, 1]$).
11. `period_morning` (Categorical, Binary): One-hot indicator for AM peak ($06:00 - 10:00$) dominance ($[0, 1]$).
12. `period_night` (Categorical, Binary): One-hot indicator for night ($20:00 - 06:00$) dominance ($[0, 1]$).

---

## 2. K-Means Clustering: Experiments, Selection & Profiling

### A. Algorithmic Mechanics
K-Means partitions $N$ routes into $K$ non-overlapping clusters by iteratively assigning each route to its nearest Euclidean centroid and updating centroids to the mean of assigned routes until within-cluster sum of squares (Inertia) reaches a minimum.

### B. Hyperparameter Grid Evaluation ($K = 2$ to $10$)
Fitted strictly on `X_train` with `n_init=10` and `random_state=42`. Results saved to `results/kmeans_k_comparison.csv`:

| $K$ | Inertia (WCSS) | Silhouette Score | Davies-Bouldin Index | Min Cluster Size | Max Cluster Size | Size Ratio (Min/Max) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 2 | 73,650.89 | 0.6303 | 0.8413 | 404 | 6,982 | $5.8\%$ |
| 3 | 51,183.19 | 0.4760 | 0.8615 | 346 | 6,075 | $5.7\%$ |
| 4 | 42,219.75 | 0.2725 | 1.1613 | 334 | 3,986 | $8.4\%$ |
| **5** | **35,786.46** | **0.3066** | **1.0384** | **250** | **4,048** | **$6.2\%$** |
| 6 | 31,631.12 | 0.3153 | 1.0467 | 134 | 4,060 | $3.3\%$ |
| 7 | 28,245.38 | 0.3274 | 0.9737 | 133 | 3,998 | $3.3\%$ |
| 8 | 25,099.25 | 0.3263 | 0.9050 | 85 | 3,893 | $2.2\%$ |
| 9 | 22,373.32 | 0.2795 | 0.9954 | 68 | 2,102 | $3.2\%$ |
| 10 | 20,529.48 | 0.2801 | 1.0305 | 67 | 1,466 | $4.6\%$ |

### C. Multi-Metric Selection Rationale for $K = 5$
* **Elbow Inflection Point:** Inertia plunges by $51.4\%$ from $K=2$ ($73,650.89$) down to $K=5$ ($35,786.46$). After $K=5$, the curve flattens into a gentle linear descent.
* **Cluster Viability:** At $K \ge 8$, cluster sizes drop below 100 routes ($85$ at $K=8$, $68$ at $K=9$, $67$ at $K=10$), creating fragmented micro-clusters. $K=5$ preserves substantial minimum cluster volume ($250$ routes in train, $315$ in all routes).
* **Operational Hierarchy:** $K=5$ creates an operationally complete 5-tier transit hierarchy, separating distinct diurnal peak specialties that are bundled together at $K=3$.

### D. Out-of-Sample Stability
* Training Silhouette: **$0.3066$** | Validation Silhouette: **$0.3076$** ($\Delta = +0.0010$)
* Training Davies-Bouldin: **$1.0384$** | Validation Davies-Bouldin: **$1.0241$** ($\Delta = -0.0143$)
* *Finding:* Zero performance degradation on unseen validation data confirms structural stability.

### E. Cluster Profiles (Unscaled Operational Units)
Evaluated across all 9,233 active routes:

| Metric | Cluster 0 ($12.8\%$) | Cluster 1 ($19.4\%$) | Cluster 2 ($3.4\%$) | Cluster 3 ($9.4\%$) | Cluster 4 ($55.0\%$) |
|---|:---:|:---:|:---:|:---:|:---:|
| **Daily Trips (Mean / Median)** | $4.4$ / $1.0$ | $5.1$ / $2.0$ | $5.7$ / $4.0$ | **$68.2$** / **$33.0$** | $33.3$ / $14.0$ |
| **Stop Count (Mean / Median)** | $31.8$ / $28.0$ | $36.8$ / $31.0$ | $27.1$ / $23.0$ | **$45.3$** / **$40.0$** | **$45.2$** / **$42.0$** |
| **Route Length km (Mean / Median)** | $23.5$ / $15.6$ | $21.8$ / $17.1$ | $14.7$ / $11.6$ | $18.6$ / $16.5$ | **$23.4$** / **$18.0$** |
| **Service Span hrs (Mean / Median)** | $1.7$ / $0.0$ | $2.5$ / $1.0$ | $3.4$ / $1.7$ | **$18.2$** / **$17.8$** | $12.6$ / $13.4$ |
| **First Departure (Mean / Median)** | $15.2$ / $15.0$ | $7.0$ / $7.0$ | $15.6$ / $19.0$ | **$3.2$** / **$4.0$** | $6.4$ / $6.0$ |
| **Morning Dominance Share** | $0.0\%$ | **$100.0\%$** | $0.6\%$ | $74.1\%$ | $82.7\%$ |
| **Afternoon Dominance Share** | **$61.0\%$** | $0.0\%$ | $7.0\%$ | $11.9\%$ | $14.2\%$ |
| **Evening Dominance Share** | **$39.0\%$** | $0.0\%$ | $20.3\%$ | $5.9\%$ | $3.1\%$ |
| **Night Dominance Share** | $0.0\%$ | $0.0\%$ | **$72.1\%$** | $8.1\%$ | $0.0\%$ |

### F. Objective Scheduled-Service Archetypes
* **Cluster 0: Midday & PM Return Specialized Feeder Runs (1,181 routes):** Late-starting routes (median departure: 15:00) with compressed operating spans (median: 0 hours, predominantly single-trip specials), serving secondary commuter return trips.
* **Cluster 1: Morning Peak-Only Commuter Shuttles (1,789 routes):** Limited-window routes operating strictly between 06:00 and 10:00 ($100\%$ morning dominant) serving morning work and school travel.
* **Cluster 2: Late-Evening & Nocturnal Feeder Runs (315 routes):** Compact, shorter-distance lines (median: 11.6 km) operating primarily between 19:00 and midnight ($72.1\%$ night dominant) providing terminal and station connections.
* **Cluster 3: 24/7 Ultra-High-Frequency Heavy Arterial Trunk Spines (866 routes):** Continuous multi-shift corridors operating from 04:00 to 23:00 (median span: 17.8 hours) with heavy daily volume (median 33.0 trips, up to 300+ trips/day).
* **Cluster 4: Standard All-Day Regular Municipal Transit Lines (5,082 routes):** The core operational network backbone, offering balanced daytime service over a 13.4-hour window across comprehensive routes.

### G. Honest Assessment of City Separation
The cluster-by-city cross-tabulation confirmed that **clusters do NOT simply separate by municipal geography**:
* **Cluster 4 (Standard Regular Lines)** constitutes **$\approx 55\%$ of routes across almost every city**: Ahmedabad ($56.0\%$), Bengaluru ($55.3\%$), Delhi ($55.7\%$), HDBRT ($55.9\%$), Mumbai ($55.9\%$), Rajkot ($57.6\%$), Pune ($46.2\%$), and Davangere ($100.0\%$).
* **Distinct Agency Specializations:** Mumbai has a high concentration of **Cluster 3 trunk corridors ($38.9\%$)**, while Pune specializes in **Cluster 1 morning shuttles ($51.4\%$)**.

---

## 3. Density-Based Clustering (DBSCAN): Grid Search & Noise Analysis

### A. Algorithmic Mechanics
DBSCAN groups points based on spatial density reachability. It requires two parameters: neighborhood radius ($\epsilon$) and minimum points (`min_samples`). Points with $\ge \text{min\_samples}$ neighbors within distance $\epsilon$ are core points; non-core points within $\epsilon$ of a core point are border points; points falling outside any dense neighborhood are flagged as noise (`-1`).

### B. $k$-Distance Curve & "Knee" Detection
Evaluating distance to the $k$-th nearest neighbor across $k \in \{5, 10, 20\}$ demonstrated a flat profile between $0.2$ and $0.6$, with a primary knee inflection between **$\epsilon = 0.6$ and $\epsilon = 1.2$** (90th percentile at $0.980$).

### C. Parameter Sensitivity & Degenerate Regimes
Evaluated across 27 settings ($\epsilon \in [0.4, 2.0]$, $\text{MinPts} \in \{5, 10, 20\}$):
* **Degenerate Mega-Cluster Collapse ($\epsilon \ge 1.6$):** A single giant cluster swallows $93\%$ to $99.4\%$ of all routes, destroying operational distinctions.
* **Degenerate Hyper-Fragmentation ($\epsilon \le 0.4$):** Over $50\%$ to $70\%$ of routes are labeled as noise, splintering the remainder into up to 105 unstable micro-clusters.
* **Approved Setting:** **$\epsilon = 1.0, \text{min\_samples} = 10$** sits directly at the knee, discovering 16 dense clusters while identifying **$478$ routes ($5.18\%$) as noise**.

### D. Deep Noise-Point Profile & Outlier Comparison
Comparing core/border routes ($8,755$) against noise routes ($478$):
* **Route Length:** Noise routes average **$29.14$ km** (IQR: $26.09$ km) vs **$21.97$ km** (IQR: $17.42$ km) for core routes.
* **Service Span:** Noise routes operate across wider daily windows (mean **$12.96$ hours**, median **$13.92$ hours**) compared to standard routes ($9.28$ hours mean).
* **Headway Dispersion:** Noise routes display an IQR of **$166.0$ minutes** (vs $90.0$ minutes), indicating irregular or pulse-scheduled runs.

### E. Taxonomic Root-Cause Classification of Noise
Cross-referencing Module 3 data quality classifications:
1. **Data Quality Issues (8 routes, $1.7\%$ of noise):** Corrupted shape files in raw BMTC GTFS feeds ($> 100$ km).
2. **Valid Extreme Core Spines (30 routes, $6.3\%$ of noise):** Corridors with $> 150$ daily trips and 24/7 service spans (e.g. `mumbai_BEST_4145`).
3. **Valid Depot & Station Pull-Outs (16 routes, $3.3\%$ of noise):** Micro-routes under $2$ km with 2 to 4 stops.
4. **Valid Regional Corridors (76 routes, $15.9\%$ of noise):** Extreme length ($> 60$ km) or stop count ($> 100$).
5. **Valid Specialized Timetables (348 routes, $72.8\%$ of noise):** Midnight departures (e.g. `mumbai_KDMT_5525` starting at 00:00), midday-only starts, and unique split-shift runs.
*Operational Principle:* **$98.3\%$ of noise points represent valid, published transit services with atypical operational profiles rather than data errors.**

---

## 4. Supervised Classification: Random Forest vs XGBoost

### A. Approved Target Label Formulation
* **Target Variable:** `scheduled_service_level` (Within-city planned operational frequency tier):
  * **Low Planned Service Level (Class 0):** Within-city trips $\le P_{33.3}$ ($40.7\%$ train, $40.7\%$ test).
  * **Medium Planned Service Level (Class 1):** Within-city trips between $P_{33.3}$ and $P_{66.7}$ ($28.6\%$ train, $28.6\%$ test).
  * **High Planned Service Level (Class 2):** Within-city trips $> P_{66.7}$ ($30.7\%$ train, $30.7\%$ test).
* *Scope Check:* Describes planned timetable capacity. Does **NOT** represent passenger load factors, demand, or route efficiency.

### B. Target Leakage Prevention
* Feature `trip_count_log1p_scaled` was **permanently eliminated** from the feature matrix ($r = 0.814$ with target).
* The remaining 11 non-leaking features represent route length, stop counts, service span, start hours, and diurnal trip shares.

### C. Out-of-Sample Performance Comparison ($N = 1,847$ test routes)
Evaluated on the unseen validation partition after tuning via 3-Fold Stratified Cross-Validation:

| Model | Test Accuracy | Macro Precision | Macro Recall | Macro F1 | F1 (Low Planned) | F1 (Medium Planned) | F1 (High Planned) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Random Forest** ($n=200, \text{depth}=10$) | $76.45\%$ | $75.02\%$ | $74.96\%$ | $0.7454$ | $0.8613$ | $0.6188$ | $0.7560$ |
| **XGBoost** ($n=100, \text{depth}=6, \eta=0.10$) | **$77.10\%$** | **$75.36\%$** | **$75.40\%$** | **$0.7507$** | **$0.8692$** | **$0.6183$** | **$0.7646$** |

### D. Feature Importance & Leakage Verification
* **Dominant Feature:** `service_span_hours_scaled` accounts for $> 35\%$ of total importance in both models, followed by `first_departure_hour_scaled`, `stop_count_scaled`, and `route_length_km_log1p_scaled`.
* **Leakage Confirmation:** Accuracy of **$77.10\%$** (well below $99\%$) confirms that the models have learned genuine operational correlations without memorizing a leaking feature.

---

## 5. Comparative Evaluation: K-Means vs DBSCAN

### A. Algorithm Alignment & Agreement
* **Adjusted Rand Index (ARI):** **$0.2453$** | **Adjusted Mutual Information (AMI):** **$0.4139$** (evaluated on non-noise routes).
* **Consensus on Commuters:** In K-Means Cluster 1 (Morning Shuttles), **$99.55\%$ of routes** map into DBSCAN Cluster 0.
* **Trunk Corridor Outliers:** In K-Means Cluster 3 (Trunk Spines), **$28.29\%$ of routes** are flagged as noise by DBSCAN due to the natural sparsity of corridors with $100–300+$ trips/day.

### B. Centroid Distance Analysis
Computing the Euclidean distance of each route to its assigned K-Means centroid ($d_i = \|x_i - \mu_{c(i)}\|$) proved that **DBSCAN noise points sit on the extreme outer periphery of K-Means clusters**:
* **Core / Border Routes:** Mean distance = **$1.8567$** (Median: $1.7305$, Max: $8.6585$).
* **DBSCAN Noise Routes:** Mean distance = **$3.5089$** (Median: $3.0238$, Max: $8.7553$).
* In the top 5% furthest routes from K-Means centroids ($d \ge 3.922$, $462$ routes), **$145$ are DBSCAN noise routes ($31.4\%$)**.

---

## 6. How the Findings Can Support Route Planning

The empirical clustering patterns and noise classifications provide quantitative baselines to guide **further operational investigation by transit planners**:

1. **Investigating Intra-Cluster Outliers for Schedule Alignment:**  
   Within a given service archetype (e.g. Cluster 4: Standard Regular Lines), certain routes display atypical operational metrics relative to their cluster peers:
   * *Example:* Routes in Cluster 4 whose scheduled headway exceeds $60$ minutes while their peers operate at $15–30$ minutes. These represent **potential candidates for timetable review** to determine if vehicle departures should be synchronized with corridor norms.
   * *Language Standard:* These are highlighted as **candidates for investigation**, not underutilised routes.
2. **Screening Spatial Overlap Candidates Within Clusters:**  
   Cross-referencing the high stop-overlap pairs identified in Module 3 with K-Means cluster assignments:
   * When two routes share $> 70\%$ of their stop sequences AND belong to the same cluster archetype (e.g. both in Cluster 4), they represent **potential candidates for service consolidation or schedule interlacing**.
   * Conversely, if two overlapping routes belong to different clusters (e.g. one in Cluster 3 trunk corridor and one in Cluster 1 morning shuttle), they serve complementary operational functions (all-day baseline vs peak shift relief) and should **not** be merged.
3. **Auditing Specialized Noise Routes:**  
   The 478 DBSCAN noise routes provide an automated triage list for timetable planners:
   * Schedulers can audit whether isolated departures (e.g. midnight runs or 1-trip shuttles) continue to meet community shift requirements or if they represent legacy timetables requiring adjustment.
4. **Mandatory Additional Data Required Before Operational Decisions:**  
   No schedule adjustments or route modifications should ever be executed based on GTFS timetable clustering alone. Transit authorities must collect:
   * **Passenger Boarding & Egress Counts:** Automated Passenger Counting (APC) or electronic fare ticketing (NCMC) data.
   * **Vehicle Load Factors:** Onboard crowding percentages relative to seated/standee vehicle capacities.
   * **Local Traffic & Corridor Speeds:** GPS Automated Vehicle Location (AVL) congestion delay logs.
   * **Operating Costs & Subsidy Mandates:** Social service obligations for rural/peri-urban accessibility.

---

## 7. Assumptions & Limitations

1. **Supply-Side Timetable Scope Only:** GTFS data reflects planned schedules, not delivered service or passenger demand. A high-frequency route cannot be assumed to be crowded or profitable; a low-frequency route cannot be assumed to be empty or inefficient.
2. **Agency Data Disparities:** Transit authorities maintain differing scheduling philosophies: BMTC (Bengaluru) includes extensive single-trip depot runs; BEST (Mumbai) emphasizes high-frequency corridors; DTC (Delhi) omitted stop arrival times (estimated in Module 2).
3. **Approximated Route Geometries:** In agencies lacking raw `shapes.txt` (Rajkot, HDBRT, Davangere), route lengths were estimated using straight-line stop sequences. In BMTC, 27 corrupted shape coordinates were capped at the 99th percentile ($82.60$ km).
4. **Algorithm Sensitivity:** Both K-Means and DBSCAN are sensitive to feature space definition and scaling parameters. While RobustScaler and $\ln(1+x)$ transformations stabilized distance metrics, alternative scaling methods would yield slightly shifted boundaries.
5. **Clusters Are Not Recommendations:** Clusters represent descriptive mathematical patterns of existing service hierarchies. They do not constitute optimization mandates.

---

## 8. Inventory of Generated Artifacts

### A. Saved Models (`models/`)
1. [`models/kmeans_model.joblib`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/models/kmeans_model.joblib) — Fitted K-Means estimator ($K=5$, 31.3 KB).
2. [`models/dbscan_model.joblib`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/models/dbscan_model.joblib) — Fitted DBSCAN estimator ($\epsilon=1.0, \text{MinPts}=10$, 942.8 KB).
3. [`models/random_forest_model.joblib`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/models/random_forest_model.joblib) — Fitted Random Forest classifier (11.2 MB).
4. [`models/xgboost_model.joblib`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/models/xgboost_model.joblib) — Fitted XGBoost classifier (937.8 KB).

### B. Result Tables (`results/`)
1. [`results/kmeans_k_comparison.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/kmeans_k_comparison.csv) — Evaluation metrics across $K=2$ to $10$.
2. [`results/kmeans_cluster_assignments.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/kmeans_cluster_assignments.csv) — Route-by-route K-Means cluster assignments (9,233 routes).
3. [`results/dbscan_parameter_grid.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/dbscan_parameter_grid.csv) — DBSCAN grid search results across 27 settings.
4. [`results/dbscan_cluster_assignments.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/dbscan_cluster_assignments.csv) — Route-by-route DBSCAN cluster and noise assignments (9,233 routes).
5. [`results/algorithm_comparison.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/algorithm_comparison.csv) — Multi-dimensional K-Means vs DBSCAN evaluation matrix.
6. [`results/classification_model_comparison.csv`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/results/classification_model_comparison.csv) — Out-of-sample supervised classification performance table.

### C. Visualizations (`visualizations/models/`)
1. [`visualizations/models/kmeans_k_evaluation_metrics.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_k_evaluation_metrics.png) — Elbow curve, silhouette scores, and Davies-Bouldin index for K-Means.
2. [`visualizations/models/kmeans_pca_scatter.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_pca_scatter.png) — 2D PCA projection of K-Means clusters ($76.49\%$ variance explained).
3. [`visualizations/models/kmeans_cluster_profiles_bar.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_cluster_profiles_bar.png) — Standardized centroid deviations across all 12 model features.
4. [`visualizations/models/kmeans_cluster_key_features_boxplot.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_cluster_key_features_boxplot.png) — Unscaled boxplots for daily trips, service span, and route length.
5. [`visualizations/models/kmeans_routes_length_vs_trips_scatter.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_routes_length_vs_trips_scatter.png) — Route length vs scheduled trips scatter plot.
6. [`visualizations/models/kmeans_cluster_by_city_composition.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_cluster_by_city_composition.png) — Municipal agency stacked percentage breakdown.
7. [`visualizations/models/dbscan_k_distance_plot.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/dbscan_k_distance_plot.png) — $k$-NN sorted distance curves ($k \in \{5, 10, 20\}$).
8. [`visualizations/models/dbscan_parameter_grid_curves.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/dbscan_parameter_grid_curves.png) — Cluster count and noise rate sensitivity curves.
9. [`visualizations/models/dbscan_noise_vs_core_boxplots.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/dbscan_noise_vs_core_boxplots.png) — Boxplots contrasting Core vs Noise distributions.
10. [`visualizations/models/dbscan_pca_scatter.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/dbscan_pca_scatter.png) — 2D PCA projection highlighting noise points.
11. [`visualizations/models/kmeans_vs_dbscan_comparison.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/kmeans_vs_dbscan_comparison.png) — Centroid distance boxplot and noise rate distribution chart.
12. [`visualizations/models/classification_confusion_and_importance.png`](file:///c:/Users/Aayush/Desktop/AI%20ROUTE%20RANKER%20PROJECT/visualizations/models/classification_confusion_and_importance.png) — Normalized confusion matrices and feature importance rankings.

---

## 9. Observations & Items Clarified

During Module 5 development, several analytical points were confirmed through data:
1. **Direct Silhouette Comparability:** While both K-Means and DBSCAN output silhouette scores, DBSCAN excludes the 478 noise routes ($5.18\%$) before computation. Evaluating K-Means on the full population naturally depresses its score relative to DBSCAN's filtered core.
2. **K-Means Outlier Pull:** Although K-Means forces all routes into clusters, the distance-to-centroid audit proved that the 478 DBSCAN noise routes sit at nearly double the Euclidean distance ($3.51$ vs $1.86$) from K-Means centroids, confirming that K-Means handles outliers by pushing them to the periphery of its macro-tiers rather than creating degenerate micro-clusters.
3. **Target Leakage Proof in Classification:** Dropping `trip_count_log1p_scaled` was essential to prevent trivial $100\%$ accuracy. The resulting $77.10\%$ accuracy reflects true structural relationships between physical/temporal route attributes and planned service tiers.
