# Module 4 - Features selected and preprocessing decisions

_Generated 2026-10-30._

## Pipeline (all steps fitted on training routes)

1. Load the Module-2 route table; **keep the original file untouched**.
2. Derived columns: period shares (`trips_<period>` / `n_trips`), `peak_period`, and invalid-speed handling.
3. Exclude non-comparable feeds: **hyderabad** (trips look like whole vehicle duties (about 68% last over 8 hours), so n_trips, headway, duration and speed do not mean the same as in the other feeds) - 1,031 routes, listed in `excluded_routes.csv`.
4. Split 80:20 (grouped by city + route name).
5. Drop near-constant features (> 95% one value): weekend_to_weekday_ratio.
6. Median imputation (+ missing indicators), `log1p` for skewed features, standardisation, one-hot encoding.
7. Drop one of any pair correlated above 0.95: none found.

## Final feature set (25 columns)

| feature | treatment |
|---|---|
| median_headway_min_was_missing | missing/invalid indicator (0/1, unscaled) |
| avg_speed_kmh_was_missing | missing/invalid indicator (0/1, unscaled) |
| n_trips | log1p + standardised |
| n_unique_stops | log1p + standardised |
| median_stops_per_trip | standardised |
| length_km | log1p + standardised |
| service_span_h | standardised |
| n_active_hours | standardised |
| trips_per_active_hour | log1p + standardised |
| median_headway_min | log1p + standardised |
| avg_trip_duration_min | log1p + standardised |
| stops_per_km | standardised |
| avg_speed_kmh | log1p + standardised |
| max_stop_overlap | standardised |
| mean_routes_per_stop | log1p + standardised |
| share_morning | standardised |
| share_afternoon | log1p + standardised |
| share_evening | log1p + standardised |
| length_method__shapes.txt | one-hot (0/1) |
| length_method__stop coordinates (shape failed sanity check) | one-hot (0/1) |
| length_method__stop coordinates (straight-line, approximate) | one-hot (0/1) |
| peak_period__afternoon | one-hot (0/1) |
| peak_period__evening | one-hot (0/1) |
| peak_period__morning | one-hot (0/1) |
| peak_period__night | one-hot (0/1) |


These features describe the **scheduled service** of a route: how many trips and stops, how long and how fast on paper, how spread over the day, how much it shares stops with others, and how its length was measured.

## Columns not used as features

| columns | reason |
|---|---|
| city, route_id, route_name | identifiers / grouping (kept as ID columns, never used as numbers; city is not a feature so clusters do not simply copy city) |
| overlap_partner, overlap_partner_name | identifiers of another route (text) |
| route_type | constant (all routes are buses after Module 2) |
| median_trip_duration_min | almost the same information as avg_trip_duration_min; one of the pair is enough |
| trips_morning, trips_afternoon, trips_evening, trips_night | replaced by period shares (trips in a period / n_trips) so the time-of-day pattern is not just n_trips again |
| first_departure_h, last_departure_h | summarised by service_span_h |
| peak_hour, peak_hour_trips | peak_hour is circular (23 is next to 0) -> replaced by the categorical peak_period; peak_hour_trips follows n_trips |
| trips_monday .. trips_sunday, avg_trips_per_weekday, avg_trips_per_weekend_day | equal to n_trips whenever every service runs every day (true in most feeds); no weekday/weekend information |
| weekend_to_weekday_ratio | candidate feature but dropped automatically: 1.0 for almost every route (near-constant, no information) |
| n_service_ids, n_directions, trips_from_frequency | properties of how a feed was written (missing for whole feeds or only in Kochi), not of the route |
| length_km_stops, length_km_shape | components of length_km (its length_method is kept as a categorical feature) |
| overlap_share_of_route | max_stop_overlap already describes the overlap |
| has_time_backwards_trip, speed_implausible, sparse_schedule | data-quality / descriptive flags (speed_implausible is handled through the invalid-speed rule; sparse_schedule is derived from n_trips) |


## Decision on non-comparable feeds

Hyderabad's 'trips' appear to be whole vehicle duties (Module 3), so `n_trips`, headway, duration and speed mean something different there. Putting them in the same distance space as single-run trips would distort KMeans/DBSCAN. They are therefore **excluded from the pooled modelling set, not deleted**: they stay in Module 2 and in `excluded_routes.csv`, and `python run_module4.py --include-all` keeps them. This is open for the mentor to decide. Delhi, Kochi and Pune (near-constant speeds, generated-looking timetables) are kept, because their trip counts are comparable; their speeds should be read with care.
