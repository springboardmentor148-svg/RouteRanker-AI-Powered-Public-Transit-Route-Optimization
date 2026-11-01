# Module 1: GTFS Dataset Understanding

## 1. Introduction

The RouteRanker project uses GTFS (General Transit Feed Specification) datasets to understand public transportation routes, trips, stops, and scheduled timings across five Indian cities.

The five selected cities are:
- Banglore
- Hyderabad
- Delhi
- Mumbai
- Pune

The datasets were collected from Mobility Database.

## 2. Understanding the GTFS Files

### routes.txt
Contains information about public transport routes.

Important column:
- `route_id`: Unique identifier for a route.

### trips.txt
Contains scheduled trips operating on different routes.

Important columns:
- `route_id`: Identifies the route.
- `trip_id`: Identifies an individual trip.
- `service_id`: Identifies the service calendar.

### stop_times.txt
Contains the scheduled arrival and departure times for each trip at different stops.

Important columns:
- `trip_id`: Identifies the trip.
- `arrival_time`: Scheduled arrival time.
- `departure_time`: Scheduled departure time.
- `stop_id`: Identifies the stop.
- `stop_sequence`: Order of stops in a trip.

### stops.txt
Contains information about public transport stops.

Important columns:
- `stop_id`: Unique stop identifier.
- `stop_name`: Name of the stop.
- `stop_lat`: Latitude, when supplied.
- `stop_lon`: Longitude, when supplied.

### calendar.txt
Contains information about the days and date ranges when scheduled services operate.

Important columns:
- `service_id`
- `monday` to `sunday`
- `start_date`
- `end_date`

## 3. Relationships Between GTFS Files

The GTFS files are connected through common identifiers.

1. `routes.txt` and `trips.txt` are connected using `route_id`.
2. `trips.txt` and `stop_times.txt` are connected using `trip_id`.
3. `stop_times.txt` and `stops.txt` are connected using `stop_id`.
4. `trips.txt` and `calendar.txt` are connected using `service_id`.

These relationships help identify which trips belong to each route, which stops are served by each trip, and when the trips operate.

## 4. Dataset Inventory Summary

The project contains five city datasets.

| City | Routes | Trips | Stop Times | Stops |
|---|---:|---:|---:|---:|
| Banglore | 4,434 | 57,836 | 1,540,686 | 9,960 |
| Hyderabad | 1,031 | 44,892 | 1,132,807 | 5,028 |
| Delhi | 2,964 | 78,515 | 3,276,092 | 6,342 |
| Mumbai | 935 | 99,080 | 2,655,026 | 7,506 |
| Pune | 315 | 10,128 | 429,302 | 6,745 |

## 5. Initial Data Quality Findings

The initial inspection checked:
- Duplicate route IDs.
- Duplicate trip IDs.
- Duplicate stop IDs.
- Missing values in important columns.
- Invalid route, trip, and stop references.

The four cities Banglore, Hyderabad, Mumbai, and Pune showed zero duplicate IDs in the checked columns.

Delhi contained 8 duplicate trip IDs, accounting for 8 exact duplicate extra rows. These records are preserved in the original dataset and will be handled during data preprocessing.

All five cities have the four main GTFS files and `calendar.txt` available.

## 6. Conclusion

The five city GTFS datasets were successfully collected and inspected. Their file structures, record counts, important columns, and relationships were examined.

The initial data quality checks identified a duplicate-trip issue in the Delhi dataset, which has been documented for later preprocessing.

These datasets provide the foundation for the next stages of RouteRanker, including feature engineering, exploratory data analysis, data preprocessing, and route optimization.