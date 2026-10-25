# Module 2 - Route profile summary

_Generated 2026-10-25._ Full route profiles: `data/processed/<city>/route_features.csv` (all cities combined: `data/processed/all_cities_route_features.csv`).

## Overview per city

| city | routes | trips | stops | median_trips_per_route | median_stops_per_route | median_length_km | length_from_shapes | share_trips_over_8h | median_trip_min | speed_p10_kmh | speed_p90_kmh |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ahmedabad | 972 | 14323 | 3235 | 8.00 | 40.00 | 17.80 | 0% | 0.01 | 75.00 | 11.50 | 46.10 |
| bengaluru | 4416 | 57836 | 9948 | 3.00 | 44.00 | 19.80 | 99% | 0.00 | 60.00 | 13.40 | 26.50 |
| chennai | 3934 | 47047 | 5477 | 4.00 | 23.00 | 15.40 | 0% | 0.00 | 51.00 | 14.60 | 31.20 |
| delhi | 2964 | 78507 | 6267 | 18.00 | 40.00 | 21.80 | 0% | 0.00 | 89.50 | 15.00 | 15.00 |
| hyderabad | 1031 | 44892 | 5028 | 8.00 | 55.00 | 26.40 | 0% | 0.68 | 768.20 | 1.00 | 5.80 |
| kochi | 465 | 15581 | 3228 | 34.00 | 100.00 | 23.20 | 100% | 0.00 | 65.00 | 20.80 | 22.40 |
| pune | 315 | 10128 | 6745 | 22.00 | 79.00 | 20.00 | 99% | 0.00 | 61.40 | 18.20 | 20.60 |


## Example route profiles (the route with the median number of trips in each city)

| city | route_id | route_name | n_trips | n_unique_stops | length_km | length_method | service_span_h | trips_per_active_hour | median_headway_min | trips_morning | trips_afternoon | trips_evening | trips_night | max_stop_overlap |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ahmedabad | AMC_1835 | 116 | 8 | 23 | 8.59 | stop coordinates (straight-line, approximate) | 11.42 | 1.00 | 90.00 | 4 | 2 | 2 | 0 | 0.16 |
| bengaluru | 1800 | 201-G D6G-BSK | 3 | 60 | 17.68 | shapes.txt | 11.37 | 1.00 | 341.00 | 1 | 1 | 1 | 0 | 0.81 |
| chennai | MTC-10522 | 104A | 4 | 44 | 36.94 | stop coordinates (straight-line, approximate) | 4.78 | 1.00 | 85.00 | 3 | 1 | 0 | 0 | 0.93 |
| delhi | 997 | 408CLUP | 18 | 57 | 24.13 | stop coordinates (straight-line, approximate) | 13.67 | 1.50 | 20.00 | 6 | 5 | 7 | 0 | 0.74 |
| hyderabad | 545 | 545 | 8 | 58 | 41.58 | stop coordinates (straight-line, approximate) | 14.00 | 1.00 | 95.00 | 3 | 3 | 2 | 0 | 0.54 |
| kochi | r13531919 | Ankamaly ↔ Perumbavoor | 34 | 76 | 17.20 | shapes.txt | 16.00 | 2.00 | 60.00 | 14 | 10 | 8 | 2 | 0.51 |
| pune | 87 | 87 | 22 | 54 | 12.31 | shapes.txt | 8.50 | 2.20 | 20.00 | 18 | 4 | 0 | 0 | 0.46 |
