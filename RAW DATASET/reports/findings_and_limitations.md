# RouteRanker: Findings, Methodological Assumptions, and Limitations Report
**Module 3: Exploratory Data Analysis of Public Transit Networks Across 8 Indian Cities**

---

## 1. Compliance Statement on Network Inefficiency & Utilization (Rule 2)

> **MANDATORY PROJECT GOVERNANCE NOTICE (RULE 2)**:
> **In strict adherence to Project Governance Rule 2, NO route in this analysis is confirmed as overcrowded, underutilised, redundant, or inefficient.**
> 
> The General Transit Feed Specification (GTFS) data evaluated throughout Module 3 represents **planned operational vehicle supply**. Timetable files record when vehicles are scheduled to depart; they contain **zero information** regarding realized passenger boardings, alightings, passenger loads, or farebox revenue.
> 
> Therefore, all routes exhibiting high stop overlap or low scheduled frequencies are strictly designated as **"potential patterns / candidates for further analysis"**. Determining whether a route is genuinely inefficient or underutilized requires external empirical ridership data.

---

## 2. Potential Patterns Requiring Further Empirical Investigation

Based on the exploratory screening conducted across 9,915 route profiles, the following structural patterns have been cataloged as candidates for in-depth operational review in subsequent modules:

### 1. High-Overlap Corridor Multiplexing (8,241 Candidate Route Pairs)
* **Screening Criterion**: Route pairs sharing $\ge 70\%$ of their physical stops ($\text{Jaccard} \ge 0.70$).
* **Candidate Scope**: Concentrated heavily in **Bengaluru (5,955 pairs)**, **Ahmedabad (1,046 pairs)**, and **Delhi (552 pairs)**.
* **Operational Nature**:
  - *Directional Splits*: Pairs representing identical two-way service cataloged under separate route IDs (e.g. HDBRT `338-U` vs `338-D`, Rajkot `B1` Up vs Down).
  - *Trunk Arterial Multiplexing*: Multiple suburban feeder lines sharing a central arterial corridor to pool frequency before branching into distinct residential neighborhoods.
  - *Day/Night Complementary Shifts*: In Pune, Route `174` (15 daytime trips) and Route `RATRANI 7` (3 overnight trips) share 50 stops ($\text{Jaccard} = 0.9615$, mean spatial separation 18.6m). They provide continuous 24-hour connectivity along the corridor without competing for service hours.
  - *Express vs. Local Service*: In Mumbai, Route `182 RING` (451 daily trips) and Route `21 AS` (5 daily trips) share 100% of stops, serving high-turnover local commuters vs. premium air-conditioned passengers.
* **Recommended Next Step**: Overlay Automated Passenger Counting (APC) data to assess whether corridor passenger load justifies multiple overlapping services or if fleet consolidation into a high-capacity trunk is feasible.

### 2. Single-Trip Operational Services (1,447 Candidate Routes)
* **Screening Criterion**: Routes with exactly 1 scheduled daily trip (`trip_count == 1`).
* **Candidate Scope**: **Bengaluru (1,043 routes)**, **HDBRT (194 routes)**, **Ahmedabad (94 routes)**, **Rajkot (81 routes)**.
* **Operational Nature**: Primarily non-revenue deadhead runs (depot pull-outs and pull-ins), early-morning factory shifts, or specialized school runs.
* **Recommended Next Step**: In Module 5 (Timetable Optimization), integrate depot deadheading constraints to identify opportunities for vehicle interlining and schedule synchronization.

### 3. Off-Peak Only Services (269 Candidate Routes)
* **Screening Criterion**: Routes with zero scheduled departures during morning peak (06:00–11:59) and evening peak (16:00–20:59).
* **Candidate Scope**: Midday shopping connectors and late-night hospital/station shuttles.
* **Recommended Next Step**: Evaluate passenger demand curves during off-peak hours to assess whether on-demand microtransit or fixed-schedule mini-buses are the optimal fleet choice.

### 4. Unserved Catalog Placeholders (682 Routes)
* **Screening Criterion**: Routes listed in `routes.txt` with zero scheduled trips in `trips.txt`.
* **Candidate Scope**: Concentrated in **Mumbai (494 routes)**, **Delhi (83 routes)**, and **Davangere (79 routes)**.
* **Operational Nature**: Inactive licenses, seasonal routes, or retired catalog entries retained in transit authority databases.
* **Recommended Next Step**: Verify with municipal transit agencies whether these represent dormant routes intended for future tender or obsolete records slated for archival cleanup.

---

## 3. Methodological Assumptions

1. **Timetable Completeness for Baseline Service**:
   - Published GTFS timetable schedules represent the intended regular weekday operating supply of the respective transit agencies.
2. **Stop Spatial Representation**:
   - Discrete stop coordinates published in `stops.txt` accurately mark physical passenger boarding and alighting locations along the road network.
3. **Distance Estimation Approximation**:
   - For transit systems where high-resolution shape alignments (`shapes.txt`) are unavailable, the cumulative straight-line Haversine distance between sequential stops serves as a consistent, reproducible proxy for physical route length.
4. **Independent Route Profiling**:
   - Unserved catalog routes (having zero scheduled trips) are preserved in the total inventory per Rule 3, but excluded from operational correlation and frequency statistics to avoid skewing active service metrics.

---

## 4. Technical Limitations of the Dataset

### Limitation 1: Scheduled Supply vs. Realized Demand (Rule 1)
* **Issue**: The dataset captures **planned vehicle dispatches**, not realized ridership.
* **Impact**: High scheduled frequency does not prove high ridership; low scheduled frequency does not prove low demand. A bus scheduled to run once a day might be completely full, while a bus scheduled every 10 minutes might run empty.
* **Analytical Boundary**: All EDA metrics describe the supply side of public transportation. Passenger crowding, passenger-kilometers traveled, and revenue performance cannot be calculated from GTFS data alone.

### Limitation 2: Absence of Farebox & Operational Cost Data
* **Issue**: The GTFS feeds contain no financial, fare collection, or operational cost attributes.
* **Impact**: Operational cost per vehicle-kilometer, farebox recovery ratios, subsidy requirements, and route profitability cannot be computed.

### Limitation 3: Agency Feed Heterogeneity & Aggregation Discrepancies
* **Issue**: Different municipal transit authorities employ vastly different GTFS publishing philosophies:
  - **Bengaluru (BMTC) & HDBRT**: Highly granular publishing. Separate `route_id` values are generated for individual trip variations, single-trip depot runs, and directional variants.
  - **Mumbai (BEST) & Pune (PMPML)**: Moderate aggregation. Common corridors are grouped under fewer parent route names, with distinct identifiers for special branches.
  - **Delhi (DTC/DIMTS)**: Published as `.csv` rather than standard `.txt`; `route_short_name` is completely null across all 1,270 routes, requiring fallback to `route_long_name`.
  - **Davangere**: A small municipal pilot dataset ($N=93$ routes cataloged, only 14 actively served).
* **Impact**: Direct cross-city comparisons of raw route counts must be interpreted in light of agency cataloging conventions.

### Limitation 4: Spatial Alignment Feed Gaps (Rule 7)
* **Issue**: High-resolution trajectory shape files (`shapes.txt`) are available **only for Bengaluru (7,355 shapes) and Pune (628 shapes)**.
* **Impact**: For the remaining 6 cities (**Ahmedabad, Davangere, Delhi, HDBRT, Mumbai, and Rajkot**), agency feeds did not publish roadway alignments.
* **Analytical Boundary**: In accordance with Rule 7, shape-based trajectory curvature, road gradient, and physical corridor overlap could not be computed for these 6 cities. Straight-line maps were intentionally excluded to prevent misleading representations.

### Limitation 5: Corrupted Coordinate Trajectories in Raw Agency Feeds
* **Issue**: In Bengaluru's raw `shapes.txt`, **27 route shapes** (e.g., `V-360B FLY DOWN` for route 6552) suffer from severe data corruption where coordinate points rapidly oscillate back and forth 1,468 times between two terminal coordinates.
* **Impact**: This oscillation artificially inflates computed route lengths to thousands of kilometers (reaching up to **10,466.58 km** for Route 6552).
* **Treatment**: These 27 routes were identified, classified as `Data Error (Corrupted Raw Shape Trajectory)`, and flagged in `processed/route_features_flagged.csv` without deleting the underlying records.

### Limitation 6: Calendar Uniformity Across Service Days
* **Issue**: In 6 of 8 cities, `calendar.txt` marks all bus services as active across all 7 days of the week (`monday` through `sunday` all set to `1`).
* **Impact**: In the processed dataset, `trips_weekday` and `trips_weekend` are identical to `trip_count`. Empirical analysis of weekday vs. weekend service reductions could not be performed due to feed limitations.

---

## 5. Roadmap to Route Optimization (Modules 4 & 5 Prerequisites)

To transition from exploratory candidate screening to authoritative network restructuring and AI route optimization, the following external datasets are strictly required:

| External Data Required | Primary Source | Analytical Purpose in Route Optimization |
| :--- | :--- | :--- |
| **Automated Passenger Counting (APC)** | Onboard infrared door sensors | Measures exact boardings, alightings, and passenger load profiles per stop. Identifies genuine passenger crowding vs. empty buses. |
| **Automated Fare Collection (AFC)** | Smartcard / QR ticketing tap logs | Establishes origin-destination (O-D) passenger travel matrices, identifying unserved travel desire lines across the city. |
| **Fleet & Vehicle Specifications** | Agency fleet asset registers | Incorporates passenger carrying capacity (30-seat minibus vs. 70-passenger standard vs. 120-passenger articulated bus) into scheduling optimization. |
| **Real-Time Vehicle Location (AVL / GPS)** | Agency telematics feeds | Evaluates actual on-time performance, headway regularity, and traffic congestion bottlenecks along corridors. |
| **Operating Cost Structures** | Agency accounting statements | Incorporates cost per vehicle-kilometer, driver shift regulations, and fuel/electricity expenses into route feasibility models. |

---

## 6. Conclusion
The Module 3 Exploratory Data Analysis establishes a rigorous, audited baseline of public transit supply across 8 Indian cities. All candidate patterns, structural outliers, and data limitations have been systematically documented. With the dataset cleaned, audited, and flagged, the project is fully prepared for **Module 4: Predictive Modeling and Feature Engineering**.
