# Module 2 - Data quality report

_Generated 2026-10-25._ Raw files are untouched (`data/raw/`); cleaned tables are rebuilt in memory and the features saved to `data/processed/`. Each action below lists how many rows it affected and why. Missing values are **not** replaced by zero.

## Cleaning actions (only steps that affected at least one row; full log incl. before/after counts: `reports/module2_cleaning_log.csv`)

`removed` = rows dropped (reason given); `expanded` = rows added; `filled` = a missing value copied from the other time of the same stop visit; `flagged` = kept and marked; `derived` = label created.

| city | table | step | action | rows_affected | reason |
|---|---|---|---|---|---|
| ahmedabad | routes | FLAG routes with no scheduled trip after cleaning | flagged | 6 | Kept in routes table; they simply have no scheduled service in this feed |
| bengaluru | routes | FLAG routes with no scheduled trip after cleaning | flagged | 18 | Kept in routes table; they simply have no scheduled service in this feed |
| chennai | routes | exclude non-bus route_type | removed | 791 | Project scope is public bus routes; metro/rail/ferry rows excluded here (they remain in the raw files) |
| chennai | trips | drop trips whose route is not in the cleaned routes | removed | 1388 | Orphan trips, or trips of excluded non-bus routes, cannot be analysed |
| chennai | stop_times | drop rows whose trip is not in the cleaned trips | removed | 28638 | Orphan rows or rows of excluded routes |
| chennai | routes | FLAG routes with no scheduled trip after cleaning | flagged | 677 | Kept in routes table; they simply have no scheduled service in this feed |
| delhi | trips | drop duplicate trip_id | removed | 8 | trip_id must be unique; first occurrence kept |
| kochi | routes | exclude non-bus route_type | removed | 8 | Project scope is public bus routes; metro/rail/ferry rows excluded here (they remain in the raw files) |
| kochi | trips | drop trips whose route is not in the cleaned routes | removed | 16 | Orphan trips, or trips of excluded non-bus routes, cannot be analysed |
| kochi | stop_times | drop rows whose trip is not in the cleaned trips | removed | 110 | Orphan rows or rows of excluded routes |
| kochi | trips | expand frequencies.txt templates into explicit trips | expanded | 14664 | Feed gives 'a bus every N seconds'; without expansion trip counts would be far too low |
| kochi | stop_times | rows after frequency expansion | expanded | 744248 | Consequence of the expansion above |


## Missing values in the route-level feature table (and why)

| city | feature | missing | pct |
|---|---|---|---|
| ahmedabad | median_headway_min | 94 | 9.70 |
| ahmedabad | length_km_shape | 972 | 100.00 |
| bengaluru | median_headway_min | 1043 | 23.60 |
| bengaluru | overlap_partner | 14 | 0.30 |
| bengaluru | overlap_partner_name | 14 | 0.30 |
| chennai | median_headway_min | 869 | 22.10 |
| chennai | length_km_shape | 3934 | 100.00 |
| chennai | overlap_partner | 1 | 0.00 |
| chennai | overlap_partner_name | 1 | 0.00 |
| delhi | median_headway_min | 96 | 3.20 |
| delhi | length_km_shape | 2964 | 100.00 |
| hyderabad | median_headway_min | 145 | 14.10 |
| hyderabad | length_km_shape | 1031 | 100.00 |

**Reading the table:** `median_headway_min` is missing when a route has fewer than 2 distinct departure times (headway undefined); `length_km_shape` when the feed has no shapes.txt or the trip has no shape_id (length then comes from stop coordinates, see `length_method`); `n_directions` when direction_id is absent; `weekend_to_weekday_ratio` when the route has no weekday trips; `trips_<day>` columns are absent when the feed has no calendar.txt. These are *unknown or undefined*, not zero.


## Other checks per city

| city | duplicate_route_ids | speed_flagged | backwards_trip_routes |
|---|---|---|---|
| ahmedabad | 0 | 27 | 0 |
| bengaluru | 0 | 93 | 0 |
| chennai | 0 | 0 | 0 |
| delhi | 0 | 0 | 0 |
| hyderabad | 0 | 778 | 0 |
| kochi | 0 | 0 | 0 |
| pune | 0 | 2 | 0 |


`speed_flagged` = routes with scheduled average speed > 80 or < 3 km/h; `backwards_trip_routes` = routes with a trip whose arrival times go backwards. These rows are **kept and flagged**; whether each is an error, a valid unusual case or a source limitation is examined in Module 3 (EDA).
