# Feature Dictionary — RouteRanker Module 2

**Dataset:** `processed/route_features.csv`  
**Total Records:** 9,915 routes across 8 Indian cities  
**Schema Definition:** 20 columns (12 numerical, 6 categorical, 2 identifier fields)

---

## 1. Feature Specifications

| Feature | Meaning | Source File(s) | Calculation Method | Data Type | Original or Derived |
|---|---|---|---|:---:|:---:|
| `city` | Name of the transit agency / municipal network | Directory name | Extracted from city folder mapping during ingest | `str` | Original |
| `route_id` | Globally unique route identifier across all cities | `routes.txt` / `.csv` | Prefixed with city name: `"{city}_{raw_route_id}"` | `str` | Derived |
| `original_route_id` | Original route identifier as assigned by transit agency | `routes.txt` / `.csv` | Raw `route_id` with `"{city}_"` prefix stripped | `str` | Original |
| `route_short_name` | Public transit line number or display designation | `routes.txt` / `.csv` | Direct extraction from GTFS feed (NaN in Delhi) | `str` | Original |
| `route_long_name` | Full origin-to-destination corridor corridor description | `routes.txt` / `.csv` | Direct extraction from GTFS feed | `str` | Original |
| `trip_count` | Total number of distinct scheduled trips per day | `trips.txt` / `.csv` | `.groupby('route_id')['trip_id'].nunique()` | `float64` | Derived |
| `stop_count` | Total distinct physical stops served along the route | `trips`, `stop_times` | Join on `trip_id`, then `.groupby('route_id')['stop_id'].nunique()` | `float64` | Derived |
| `route_length_km` | Physical trajectory distance in kilometers | `shapes.txt` or `stops.txt` | Cumulative Haversine sum along mode shape or max-stop trip | `float64` | Derived |
| `length_method` | Methodology used to calculate route distance | GTFS file audit | `'shape'` if `shapes.txt` used; `'stop_straight_line_estimate'` if fallback | `str` | Derived |
| `median_headway_min` | Median scheduled interval between consecutive departures | `stop_times`, `trips` | `(start_seconds.diff() / 60.0).median()` grouped by route, day, and direction | `float64` | Derived |
| `trips_morning` | Scheduled departures in morning peak window (05:00–11:59) | `stop_times`, `trips` | Count distinct trips departing with terminal hour 5 to 11 | `float64` | Derived |
| `trips_afternoon` | Scheduled departures in afternoon window (12:00–16:59) | `stop_times`, `trips` | Count distinct trips departing with terminal hour 12 to 16 | `float64` | Derived |
| `trips_evening` | Scheduled departures in evening peak window (17:00–20:59) | `stop_times`, `trips` | Count distinct trips departing with terminal hour 17 to 20 | `float64` | Derived |
| `trips_night` | Scheduled departures in night/owl window (21:00–04:59) | `stop_times`, `trips` | Count distinct trips departing with terminal hour 21–23 or 0–4 | `float64` | Derived |
| `trips_weekday` | Scheduled trips active on Monday through Friday | `trips`, `calendar` | Distinct trips whose `operating_days` includes any weekday | `float64` | Derived |
| `trips_weekend` | Scheduled trips active on Saturday or Sunday | `trips`, `calendar` | Distinct trips whose `operating_days` includes Saturday or Sunday | `float64` | Derived |
| `first_departure_hour` | Earliest scheduled departure hour from origin terminal | `stop_times`, `trips` | `min(start_seconds) // 3600` for that route (0 to 23) | `float64` | Derived |
| `last_departure_hour` | Latest scheduled departure hour from origin terminal | `stop_times`, `trips` | `max(start_seconds) // 3600` for that route (may be $\ge 24$) | `float64` | Derived |
| `service_span_hours` | Operating duration between first and last departure | `stop_times`, `trips` | `(max(start_seconds) - min(start_seconds)) / 3600.0` | `float64` | Derived |
| `operating_days` | Union of active service days for the route | `trips`, `calendar` | Unique day names across route trips, ordered Mon–Sun | `str` | Derived |

---

## 2. Excluded Candidate Features (Rule Compliance)

- **Passenger Counts / Boarding / Alighting / Load Factors**: Excluded per **Rule 4**. GTFS contains scheduled timetables only; no passenger volume is recorded.
- **Overcrowding Indicators**: Excluded per **Rule 4**. Cannot be inferred from scheduled trips.
- **Fare Amounts**: Excluded because fare rules exist in only 2 of 8 cities (Ahmedabad and Bengaluru); including would create 75%+ structural missingness.
- **Live Travel Speeds**: Excluded because GTFS is a static schedule and lacks real-time GPS vehicle tracking (AVL).
- **Curvature / Circuity Ratio**: Excluded because `shapes.txt` is present in only 2 of 8 cities.
