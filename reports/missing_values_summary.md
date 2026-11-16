# RouteRanker Module 4: Missing Values Summary Report

**Project:** AI-Based Public Transit Route Optimization for Indian Cities (RouteRanker)  
**Dataset:** 8 Indian Transit Networks (`Ahmedabad`, `Bengaluru`, `Davangere`, `Delhi`, `HDBRT`, `Mumbai`, `Pune`, `Rajkot`)  
**Input Dataset:** `processed/route_features.csv` (9,915 routes)  
**Deliverable CSV:** `reports/missing_values_summary.csv`  
**Isolated Catalog:** `processed/unserved_routes_catalog.csv` (682 routes)

---

## 1. Overview of Missing Data Investigation

In strict adherence to **Rule 2** (context-aware investigation; no blind zero-filling), every column in `processed/route_features.csv` was audited overall and broken down across all 8 transit agencies. Cross-referencing against raw GTFS feeds (`routes.txt`, `routes.csv`, `trips.txt`, `stop_times.txt`) established that missingness is not random noise, but maps to three distinct structural mechanisms:

1. **Agency Data Feed Structure:** The Delhi Transport Corporation (DTC) open-data feed omits `route_short_name` entirely.
2. **Unserved Agency Catalog Routes:** Transit authorities published route entries in `routes.txt` with zero associated scheduled trips in `trips.txt`.
3. **Mathematical Definition Limits:** Headway requires at least two departures in the same direction ($\Delta t = t_2 - t_1$). Routes with only one departure across the day or per direction cannot have a calculable headway.

Zero records exhibited missingness due to corrupted database writes or unknown causes.

---

## 2. Missing Values by Feature and Agency

| Feature / Column Name | Total Missing | Pct (%) | Primary Cities Affected | Ground-Truth Root Cause |
|---|---:|---:|---|---|
| **`route_short_name`** | 1,270 | 12.81% | **Delhi (1,270 / 1,270 = 100%)** | Delhi DTC feed omits `route_short_name` and embeds route codes in `route_long_name`. All other 7 cities have 0% missing. |
| **`trip_count`** | 682 | 6.88% | Mumbai (494), Delhi (83), Davangere (79), Bengaluru (18), Ahmedabad (6), HDBRT (2) | Official catalog routes with 0 scheduled trips in `trips.txt`. |
| **`stop_count`** | 682 | 6.88% | Same 682 routes as above | Zero trips scheduled; no stop visits exist in `stop_times.txt`. |
| **`route_length_km`** | 682 | 6.88% | Same 682 routes as above | Zero stops or shapes associated with unserved catalog routes. |
| **Diurnal Window Counts (4 cols)** | 682 | 6.88% | Same 682 routes as above | Zero trips scheduled in any departure window. |
| **Calendar Trip Counts (2 cols)** | 682 | 6.88% | Same 682 routes as above | Zero trips scheduled on weekdays or weekends. |
| **Service Timing (3 cols)** | 682 | 6.88% | Same 682 routes as above | No first/last departure hour or service span can exist without trips. |
| **`median_headway_min`** | 3,015 | 30.41% | Bengaluru (1,947), Mumbai (507), HDBRT (196), Ahmedabad (100), Delhi (94), Rajkot (81), Davangere (79), Pune (11) | • 682 unserved catalog routes (0 trips)<br>• 1,447 single-trip routes (`trip_count == 1`)<br>• 886 directional single-trip routes in Bengaluru (`trip_count == 2`, 1 outbound + 1 inbound) |

---

## 3. Detailed City Breakdown of Missing Values

| City | Total Routes | `route_short_name` | Unserved Routes (12 Operational Features) | Headway: Single-Trip (`trip_count == 1`) | Headway: Single-Dir (`trip_count == 2`) | Total Headway Missing |
|---|---:|---:|---:|---:|---:|---:|
| **Ahmedabad** | 978 | 0 | 6 | 94 | 0 | 100 |
| **Bengaluru** | 4,434 | 0 | 18 | 1,043 | 886 | 1,947 |
| **Davangere** | 93 | 0 | 79 | 0 | 0 | 79 |
| **Delhi** | 1,270 | 1,270 | 83 | 11 | 0 | 94 |
| **HDBRT** | 632 | 0 | 2 | 194 | 0 | 196 |
| **Mumbai** | 1,609 | 0 | 494 | 13 | 0 | 507 |
| **Pune** | 628 | 0 | 0 | 11 | 0 | 11 |
| **Rajkot** | 271 | 0 | 0 | 81 | 0 | 81 |
| **TOTAL** | **9,915** | **1,270** | **682** | **1,447** | **886** | **3,015** |

---

## 4. Remediation Methods Applied & Operational Justifications

The remediation strategy corresponds to the log stored in `reports/missing_values_summary.csv`:

### A. Line Identifier Remediation (`route_short_name`)
* **Method Used:** In the metadata lookup table (`processed/route_lookup_*.csv`), missing `route_short_name` values for Delhi routes were populated by copying `route_long_name`.
* **Count Affected:** 1,270 routes (1,187 active routes, 83 unserved routes).
* **Justification:** Delhi DTC embeds public route code strings (e.g. `193STLDOWN`, `827LNKSTLUP`) directly in `route_long_name`. Copying it ensures route inspection tables have an intuitive line code. Furthermore, per **Rule 3**, `route_short_name` is an identifier and is strictly excluded from machine learning distance calculations.

### B. Unserved Agency Catalog Routes (12 Operational Features)
* **Method Used:** Isolated all 682 unserved catalog routes into `processed/unserved_routes_catalog.csv` with their original identifiers, agency metadata, and Module 3 audit flags preserved. Active service clustering is performed on the remaining **9,233 active routes**.
* **Count Affected:** 682 routes.
* **Justification:** Imputing zeros (0 trips, 0 stops, 0 km) into distance-based algorithms (KMeans/DBSCAN) causes all 682 routes to collapse into an artificial $(0,0,\dots,0)$ coordinate, forcing clustering models to dedicate an entire cluster to non-existent lines and distorting silhouette scores. Isolating them into an agency catalog preserves complete data provenance without polluting active service clustering.

### C. Missing Headway on Active Routes (`median_headway_min`)
* **Method Used:** Approved Option A. Excluded `median_headway_min` from the primary Euclidean distance matrix. Service capacity and operational intensity are represented via **`trip_count`** (which has 0 missing values across all active routes) and normalized **diurnal trip shares** (`morning_trip_share`, `evening_trip_share`, `night_trip_share`). Added explicit boolean indicator column `is_headway_missing` to the route lookup.
* **Count Affected:** 2,333 active routes (1,447 single-trip routes + 886 directional single-trip routes in Bengaluru).
* **Justification:** Zero-filling headway is strictly forbidden by **Rule 2** (a 0-minute headway implies buses arrive infinitely frequently). Median imputation (~30 minutes) falsely informs models that once-daily buses arrive every 30 minutes. Representing cadence via total daily trips and diurnal shares bypasses mathematical singularity while maintaining 100% operational fidelity.

### D. Corrupted GIS Shape Trajectory Spikes (`route_length_km`)
* **Method Used:** Capped at the training partition 99th percentile upper bound ($82.6022$ km), fitted strictly on `train_df` and applied to `val_df`.
* **Count Affected:** 27 BMTC routes in Bengaluru (routes jumping up to 10,466 km).
* **Justification:** In compliance with **Rule 6** (no automatic outlier deletion), these routes are valid operational services with real trips and stops, but suffered from GPS coordinate jumps in the agency's raw `shapes.txt`. Capping at the 99th percentile eliminates distance distortion in clustering while keeping all 27 routes in the dataset.

---

## 5. Verification of Zero Blind Zero-Filling

In strict adherence to **Rule 2**:
* Zero was **never** substituted for missing `median_headway_min`.
* Zero was **never** substituted for missing `service_span_hours`, `trip_count`, or `stop_count` to force unserved routes into active clustering.
* Where zeros exist in the final model matrix (e.g. `night_trip_share = 0.0`), they reflect genuine physical operational truth: transit routes that have zero scheduled departures during late-night hours (21:00 to 04:59).
