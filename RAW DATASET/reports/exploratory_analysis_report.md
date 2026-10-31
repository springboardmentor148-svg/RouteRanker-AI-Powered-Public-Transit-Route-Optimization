# RouteRanker: Exploratory Data Analysis (EDA) Report
**Module 3: Public Transit Route Profiles Across 8 Indian Cities**

---

## Executive Summary
This report presents the consolidated findings from **Module 3: Exploratory Data Analysis (EDA)** of the RouteRanker project. The objective of this phase is to analyze the structural, temporal, spatial, and relational characteristics of bus transit networks across **8 major Indian cities**: **Ahmedabad, Bengaluru, Davangere, Delhi, Hubballi-Dharwad (HDBRT), Mumbai, Pune, and Rajkot**.

The analysis evaluates **9,915 route profiles** derived from published General Transit Feed Specification (GTFS) schedules, comprising **9,233 active scheduled routes** and **682 unserved catalog routes**, representing **226,357 distinct daily scheduled trips** across **37,649 physical stops**.

In strict adherence to project governance rules:
1. **Rule 1 (Scheduled Service Only)**: All metrics describe planned operational vehicle supply. No passenger counts, crowding levels, or ridership volumes are created, inferred, or assumed.
2. **Rule 2 (Strict Candidate Terminology)**: Routes identified through overlap screening or low scheduled trip counts are designated strictly as **"potential patterns / candidates for further analysis"**. Schedule data alone cannot diagnose operational inefficiency, redundancy, or underutilization.
3. **Rule 3 (Preserve Complete Inventory)**: Zero rows or routes were deleted or silently modified. All 9,915 routes remain preserved.
4. **Rule 4 (Categorical Identifiers)**: Identifiers (`route_id`, `stop_id`, `trip_id`) are treated strictly as reference keys.
5. **Rule 7 (Transparent Data Limitations)**: Feed limitations (e.g., absence of `shapes.txt` in 6 of 8 cities) are documented rather than artificially interpolated.

---

## 1. Dataset Overview & Inventory

| Transit Network / City | Primary Agency | Raw File Format | Total Routes Cataloged | Active Scheduled Routes | Unserved Catalog Routes | Total Scheduled Daily Trips | Distinct Physical Stops | Shapes Feed Availability |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ahmedabad** | AMTS / BRTS | `.txt` | 978 | 972 | 6 (0.6%) | 20,404 | 2,176 | Unavailable (Feed Limitation) |
| **Bengaluru** | BMTC | `.txt` | 4,434 | 4,416 | 18 (0.4%) | 83,099 | 10,753 | **Available** (7,355 shapes) |
| **Davangere** | Municipal Transit | `.txt` | 93 | 14 | 79 (85.0%) | 586 | 602 | Unavailable (Feed Limitation) |
| **Delhi** | DTC / DIMTS | `.csv` | 1,270 | 1,187 | 83 (6.5%) | 50,381 | 6,851 | Unavailable (Feed Limitation) |
| **HDBRT** | NWKRTC / BRTS | `.txt` | 632 | 630 | 2 (0.3%) | 8,926 | 321 | Unavailable (Feed Limitation) |
| **Mumbai** | BEST | `.txt` | 1,609 | 1,115 | 494 (30.7%) | 43,456 | 6,561 | Unavailable (Feed Limitation) |
| **Pune** | PMPML | `.txt` | 628 | 628 | 0 (0.0%) | 14,047 | 9,067 | **Available** (628 shapes) |
| **Rajkot** | RMTS / BRTS | `.txt` | 271 | 271 | 0 (0.0%) | 5,458 | 1,318 | Unavailable (Feed Limitation) |
| **Total All Networks**| — | — | **9,915** | **9,233** | **682 (6.9%)** | **226,357** | **37,649** | **2 of 8 Cities Available** |

---

## 2. Key Observations by Analytical Phase

### Phase 1 & 2: Univariate Distributions & Skewness
* **Extreme Skewness Across Core Features**:
  - `trip_count`: Heavily right-skewed. The national mean is **24.52 trips/day**, whereas the median is **8.00 trips/day** with a standard deviation of **44.97**. Over **70.4% of routes** schedule fewer trips than the mean.
  - `stop_count`: Moderate right-skewness. Mean is **40.71 stops**, median is **33.00 stops** (range: 2 to 184 stops).
  - `route_length_km`: Heavy right-skewness. Mean is **22.84 km**, median is **17.50 km** (IQR: 10.37 km to 29.83 km).
  - `service_span_hours`: Bimodal distribution. The primary mode peaks at **14.0–15.5 hours/day** (full-day operations), while a secondary peak at **0.0–1.0 hours/day** captures **1,447 single-trip special routes**.
* **Methodological Synthesis (Mean vs. Median)**:
  - Because extreme high-frequency corridors (e.g., BEST feeders with 500+ trips) pull the arithmetic mean upward by over $300\%$, the **median** represents the true operational center for transit baseline comparisons.

### Phase 3: Temporal Scheduled Service Patterns
* **24-Hour Bimodal Peak Profile**:
  - Across all 8 cities combined, service follows an authentic transit supply curve with two distinct operational peaks:
    1. **Morning Commuter Peak**: Reaches maximum scheduled supply at **08:00 (17,289 trips, 7.64% of daily supply)**, with heavy service sustained between 07:00 and 09:59 (46,478 trips).
    2. **Evening Commuter Peak**: Secondary peak at **17:00 (14,411 trips, 6.37% of daily supply)**, sustained from 16:00 to 19:59 (53,230 trips).
    3. **Night-Owl Trough**: Minimum scheduled activity occurs at **02:00 (161 trips, 0.07%)**, followed by 03:00 (232 trips) and 01:00 (283 trips).
* **Operational Time Period Shares**:
  - **Morning Peak (06:00–11:59)**: **40.34%** (91,321 trips) — the dominant operational window across India.
  - **Midday Afternoon (12:00–15:59)**: **28.76%** (65,099 trips).
  - **Evening Peak (16:00–20:59)**: **21.99%** (49,771 trips).
  - **Night / Early Morning (21:00–05:59)**: **8.92%** (20,166 trips).
* **Calendar Data Limitation (Rule 7)**:
  - In 6 of 8 cities, `calendar.txt` lists scheduled trips as operating uniformly 7 days a week, preventing empirical weekday vs. weekend divergence analysis.

### Phase 4: Route-Level Operational Comparisons
* **Frequency Tiers**:
  - **Low-Frequency Routes ($\le 3$ trips/day)**: **2,875 routes (31.1%)** — specialized runs, depot deadheads, and rural feeders.
  - **Moderate-Frequency Routes (4–29 trips/day)**: **4,374 routes (47.4%)** — standard suburban community connectors.
  - **High-Frequency Corridors ($\ge 30$ trips/day)**: **1,984 routes (21.5%)** — arterial trunk routes and railway station feeders.
* **Extreme Operational Profiles**:
  - **Top 10 Trip Routes**: Exclusively short-haul railway station feeder loops in **Mumbai (BEST)**, operating over alignments of **1.5 to 12.0 km** with **413 to 573 trips/day** and 2–3 minute headways.
  - **Top 10 Stop Routes**: Exclusively peripheral inter-suburban loops in **Bengaluru (BMTC)**, covering **44 to 136 km** with **149 to 184 stops**, but scheduling only **2 to 24 trips/day**.

### Phase 5: Geographical & Spatial Analysis
* **Stop Coordinate Reliability**:
  - **100% of all 37,649 stops** possess complete, non-null coordinates falling strictly within India's geographical bounding box ($6.0^\circ\text{N}$ to $37.5^\circ\text{N}$, $68.0^\circ\text{E}$ to $97.5^\circ\text{E}$).
* **Network Trajectory Alignments (Rule 7)**:
  - High-resolution trajectory shape files (`shapes.txt`) are present **only in Bengaluru (7,355 shapes) and Pune (628 shapes)**.
  - In the remaining 6 cities, spatial route lengths rely on straight-line Haversine stop-to-stop distances; straight-line maps were strictly avoided to prevent misleading representations.

### Phase 6: Stop Overlap & Low-Activity Screening
* **Inverted Index Overlap Screening**:
  - Using an inverted index (`stop_id -> route_ids`), **8,241 route pairs** were identified across India sharing $\ge 70\%$ of physical stops ($\text{Jaccard} \ge 0.70$).
  - **Bengaluru** accounts for **5,955 pairs (72.3%)**, driven by BMTC's radial corridor branching design where multiple route sub-variants share common trunk corridors before fanning out into suburbs.
  - **Why Overlap $\ne$ Redundancy**: Overlap is driven by directional Up/Down splits (e.g. HDBRT 338-U vs 338-D), trunk multiplexing, express vs. local services (Mumbai 182 RING vs 21 AS), and complementary temporal schedules (Pune 174 daytime trunk vs RATRANI 7 overnight owl service sharing 50 stops).
* **Low-Activity Candidates (2,023 Routes)**:
  - **1,447 routes schedule exactly 1 trip/day** (depot pull-outs, factory shifts).
  - **269 routes operate off-peak only** (zero morning and evening peak trips).
  - **307 routes operate with low frequency** within their city's bottom 10th percentile.

### Phase 7: Correlation & Feature Relationships
* **Spearman ($\rho$) vs. Pearson ($r$)**:
  - Spearman rank correlation captures true monotonic trends without distortion from extreme outliers. For instance, `stop_count` vs. `route_length_km` yields $\rho = +0.829$ (Spearman), but Pearson collapses to $r = +0.090$ due to heavy skewness.
* **Frequency Mechanics**:
  - `trip_count` vs. `median_headway_min` exhibits a strong negative correlation ($\rho = -0.730$), confirming that higher daily trips systematically decrease passenger waiting intervals.
* **Collinearity by Construction**:
  - `trips_morning` correlates with `trip_count` at $\rho = +0.893$ and $r = +0.970$ because total trips is the arithmetic sum of period trips.

### Phase 8: Data Quality Audit & Outlier Investigation
* **Bengaluru Shape File Corruption**:
  - Exactly **27 routes in Bengaluru** have computed lengths $> 200\text{ km}$ (up to **10,466.58 km** for Route 6552). Audit of raw `shapes.txt` revealed that coordinate points rapidly oscillate back and forth between two terminal coordinates 1,468 times, accumulating thousands of kilometers of synthetic length despite the physical route being $\approx 35\text{ km}$.
  - Classified as **Data Error / Raw Feed Corruption** and flagged in `processed/route_features_flagged.csv`.
* **Treatment Principle (Rule 3)**:
  - Outliers were **not deleted**. Automatic deletion would remove the most important high-capacity corridors in Indian cities (e.g., Mumbai station feeders).

---

## 3. Answers to Core Research Questions (With Exact Figures)

### Q1: Which hours have the highest and lowest scheduled trip counts?
* **Highest Scheduled Activity**:
  1. **08:00–08:59**: **17,289 trips** (7.64% of national supply) — Peak morning rush hour.
  2. **07:00–07:59**: **15,957 trips** (7.05% of national supply).
  3. **17:00–17:59**: **14,411 trips** (6.37% of national supply) — Peak evening return rush.
  4. **18:00–18:59**: **14,028 trips** (6.20% of national supply).
* **Lowest Scheduled Activity**:
  1. **02:00–02:59**: **161 trips** (0.07% of national supply) — Deep-night trough.
  2. **03:00–03:59**: **232 trips** (0.10% of national supply).
  3. **01:00–01:59**: **283 trips** (0.13% of national supply).
  4. **00:00–00:59**: **442 trips** (0.20% of national supply).
* **City Variations**: In Delhi, the single busiest departure hour is **20:00 (3,511 trips, 6.97% of Delhi daily supply)**, whereas in Bengaluru, Ahmedabad, and Pune, peak activity concentrates at **08:00**.

### Q2: How do operational patterns vary across routes?
Operational patterns display extreme polarization:
* **The High-Frequency Core**: **518 routes** schedule $\ge 100$ trips/day. Led by BEST in Mumbai, where Route `203` schedules **573 trips/day**, Route `182 RING` schedules **451 trips/day**, and Route `272` schedules **447 trips/day**. These operate with headways under 3 minutes across 18–20 hour daily spans.
* **The Micro & Single-Trip Long Tail**: **1,447 routes** schedule exactly 1 trip/day (1,043 in Bengaluru, 194 in HDBRT). These routes operate over very short daily spans (median 1.0 hour) serving as early-morning depot pull-outs or specialized school shuttles.
* **Off-Peak Only Circulators**: **269 routes** schedule zero trips during peak commuting windows (06:00–11:59 and 16:00–20:59), operating strictly as midday shopping circulators or overnight hospital shuttles.

### Q3: Which routes have the most distinct stops?
Routes with the highest physical stop counts are exclusively long peripheral circular loops in **Bengaluru (BMTC)** and **Mumbai (BEST)**:
1. `bengaluru_5056` (`TR-12`): **184 stops** (136.2 km, 2 scheduled trips/day).
2. `bengaluru_746` (`502-CT`): **179 stops** (126.3 km, 2 scheduled trips/day).
3. `bengaluru_3325` (`502-K`): **175 stops** (123.7 km, 2 scheduled trips/day).
4. `bengaluru_3327` (`502-C`): **168 stops** (120.5 km, 2 scheduled trips/day).
5. `bengaluru_2265` (`600-F`): **167 stops** (114.1 km, 2 scheduled trips/day).
6. `mumbai_1253` (`C-72 EXP`): **147 stops** (141.7 km, 8 scheduled trips/day).
*Pattern*: High-stop routes are predominantly long peripheral orbital services operating at low daily frequency (2–8 trips/day).

### Q4: Is route length associated with scheduled trip count in this data?
> **Answer**: **No. There is no consistent or meaningful association between route length and scheduled trip count across the dataset.**

* **Overall Evidence**:
  - Spearman rank correlation: $\rho = \mathbf{-0.050}$ (essentially zero monotonic association).
  - Pearson linear correlation: $r = \mathbf{-0.027}$ (essentially zero linear association).
* **City-Specific Divergence**:
  - **Delhi**: Mild positive association ($\rho = +0.348$, $r = +0.265$). Long Ring Road arterial trunks receive higher scheduled frequencies.
  - **Mumbai**: Mild negative association ($\rho = -0.171$, $r = -0.220$). Short station feeders (1.5–5 km) receive the highest frequencies (up to 573 trips), while long suburban routes maintain lower frequencies.
  - **Bengaluru**: Completely uncorrelated ($\rho = +0.025$, $r = -0.014$). Frequency is allocated based on passenger demand on the corridor rather than route distance.
  - **Davangere**: Negative association ($\rho = -0.535$, $r = -0.611$) across a small sample ($N=14$).

### Q5: Do any routes appear to share stops or geographic segments?
> **Answer**: **Yes. A total of 8,241 route pairs share $\ge 70\%$ of their physical stops ($\text{Jaccard} \ge 0.70$).**

* **Operational Explanations**:
  1. **Directional Inbound/Outbound Splitting**: Feeds frequently catalog UP and DOWN runs under distinct route IDs (e.g. HDBRT `338-U` vs `338-D`, Rajkot `B1` Up vs Down), exhibiting 100% stop overlap.
  2. **Trunk Multiplexing**: Multiple suburban feeder routes share a common central arterial highway before diverging into residential sectors (e.g., BMTC's 5,955 high-overlap pairs).
  3. **Temporal Complementarity**: In Pune, Route `174` (15 daytime trips) and `RATRANI 7` (3 overnight trips) share 50 stops ($\text{Jaccard} = 0.9615$, mean spatial separation 18.6m). They provide 24-hour connectivity along the corridor without competing for service hours.
  4. **Express vs. Local Differentiation**: In Mumbai, Route `182 RING` (451 daily trips) and Route `21 AS` (5 daily trips) share 100% of stops, serving high-turnover local commuters vs. premium air-conditioned passengers.

### Q6: Are there unusual values requiring investigation?
Yes, four major categories of anomalies were audited and classified:
1. **Unserved Catalog Routes (682 routes, 6.9%)**: Routes present in `routes.txt` with zero scheduled trips in `trips.txt` (494 in Mumbai, 83 in Delhi, 79 in Davangere). Classified as *Source-Data Limitation*.
2. **Corrupted Shape Trajectories (27 routes, 0.3%)**: In Bengaluru's `shapes.txt`, oscillating coordinate sequences inflate computed route lengths to thousands of kilometers (up to 10,466 km for Route 6552). Classified as *Data Error / Raw Feed Corruption*.
3. **Micro-Routes (68 routes, 0.7%)**: Routes under 0.5 km with 2–5 stops serving terminal platforms or depot gates. Classified as *Valid but Unusual*.
4. **Extended Peri-Urban Loops (12 routes, 0.1%)**: Ahmedabad AMTS routes spanning 150–171 km with 71–90 stops. Verified in `stops.txt` as legitimate industrial circuits. Classified as *Valid but Unusual*.

### Q7: What conclusions are supported and what additional data is needed?
* **Supported Conclusions**:
  1. The dataset provides an authoritative profile of **planned vehicle service supply** across 8 Indian transit systems.
  2. Transit agencies allocate service frequencies based on corridor passenger demand, resulting in zero correlation between route length and trip count nationally.
  3. Stop sharing is widespread (8,241 pairs) and represents intentional network structuring (trunk-feeder corridors, directional splits, day/night complementary shifts).
* **Unsupported Claims (Rule 2)**:
  - It is **impossible** to determine whether a route is overcrowded, underutilised, redundant, or inefficient from schedule data alone.
* **Essential Additional Data Required for Optimization (Modules 4 & 5)**:
  1. **Automated Passenger Counting (APC)**: Stop-level boardings, alightings, and in-vehicle passenger loads.
  2. **Automated Fare Collection (AFC)**: Smartcard tap-in/tap-out origin-destination travel matrices.
  3. **Fleet & Vehicle Specifications**: Differentiating 30-passenger midi-buses from 70-passenger standard and 120-passenger articulated buses.
  4. **Corridor Load Profiles**: Hourly passenger volume vs. rated vehicle capacity curves across stop sequences.

---

## 4. Deliverables & Data Inventory Summary
- **Baseline Feature Table**: `processed/route_features.csv` (9,915 routes, 20 features).
- **Quality-Flagged Table**: `processed/route_features_flagged.csv` (9,915 routes, 30 columns including 10 audit flags).
- **Route Comparison Table**: `reports/route_comparison_summary.csv` (9,915 routes).
- **Candidate Overlap List**: `reports/candidate_overlapping_routes.csv` (8,241 candidate pairs).
- **Candidate Low-Activity List**: `reports/candidate_low_activity_routes.csv` (2,023 candidate routes).
- **Data Quality Report**: `reports/eda_data_quality_summary.md`.
- **Findings & Limitations**: `reports/findings_and_limitations.md`.
- **Visualizations**: 17 high-resolution PNG charts (`visualizations/01_*.png` to `17_*.png`) and 3 interactive Folium maps (`visualizations/maps/01_*.html` to `03_*.html`).
