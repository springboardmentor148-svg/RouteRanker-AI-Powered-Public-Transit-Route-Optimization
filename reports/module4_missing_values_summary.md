# Module 4 - Missing values summary

_Generated 2026-10-30._ Input: `data/processed/all_cities_route_features.csv` (Module 2), 14,097 routes; 1,031 routes of hyderabad excluded (see decisions report) -> 13,066 routes modelled.

## Columns with missing or invalid values (candidate features only)

| column | missing | pct | worst_city | worst_city_pct |
|---|---|---|---|---|
| median_headway_min | 2102 | 16.09 | bengaluru | 23.60 |
| avg_speed_kmh | 122 | 0.93 | ahmedabad | 2.80 |


## Why the values are missing - investigation

**`median_headway_min`.** Headway needs at least two scheduled departures of the same route and service. The table shows where it is missing:

| group | routes | missing_headway | share_missing_% |
|---|---|---|---|
| routes with 1 trip | 2102 | 2102 | 100.00 |
| routes with 2+ trips | 10964 | 0 | 0.00 |


Every missing value belongs to a route with exactly one scheduled trip, and no route with two or more trips is affected. With a single departure there is no gap between two departures, so the value is **undefined in the source**: it cannot be recovered from the GTFS files, and it is not zero.

**`avg_speed_kmh`.** Scheduled speed = estimated route length / scheduled duration. 52 routes have a speed below 3 km/h and 70 above 80 km/h, which no bus schedule can mean; the length (a straight-line estimate for many feeds) or the timetable is unreliable. Both inputs come from the source, so the speed cannot be recovered. By city:

| city | invalid_speed_routes | share |
|---|---|---|
| ahmedabad | 27 | 0.03 |
| bengaluru | 93 | 0.02 |
| chennai | 0 | 0.00 |
| delhi | 0 | 0.00 |
| kochi | 0 | 0.00 |
| pune | 2 | 0.01 |


**Other columns:** `length_km_shape` (missing wherever a feed has no shapes) and `n_directions` (missing where a feed has no direction_id) are not model features; `overlap_partner` (missing for routes with no overlap partner) is an identifier. No route was removed for missing values.


## Methods and justification

| Column | Method | Why |
|---|---|---|
| median_headway_min | median imputation (median of the **training** routes) + a 0/1 column `median_headway_min_was_missing` | The median is robust to the very skewed headways; the indicator keeps the information that the route has no repeating service, so the filled value is not mistaken for a real headway. Zero would mean a bus every 0 minutes. |
| avg_speed_kmh | impossible values set to missing, then median imputation + `avg_speed_kmh_was_missing` | An invalid value is not a measurement; deleting the route would lose its other valid features. |

After preprocessing, the number of missing or infinite values in the modelling tables is **0** (checked by the runner). The original files are unchanged.
