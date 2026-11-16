# RouteRanker Module 4: Comprehensive Data Preprocessing Technical Report

**Project:** AI-Based Public Transit Route Optimization for Indian Cities (RouteRanker)  
**Scope:** Preprocessing for Unsupervised Machine Learning (KMeans, DBSCAN) and Transit Archetype Discovery  
**Coverage:** 8 Indian Municipal Transit Networks (`Ahmedabad`, `Bengaluru`, `Davangere`, `Delhi`, `HDBRT`, `Mumbai`, `Pune`, `Rajkot`)  
**Input Data:** `processed/route_features.csv` (9,915 routes) & `processed/route_features_flagged.csv` (9,915 routes)  
**Notebook:** `module4_preprocessing.ipynb` (69 executed cells)

---

## 1. Executive Summary

Module 4 establishes an end-to-end, leakage-free preprocessing pipeline designed to prepare multi-city Indian transit schedule data for unsupervised clustering models (KMeans and DBSCAN) and downstream latent archetype discovery.

Starting from **9,915 routes** across 8 cities, the pipeline:
1. Audited feature schemas and isolated **682 unserved catalog routes** into `processed/unserved_routes_catalog.csv`.
2. Evaluated mathematical redundancies, collinear relationships, and geographic confounding risks across all 20 master features.
3. Formulated an orthogonal **12-dimensional feature matrix** capturing service scale, physical geometry, temporal coverage, and diurnal peaking.
4. Established an 80:20 stratified train/validation split (**7,386 train routes / 1,847 validation routes**) preserving municipal agency balance across all 8 transit systems.
5. Capped 27 corrupted BMTC GPS shape spikes at the training 99th percentile ($82.60$ km) and applied `np.log1p` to heavily skewed features.
6. Fitted `RobustScaler` (median & IQR) and `OneHotEncoder` strictly on training data, transforming validation data with zero leakage.
7. Serialized all preprocessed datasets, lookup tables, and fitted pipeline artifacts to `processed/` and `processed/pipeline/` for future Streamlit deployment.

---

## 2. Feature Selection: Inclusions, Exclusions, and Operational Rationale

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FEATURE ARCHITECTURE SUMMARY                    │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Metadata & Identifiers Lookup (Excluded from Model Matrix — Rule 3) │
│    • route_id (Primary Key)           • route_long_name                │
│    • city (Municipal authority)       • length_method                  │
│    • original_route_id (Raw ID)       • operating_days                 │
│    • route_short_name (Line code)     • All Module 3 Audit Flags       │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Excluded Redundant Features (Collinear / Mathematically Linked)     │
│    • trips_weekday (100% duplicate of trip_count, r = 1.000)           │
│    • trips_weekend (100% duplicate of trip_count, r = 1.000)           │
│    • last_departure_hour (Collinear with first_hour + span, r = 0.962) │
│    • Raw period counts (Sum to trip_count; replaced by shares)         │
│    • median_headway_min (Excluded from distance matrix; Option A)      │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Final 12-Dimensional Modeling Feature Matrix (X_train, X_val)       │
│    • trip_count_log1p_scaled          • period_afternoon (One-Hot)     │
│    • stop_count_scaled                • period_evening (One-Hot)       │
│    • route_length_km_log1p_scaled     • period_morning (One-Hot)       │
│    • service_span_hours_scaled        • period_night (One-Hot)         │
│    • first_departure_hour_scaled      • morning_trip_share_scaled      │
│    • evening_trip_share_scaled        • night_trip_share_scaled        │
└────────────────────────────────────────────────────────────────────────┘
```

### A. Features Selected for Modeling:
1. **`trip_count_log1p_scaled`:** Captures total daily vehicle resource allocation. Transformed via `np.log1p` to contract heavy positive skewness (skewness reduced from $+3.71$ to $+0.54$).
2. **`stop_count_scaled`:** Measures boarding density, stopping frequency, and passenger accessibility. Distinguishes stop-dense local stopping routes from limited-stop express corridors.
3. **`route_length_km_log1p_scaled`:** Measures physical spatial coverage. Capped at training 99th percentile ($82.60$ km) and log-transformed to eliminate extreme shape spike distortion (skewness reduced from $+88.83$ to $-0.35$).
4. **`service_span_hours_scaled`:** Measures operating longevity across the day (0.0 to 24.0 hours). Distinguishes all-day comprehensive corridors from short peak-only commute shuttles.
5. **`first_departure_hour_scaled`:** Captures service inception timing, separating early-morning industrial/workman runs from standard midday services.
6. **Diurnal Proportional Shares (`morning_trip_share`, `evening_trip_share`, `night_trip_share`):**
   Ratios ($\text{trips\_period} / \text{trip\_count}$) capturing diurnal peaking profiles independent of route scale ($r \approx -0.10$ to $0.07$ with total trips).
7. **One-Hot Encoded Dominant Time Period (`period_afternoon`, `period_evening`, `period_morning`, `period_night`):**
   Orthogonal binary indicators representing the primary operational service orientation.

### B. Features Excluded from Modeling:
1. **`trips_weekday` & `trips_weekend`:** Dropped because both are **100% identical** to `trip_count` across all 9,233 active routes ($r = 1.000$, $\max |\text{diff}| = 0.0$). Retaining them would triple-weight total trip volume in Euclidean distance calculations.
2. **`last_departure_hour`:** Dropped because it is collinear with $\text{first\_departure\_hour} + \text{service\_span\_hours}$ ($r = 0.962$).
3. **Raw Period Counts (`trips_morning`, `trips_afternoon`, etc.):** Excluded because their sum equals `trip_count` by definition, creating severe multicollinearity ($r = 0.78$ to $0.97$).
4. **`median_headway_min`:** Excluded from the distance matrix under approved Option A to avoid mathematical singularity on the 2,333 single-trip/single-direction routes where consecutive departures do not exist. Preserved in metadata lookup for auxiliary evaluation.
5. **`city`:** Excluded from the model matrix to prevent artificial geographic segregation. One-hot encoding city would penalize routes from different municipalities by a fixed distance $\sqrt{2} \approx 1.414$, causing KMeans to cluster by administrative city rather than transit operational behavior.

---

## 3. Preprocessing Decisions and Methodological Justifications

1. **Isolation of 682 Unserved Catalog Routes:**
   Routes published in agency `routes.txt` but with zero scheduled trips in `trips.txt` were separated into `processed/unserved_routes_catalog.csv`. Active clustering is performed strictly on active services, eliminating 100% of missing values across operational features without artificial zero-filling.
2. **Delhi Line Identifiers Standardized:**
   In the metadata lookup, missing `route_short_name` values for Delhi routes were populated from `route_long_name`.
3. **Capping Corrupted BMTC Shape Trajectories (Rule 6):**
   Rather than deleting the 27 BMTC routes with GPS coordinate spikes (jumping up to 10,466 km), their trajectory length was capped at the training 99th percentile ($82.60$ km). All valid operational services were preserved.
4. **One-Hot Encoding for Nominal Time Periods:**
   One-Hot Encoding was selected over Label Encoding to avoid imposing a false linear ordering (e.g. night > morning) that would distort Euclidean distance.
5. **Robust Scaling (`RobustScaler`):**
   Numerical features were centered by their median and scaled by their Interquartile Range (IQR). This ensures that valid-but-unusual services (depot shuttles, long regional loops) do not compress the scale of standard transit routes.
6. **Strict Train-Only Fitting (Rule 5):**
   All capping thresholds, scaling statistics, and one-hot categories were fitted strictly on `train_df` (7,386 routes) and applied to `val_df` (1,847 routes) to guarantee zero data leakage.

---

## 4. Key Assumptions

1. **Timetable Faithfulness:** Published GTFS files are assumed to represent the planned service intent of municipal transit authorities during the respective collection periods.
2. **Spatial Approximation Validity:** Straight-line Haversine stop-to-stop distances are assumed to provide a consistent, rank-preserving approximation of route trajectory length for cities lacking `shapes.txt`.
3. **Directional Separation:** Bus trips operating in opposite directions are assumed to belong to separate passenger-service streams for headway calculations.
4. **Operational Uniformity:** 7-day timetable representations are assumed to reflect standard weekly scheduling policies published by Indian municipal bus agencies.

---

## 5. Technical Limitations (Rule 1 Adherence)

1. **Scheduled Supply Only (No Ridership):**
   The dataset contains planned vehicle supply only. It contains **no passenger boarding counts, farebox revenues, tap-in/tap-out smart card records, or GPS vehicle location logs**. High trip counts prove service supply, not passenger demand.
   *No route is confirmed as overcrowded, balanced, underutilised, or inefficient.*
2. **Heterogeneous Data Feeds Across Cities:**
   Transit agencies differ in data sophistication: Bengaluru and Pune publish high-resolution GIS shape traces (`shapes.txt`), whereas Ahmedabad, Delhi, Mumbai, HDBRT, Rajkot, and Davangere provide stop coordinates only.
3. **Approximated Route Lengths:**
   Route lengths for cities without shapes represent straight-line stop sequences (`haversine_stops`), which underestimate actual road network curvature by approximately 15% to 25% (circuity factor).
4. **Undefined Headway on Low-Frequency Services:**
   Headway is mathematically undefined for routes with $\le 1$ trip per direction. Total daily trips and diurnal shares serve as proxies for operational intensity.

---

## 6. Engineering Challenges Encountered & Resolutions

| Challenge Encountered | Technical Impact | Engineering Resolution |
|---|---|---|
| **OS-Level Windows Code Integrity Block** | System reboot triggered Smart App Control / WDAC State 1, blocking unsigned wheel `.pyd` files installed under `AppData\Local`. | Configured and executed all notebook processing via the verified standalone CPython 3.14 environment at `AppData\Roaming\uv\python\`, which passed integrity checks. |
| **Delhi Route Code Omission** | Delhi DTC published 1,270 routes with `route_short_name` as 100% NaN. | Verified that Delhi embeds line codes inside `route_long_name`. Populated metadata lookup from `route_long_name`. |
| **Catalog Ghost Routes** | 682 routes in agency feeds contained 0 scheduled trips, producing missing values across all operational metrics. | Verified exact match against raw GTFS feeds. Isolated routes into `processed/unserved_routes_catalog.csv` without zero-filling. |
| **BMTC GPS Coordinate Jumps** | 27 Bengaluru routes exhibited trajectory lengths up to 10,466 km due to corrupted raw shape points. | Preserved routes per Rule 6; capped length at training 99th percentile ($82.60$ km) and stabilized via `np.log1p`. |
| **Headway Singularity on Single Trips** | 2,333 active routes had undefined headway due to lack of consecutive departures. | Excluded headway from primary distance matrix; represented operational intensity via `trip_count` and diurnal shares. |

---

## 7. Deliverables & Data Integrity Summary

All deliverables have been saved to `processed/`, `processed/pipeline/`, and `reports/`:
* **Preprocessed Datasets:** `route_features_preprocessed_train.csv` (7,386 × 14), `route_features_preprocessed_val.csv` (1,847 × 14), `route_features_preprocessed_all.csv` (9,233 × 14).
* **Pure Model Matrices:** `X_train.csv` (7,386 × 12), `X_val.csv` (1,847 × 12), `X_all.csv` (9,233 × 12).
* **Metadata Lookups:** `route_lookup_train.csv` (7,386 × 11), `route_lookup_val.csv` (1,847 × 11), `route_lookup_all.csv` (9,233 × 8).
* **Catalog Dataset:** `unserved_routes_catalog.csv` (682 × 30).
* **Serialized Pipeline:** `feature_scaler.joblib`, `one_hot_encoder.joblib`, `length_cap.json`, `feature_list.json`.
* **Reports:** `missing_values_summary.md`, `encoding_and_scaling_documentation.md`, `train_validation_strategy.md`, `preprocessing_report.md`.

*Automated Audit Outcome:* **100% Clean. Zero missing values (`NaN = 0`), zero infinite values (`Inf = 0`), zero overwritten raw files.**
