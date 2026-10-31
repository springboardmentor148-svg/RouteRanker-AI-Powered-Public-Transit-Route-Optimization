# Data Quality and Outlier Investigation Report (Module 3 EDA)

## Executive Summary
This document provides a comprehensive inventory of data quality checks, structural anomalies, and statistical outliers identified across the **9,915 route profiles** and **8 Indian public transit networks** in the RouteRanker project (Ahmedabad, Bengaluru, Davangere, Delhi, HDBRT, Mumbai, Pune, Rajkot).

In accordance with **Project Governance Rule 3**, no rows or routes were deleted or silently modified. All routes remain preserved in `processed/route_features.csv`, with audit flags and root-cause classifications recorded in `processed/route_features_flagged.csv`.

---

## 1. Summary of Data Quality Issues, Root Causes, and Actions Taken

| Issue Identified | Affected City / Network | Route Count | Root-Cause Classification | Action Taken | Technical Explanation & Context |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Unserved Catalog Routes** | Mumbai (494), Delhi (83), Davangere (79), Bengaluru (18), Ahmedabad (6), HDBRT (2) | 682 | Source-Data Limitation | Flagged (`is_unserved_route = True`), kept in inventory | Routes cataloged in `routes.txt` with zero scheduled trips in `trips.txt` during feed period. Excluded from correlation calculations. |
| **Corrupted Shape Trajectories** | Bengaluru (`shapes.txt`, e.g. `V-360B FLY DOWN`) | 27 | Data Error / Raw Feed Corruption | Flagged (`is_corrupted_shape = True`), kept in inventory | Raw coordinate points rapidly oscillate back and forth 1,468 times between terminal points, accumulating up to 10,466 km of synthetic length. |
| **Extremely Short Micro-Routes (< 0.5 km)** | Bengaluru (66), HDBRT (2) | 68 | Valid but Unusual / Operational Outlier | Flagged (`is_extreme_length_short = True`), kept | Micro-routes serving 2–5 stops between adjacent terminal platforms, depot gates, or junction turnarounds. |
| **Extended Peri-Urban Loops (> 150 km)** | Ahmedabad (AMTS) | 12 | Valid but Unusual / Operational Outlier | Flagged (`is_extreme_length_long = True`), verified, kept | Long-distance intercity/peri-urban loops connecting outlying industrial estates (Sanand, Bavla) with 71–90 stops. Verified valid. |
| **High-Frequency Corridor Trunks (≥ 100 trips/day)** | Mumbai (266), Delhi (156), Ahmedabad (60), Rajkot (24), Bengaluru (8), HDBRT (4) | 518 | Valid but Unusual / Operational Outlier | Flagged (`is_high_frequency_trunk = True`), kept | Core arterial corridors and railway station feeders carrying heavy commuter volumes with 2–5 minute headways (up to 573 trips/day). |
| **Single-Trip Special Services (== 1 trip/day)** | Bengaluru (1,043), HDBRT (194), Ahmedabad (94), Rajkot (81), Mumbai (13), Delhi (11), Pune (11) | 1,447 | Valid but Unusual / Operational Outlier | Flagged (`is_single_trip_special = True`), kept | Specialized operational runs: depot pull-out/pull-in deadhead trips, early morning factory shuttles, or student specials. |
| **Next-Day Trips (Hours ≥ 24:00)** | Delhi, Mumbai, Ahmedabad, Bengaluru | ~2.1% of raw trips | GTFS Standard Specification | Standardized in Module 2 | Standard GTFS representation of trips starting after midnight on the previous operational service day. Service spans properly bounded. |
| **Coordinate Bounds & Validity** | All 8 Cities (37,649 stops) | 0 invalid | Verified Clean | None needed | 100% of physical transit stops have valid coordinates strictly within India's bounding box [6.0°N–37.5°N, 68.0°E–97.5°E]. |
| **Duplicate Records & Identifiers** | All 8 Cities (9,915 routes) | 0 duplicates | Verified Clean | None needed | Zero duplicate rows; `route_id` serves as a perfectly unique primary key. |

---

## 2. City-Specific IQR Outlier Analysis

Outlier detection was performed using the Interquartile Range (IQR) rule independently per city:
$$\text{Lower Bound} = \max(0, Q_1 - 1.5 \times \text{IQR})$$
$$\text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$

### Outlier Findings by Dimension:
1. **Trip Count (`trip_count`)**:
   - Outliers are heavily concentrated on the upper tail (high-frequency corridors).
   - In **Mumbai**, the upper IQR bound is 250.5 trips; 66 routes exceed this bound, reaching up to 573 trips per day.
   - In **Bengaluru**, the upper IQR bound is 17.0 trips; 591 routes exceed this bound, reflecting a massive long-tail frequency distribution.
2. **Stop Count (`stop_count`)**:
   - Outliers represent extended peripheral circular routes, led by **Bengaluru** (18 routes > 143.5 stops, max 184 stops) and **Mumbai** (4 routes > 84 stops, max 147 stops).
3. **Route Length (`route_length_km`)**:
   - In **Bengaluru**, 107 routes exceed the upper bound (58.4 km), of which 27 routes exceed 200 km due to raw shape trajectory corruption in `shapes.txt`.
   - In **Ahmedabad**, 123 routes exceed the upper bound (58.8 km), representing valid extended peri-urban routes connecting industrial growth centers.
4. **Service Span (`service_span_hours`)**:
   - Outliers in **Mumbai** (41 routes) and **Pune** (20 routes) capture routes with very short operating spans (1.0 to 3.0 hours), characteristic of morning-only or late-night special services.

---

## 3. Why Outliers Must NOT Be Removed Automatically

In transportation data science and public transit optimization, **automatically deleting statistical outliers is a severe methodological flaw**:

1. **Destruction of Network Hierarchy**:
   - High-frequency routes (e.g., BEST Route 182 with 451 trips, or Route 203 with 573 trips) carry the highest passenger volumes in the city. Discarding them because they exceed the statistical IQR threshold would eliminate the core backbone of the transit network, leaving an analysis biased toward low-demand services.
2. **Operational Reality of Micro and Single-Trip Services**:
   - Routes with 1 scheduled trip or lengths under 0.5 km are not data entry errors. They reflect real vehicle movements: buses departing depots to reach terminal origins, late-night hospital/factory runs, or short-turn station loops. Deleting them distorts vehicle fleet balancing and scheduling constraints in Module 5.
3. **Distinction Between Data Errors and Operational Extremes**:
   - Outliers fall into fundamentally different categories. While Bengaluru's 10,466 km shape trajectory is a genuine measurement error in the feed requiring a length recalculation flag, a 170 km peri-urban loop in Ahmedabad is an authentic physical service. Automatic truncation fails to distinguish between corrupt measurements and genuine operational diversity.
4. **Machine Learning Integrity (Module 4)**:
   - For downstream predictive modeling and ranking algorithms, extreme operational values should be managed through **rank-based metrics (Spearman), log transformations, robust loss functions (Huber loss), or stratified modeling (segmenting trunks from feeders)** rather than arbitrary sample deletion.

---

## 4. Preserved and Flagged Datasets
- Clean Baseline: `processed/route_features.csv` (all 9,915 routes preserved).
- Quality-Flagged Copy: `processed/route_features_flagged.csv` (contains 10 boolean audit flags and `data_quality_classification`).
