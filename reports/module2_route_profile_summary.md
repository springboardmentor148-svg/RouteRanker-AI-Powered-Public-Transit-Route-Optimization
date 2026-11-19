# Module 2 - Route profile summary

_Generated 2026-10-24._ Full route profiles: `data/processed/<city>/route_features.csv` (all cities combined: `data/processed/all_cities_route_features.csv`).

## Overview per city

| city | routes | trips | stops | median_trips_per_route | median_stops_per_route | median_length_km | length_from_shapes | share_trips_over_8h | median_trip_min | speed_p10_kmh | speed_p90_kmh |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ahmedabad | 972 | 14323 | 3235 | 8.00 | 40.00 | 17.80 | 0% | 0.01 | 75.00 | 11.50 | 46.10 |
| bengaluru | 4416 | 57836 | 9948 | 3.00 | 44.00 | 19.80 | 99% | 0.00 | 60.00 | 13.40 | 26.50 |
| chennai | 3934 | 47047 | 5477 | 4.00 | 23.00 | 15.40 | 0% | 0.00 | 51.00 | 14.60 | 31.20 |
| delhi | 2964 | 78507 | 6267 | 18.00 | 40.00 | 21.80 | 0% | 0.00 | 89.50 | 15.00 | 15.00 |
| hyderabad | 1031 | 44892 | 5028 | 8.00 | 55.00 | 26.50 | 0% | 0.68 | 768.20 | 1.00 | 5.80 |
| kochi | 465 | 15581 | 3228 | 34.00 | 100.00 | 23.20 | 100% | 0.00 | 65.00 | 20.80 | 22.40 |
| pune | 315 | 10128 | 6745 | 22.00 | 79.00 | 20.00 | 99% | 0.00 | 61.40 | 18.20 | 20.60 |


## Example route profiles (the route with the median number of trips in each city)

| city | route_id | route_name | n_trips | n_unique_stops | length_km | length_method | service_span_h | trips_per_active_hour | median_headway_min | trips_morning | trips_afternoon | trips_evening | trips_night | max_stop_overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ahmedabad | AMC_5335 | 136 | 8 | 59 | 18.82 | stop coordinates (straight-line, approximate) | 10.50 | 1.00 | 70.00 | 4 | 3 | 1 | 0 | 0.31 |
| bengaluru | 1991 | 258-F | 3 | 111 | 36.63 | shapes.txt | 13.17 | 1.00 | 395.00 | 1 | 1 | 0 | 1 | 0.85 |
| chennai | MTC-23295 | 500Et R1 | 4 | 40 | 34.77 | stop coordinates (straight-line, approximate) | 12.67 | 1.00 | 195.00 | 2 | 1 | 1 | 0 | 0.84 |
| delhi | 991 | 813EDOWN | 18 | 48 | 20.53 | stop coordinates (straight-line, approximate) | 13.50 | 1.50 | 24.00 | 3 | 8 | 6 | 1 | 0.64 |
| hyderabad | 277P | 277P | 8 | 61 | 35.61 | stop coordinates (straight-line, approximate) | 15.17 | 1.00 | 95.00 | 2 | 3 | 2 | 1 | 0.54 |
| kochi | r13874633 | Elamakkara ↔ Ernakulam South | 34 | 54 | 10.01 | shapes.txt | 16.00 | 2.00 | 60.00 | 14 | 10 | 8 | 2 | 0.90 |
| pune | N15 | N15 | 22 | 23 | 3.40 | shapes.txt | 7.50 | 2.75 | 20.00 | 18 | 4 | 0 | 0 | 0.08 |
