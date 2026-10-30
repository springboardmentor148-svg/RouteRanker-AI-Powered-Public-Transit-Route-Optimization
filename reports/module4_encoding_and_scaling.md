# Module 4 - Categorical encoding and feature scaling

_Generated 2026-10-30._ Planned next models: KMeans and DBSCAN, both **distance based**.

## Categorical features and encoding

| feature | meaning | encoding | why |
|---|---|---|---|
| length_method | how the route length was obtained (shapes.txt / stop coordinates / shape failed sanity check) | one-hot | unordered labels, so a single 1-2-3 column would invent an order and distances between them |
| peak_period | time period of the route's busiest hour (morning / afternoon / evening / night) | one-hot | unordered labels; recomputed from peak_hour with the Module-2 period rules; hour 23 and hour 0 are not far apart, which a plain number would claim |


**Not encoded as numbers:** `route_id`, `route_name`, `city` (identifiers/groups, kept beside the features, never inside them). Label encoding was not used because none of the categorical features has a natural order. The one-hot encoder is fitted on training data and ignores unknown categories at validation time.

## Scaling

* **Method: standardisation (z-score)**, fitted on the training routes: (x - mean) / standard deviation. KMeans and DBSCAN use Euclidean distance, so a feature measured in large units (e.g. trips, up to hundreds) would dominate one in small units (e.g. a 0-1 share). Standardisation gives every numeric feature mean 0 and standard deviation 1.
* **Why not min-max:** a few very long or very frequent routes would squeeze all other routes into a tiny part of 0-1, and DBSCAN's distance threshold depends on that spread.
* **Skew first:** counts and lengths are strongly right-skewed (seen in Module 3). Features with training skewness above 1.0 get `log1p` **before** standardisation so a few extreme routes do not stretch the scale.

| feature | skewness (train, after imputation) | log1p applied |
|---|---|---|
| n_trips | 3.72 | yes |
| n_unique_stops | 1.38 | yes |
| median_stops_per_trip | 0.58 | no |
| length_km | 11.73 | yes |
| service_span_h | -0.20 | no |
| n_active_hours | 0.73 | no |
| trips_per_active_hour | 3.58 | yes |
| median_headway_min | 2.68 | yes |
| avg_trip_duration_min | 26.75 | yes |
| stops_per_km | 0.96 | no |
| avg_speed_kmh | 2.35 | yes |
| max_stop_overlap | -0.29 | no |
| mean_routes_per_stop | 1.29 | yes |
| share_morning | 0.34 | no |
| share_afternoon | 1.04 | yes |
| share_evening | 1.65 | yes |


* **Not scaled:** the 0/1 one-hot columns and missing-indicator columns (already on a 0-1 scale).


## Verification

| feature | mean | std |
|---|---|---|
| median_headway_min_was_missing | 0.16 | 0.37 |
| avg_speed_kmh_was_missing | 0.01 | 0.10 |
| n_trips | -0.00 | 1.00 |
| n_unique_stops | -0.00 | 1.00 |
| median_stops_per_trip | -0.00 | 1.00 |
| length_km | -0.00 | 1.00 |
| service_span_h | 0.00 | 1.00 |
| n_active_hours | 0.00 | 1.00 |
| trips_per_active_hour | -0.00 | 1.00 |
| median_headway_min | -0.00 | 1.00 |
| avg_trip_duration_min | -0.00 | 1.00 |
| stops_per_km | -0.00 | 1.00 |
| avg_speed_kmh | -0.00 | 1.00 |
| max_stop_overlap | -0.00 | 1.00 |
| mean_routes_per_stop | -0.00 | 1.00 |
| share_morning | -0.00 | 1.00 |


Training means are 0 and standard deviations 1 by construction; the validation set is transformed with the **training** mean and standard deviation, so its values are not exactly 0 / 1 - this is intended.
