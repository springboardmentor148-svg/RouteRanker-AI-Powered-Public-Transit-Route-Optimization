# Assumptions and Limitations — RouteRanker Module 2

**Scope:** Analytical assumptions, methodological boundaries, and data constraints across Module 2 feature engineering.

---

## 1. Crucial Data Grounding Rule (Passenger Data)

> **Mandatory Transit Planning Principle (Rule 4):**  
> **Scheduled trips are NOT passenger counts, and transit overcrowding CANNOT be concluded from scheduled GTFS data alone.**  
>
> GTFS files represent published operational timetables (supply-side schedules). They contain zero information about passenger demand, ticket sales, electronic ticketing machine (ETM) logs, automated passenger counters (APC), or actual on-board bus crowding. A route with 100 scheduled trips might run half-empty, while a route with 5 trips might be severely overcrowded. No passenger volume or overcrowding features were created or assumed in this module.

---

## 2. Time-Based Feature Rules

### A. Time Period Classification
Assigned based on normalized departure hour `dep_hour` ($0 \le \text{dep\_hour} \le 23$):
- **`morning`**: `05:00` to `11:59` (`dep_hour` $\in [5, 11]$) — Captures the morning commute peak.
- **`afternoon`**: `12:00` to `16:59` (`dep_hour` $\in [12, 16]$) — Captures midday base service.
- **`evening`**: `17:00` to `20:59` (`dep_hour` $\in [17, 20]$) — Captures the evening return commute peak.
- **`night`**: `21:00` to `04:59` (`dep_hour` $\in [21, 23] \cup [0, 4]$) — Wraps across midnight to capture night and early dawn runs.

### B. Handling of Times Past 24:00:00 (Overnight GTFS Schedules)
- GTFS explicitly allows hour values $\ge 24$ for late-night trips that belong to the preceding service day (e.g. `25:10:00` = 01:10 AM next day).
- **Assumption & Rule**: Standard clock parsers (`pd.to_datetime()`) were **never used**.
- **Implementation**: Times are converted to cumulative seconds from service day start via string splitting:
  $$\text{dep\_seconds} = h \times 3600 + m \times 60 + s$$
  - `dep_hour_raw` $= \text{dep\_seconds} // 3600$ (preserves values $\ge 24$).
  - `dep_hour` $= \text{dep\_hour\_raw} \pmod{24}$ (maps to standard 0–23 clock hours).
  - `next_day_flag` $= (\text{dep\_hour\_raw} \ge 24)$.

---

## 3. Day Type Classification Rules

Calendar operational profiles are classified from `calendar.txt` / `.csv` binary day flags:
- **`weekday_only`**: At least one of Mon–Fri $= 1$, AND Saturday $= 0$, AND Sunday $= 0$.
- **`weekend_only`**: Saturday $= 1$ or Sunday $= 1$, AND all Mon–Fri $= 0$.
- **`all_days`**: All 7 days (Monday through Sunday) $= 1$.
- **`mixed`**: Any non-uniform schedule (e.g. Mon–Sat, omitting Sunday).
- **`unknown`**: Service IDs lacking day-of-week specifications (or orphan calendar records).

---

## 4. Headway Definition & Boundaries

- **Definition**: Headway is calculated as the time gap (in minutes) between consecutive vehicle departures on the **same route**, in the **same direction** (where `direction_id` is published), and within the **same `day_type`**:
  $$\text{headway\_min} = \frac{t_{i} - t_{i-1}}{60.0}$$
- **Single-Trip Rule (Rule 5 Compliance)**:
  - If a route/direction operates only 1 trip during a day type, headway is assigned **`NaN`**, **never `0`**.
  - A headway of 0 minutes would imply infinite bus frequency, which would severely distort route inefficiency ranking.

---

## 5. Route Length Estimation Methods & City Distribution

| Method | Description | Precision Level | Cities Utilizing Method |
|---|---|:---:|---|
| **`shape`** | Sum of Haversine distances along ordered road polyline vertices in `shapes.txt` for the route's mode `shape_id`. | **High** (traces road curves) | **Bengaluru** (4,416 routes), **Pune** (628 routes) |
| **`stop_straight_line_estimate`** | Sum of Haversine distances between consecutive physical stops along the route's representative trip with the most stops. | **Moderate** (underestimates road distance by 15–35%) | **Ahmedabad** (972 routes), **Delhi** (1,187 routes), **Mumbai** (1,115 routes), **HDBRT** (630 routes), **Rajkot** (271 routes), **Davangere** (14 routes) |
| **`unmeasured`** | Routes declared in `routes.txt` that have no scheduled trips or lack stop coordinates. | — | 682 inactive routes across all cities (retained as `NaN`) |

### Why Straight-Line Stop Distance is an Underestimate:
A straight line between stops cuts across terrain and buildings as a chord. Actual transit vehicles follow physical roadway networks that bend and turn. Therefore, stop-to-stop distances represent a mathematical lower bound.

---

## 6. Heterogeneity of GTFS Schemas Across Cities

Different municipal transit agencies publish differing subsets of GTFS fields:
1. **File Formats**: Delhi publishes comma-separated files with `.csv` extensions (`routes.csv`, etc.); all other 7 cities publish `.txt` files.
2. **Missing Identifiers in Delhi**: Delhi omits `route_short_name` entirely across all 1,270 routes; `route_long_name` serves as the sole route identifier.
3. **Column Set Disparities**:
   - Davangere `trips` has only 3 columns (`route_id`, `trip_id`, `service_id`), omitting `direction_id`, `shape_id`, and `block_id`.
   - Bengaluru `stops` has 9 columns (including `parent_station`, `platform_code`), while other cities have 4 columns.
4. **Shapes Availability**: Only Bengaluru and Pune provide `shapes.txt`.
