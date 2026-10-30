# Data Quality Report — RouteRanker Module 2

**Scope:** Quality validation across all 8 city GTFS datasets  
**Audit Reference:** `reports/data_quality_checks.csv`  

---

## 1. Summary of Data Quality Findings

The table below summarizes the comprehensive automated audit conducted in Phase 2 across all 8 transit networks:

| City | Total Missing Cells | Duplicate Rows | Duplicate Primary IDs | Orphan Foreign Keys | Bad Time Formats | Overnight Times ($\ge 24\text{h}$) | Bad Coordinates | Date Inversions (`end < start`) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Ahmedabad** | 14,323 | 0 | 0 | 0 | 0 | 3,988 | 0 | 0 |
| **Bengaluru** | 30,368 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Davangere** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Delhi** | 51,626 | 0 | 0 | 0 | 0 | 6,148 | 0 | 0 |
| **HDBRT** | 0 | 0 | 0 | 0 | 0 | 17 | 0 | 0 |
| **Mumbai** | 0 | 0 | 0 | 0 | 0 | 28,548 | 0 | 0 |
| **Pune** | 0 | 0 | 0 | 0 | 0 | 358 | 0 | 0 |
| **Rajkot** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | **96,317** | **0** | **0** | **0** | **0** | **39,059** | **0** | **0** |

---

## 2. Detailed Issue Analysis & Actions Taken

### A. Missing Values
| City | File | Column | Missing Count | % of File | Meaning | Action Taken |
|---|---|---|---:|---:|---|---|
| **Ahmedabad** | `trips` | `shape_id` | 14,323 | 100.0% | Feed does not provide spatial geometry shapes for trips | None (documented only; fallback to stop-to-stop distance in Phase 6) |
| **Delhi** | `trips` | `shape_id` | 50,355 | 100.0% | Feed does not include `shapes.csv` | None (documented only; fallback to stop-to-stop distance in Phase 6) |
| **Delhi** | `routes` | `route_short_name` | 1,270 | 100.0% | Delhi transit feeds use `route_long_name` as the primary identifier | None (documented only; retained as `NaN`, `route_long_name` used) |
| **Delhi** | `stops` | `stop_code` | 1 | 0.02% | Single stop missing public code | None (documented only; primary key `stop_id` is intact) |
| **Bengaluru** | `stops` | `parent_station` | 9,883 | 99.2% | Most BMTC bus stops are roadside poles, not partitioned stations | None (documented only; standard GTFS optional hierarchy) |
| **Bengaluru** | `stops` | `platform_code` | 9,883 | 99.2% | Roadside stops lack numbered platforms | None (documented only; standard GTFS optional field) |
| **Bengaluru** | `stops` | `location_type` | 9,948 | 99.9% | Default `0` (regular stop) omitted by agency | None (documented only; interpreted as standard stop) |
| **Bengaluru** | `stops` | `stop_desc` | 455 | 4.6% | Landmark descriptive text omitted | None (documented only; coordinates and names intact) |
| **Bengaluru** | `stops` | `zone_id` | 199 | 2.0% | Unzoned peripheral stops | None (documented only; fares not modeled in this module) |

### B. Inactive / Ghost Routes (Unscheduled Routes)
- **Finding**: Out of 9,915 declared routes in `routes.txt`, **682 routes (6.88%)** have zero scheduled trips in `trips.txt`.
  - Mumbai: 494 unscheduled routes
  - Delhi: 83 unscheduled routes
  - Davangere: 79 unscheduled routes
  - Bengaluru: 18 unscheduled routes
  - Ahmedabad: 6 unscheduled routes
  - HDBRT: 2 unscheduled routes
- **Action Taken**: **None (documented only)**. In accordance with **Rule 5**, their `trip_count`, `stop_count`, `route_length_km`, and headway are preserved as **`NaN`**, **never filled with 0**.

### C. Times Past 24:00:00 (Overnight Trips)
- **Finding**: **39,059 stop_times records** have scheduled arrival/departure hours $\ge 24$ (e.g. `24:15:00`, `25:30:00`).
  - Mumbai: 28,548 records
  - Delhi: 6,148 records
  - Ahmedabad: 3,988 records
  - Pune: 358 records
  - HDBRT: 17 records
- **Meaning**: These are late-night trips that depart after midnight but belong operationally to the previous service day.
- **Action Taken**: None (documented only). Arithmetic string splitting was implemented to convert times to cumulative seconds from service day start (`h*3600 + m*60 + s`), and `dep_hour = raw_hour % 24` was computed for time-of-day classification.

### D. Relational Consistency (Foreign Keys)
- **Finding**: All 4 relational cross-checks verified **0 orphan IDs** across all 8 cities:
  - Every `trips.route_id` exists in `routes.txt`.
  - Every `stop_times.trip_id` exists in `trips.txt`.
  - Every `stop_times.stop_id` exists in `stops.txt`.
  - Every `trips.service_id` exists in `calendar.txt`.
- **Action Taken**: None needed; relational integrity is 100% sound.
