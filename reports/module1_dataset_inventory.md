# Module 1 – Dataset inventory and data-quality observations

_Generated 2026-10-18. Counts only – **no record was deleted, imputed or modified**._

## Summary: required files and record counts per city

| city | calendar.txt | routes.txt | stop_times.txt | stops.txt | trips.txt |
|---|---|---|---|---|---|
| ahmedabad | 1 | 978 | 646854 | 3235 | 14323 |
| bengaluru | 1 | 4434 | 1540686 | 9960 | 57836 |
| chennai | 12 | 5402 | 1389081 | 6542 | 48435 |
| delhi | 1 | 2964 | 3276092 | 6342 | 78515 |
| hyderabad | 1 | 1031 | 1132807 | 5028 | 44892 |
| kochi | 1 | 473 | 46648 | 3258 | 933 |
| pune | 1 | 315 | 429302 | 6745 | 10128 |

**Missing required files:** none


## Optional files available

| city | agency.txt | calendar_dates.txt | feed_info.txt | frequencies.txt | shapes.txt |
|---|---|---|---|---|---|
| ahmedabad | yes | – | yes | – | – |
| bengaluru | yes | – | yes | – | yes |
| chennai | yes | yes | yes | – | yes |
| delhi | yes | – | – | – | – |
| hyderabad | yes | – | yes | – | – |
| kochi | yes | – | yes | yes | yes |
| pune | yes | – | yes | – | yes |


**Why optional files matter:**

* `frequencies.txt` – Lets feeds describe 'a bus every N seconds' instead of listing each trip; needed to count real trips/hour.
* `shapes.txt` – Exact road geometry of a route; gives true route length/maps (stop-to-stop distance is only an approximation).
* `calendar_dates.txt` – Date-specific exceptions (holidays / added or removed service); needed when calendar.txt is missing.
* `agency.txt` – Operator name/contact; useful for documentation and multi-operator cities.
* `feed_info.txt` – Feed publisher, version and validity dates; useful to judge how current the data is.

## Important columns per file

* `routes.txt`: route_id, route_short_name, route_long_name, route_type
* `trips.txt`: route_id, service_id, trip_id, direction_id, shape_id
* `stop_times.txt`: trip_id, arrival_time, departure_time, stop_id, stop_sequence
* `stops.txt`: stop_id, stop_name, stop_lat, stop_lon
* `calendar.txt`: service_id, monday..sunday, start_date, end_date
* `calendar_dates.txt`: service_id, date, exception_type
* `frequencies.txt`: trip_id, start_time, end_time, headway_secs
* `shapes.txt`: shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence


---
## Ahmedabad – AMTS + Janmarg BRTS

Download size: 4.64 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 978 | 5 | route_id, agency_id, route_short_name, route_long_name, route_type |
| trips.txt | required | True | 14323 | 6 | route_id, service_id, trip_id, trip_headsign, direction_id, shape_id |
| stop_times.txt | required | True | 646854 | 6 | trip_id, arrival_time, departure_time, stop_id, stop_sequence, timepoint |
| stops.txt | required | True | 3235 | 4 | stop_id, stop_name, stop_lat, stop_lon |
| calendar.txt | required | True | 1 | 10 | service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date |
| calendar_dates.txt | optional | False | 0 | 0 |  |
| frequencies.txt | optional | False | 0 | 0 |  |
| shapes.txt | optional | False | 0 | 0 |  |
| agency.txt | optional | True | 3 | 6 | agency_id, agency_name, agency_url, agency_timezone, agency_phone, agency_email |
| feed_info.txt | optional | True | 1 | 6 | feed_publisher_name, feed_publisher_url, feed_lang, feed_start_date, feed_end_date, feed_contact_url |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| routes.txt | route_short_name shared by >1 route_id (directions/variants) | 782 | 79.96 | Not an error: one bus line is often split into several route_ids |
| routes.txt | route with no trips | 6 | 0.61 |  |
| stop_times.txt | time >= 24:00:00 (valid GTFS: trip runs past midnight) | 1994 | 0.31 | Valid in GTFS; must be handled when extracting hour-of-day |
| stop_times.txt | identical arrival time at consecutive stops | 35178 | 5.44 | High values suggest times were interpolated/estimated by the publisher |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 1 | 100.0 | 1 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Bengaluru – BMTC

Download size: 44.39 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 4434 | 5 | route_long_name, route_short_name, agency_id, route_type, route_id |
| trips.txt | required | True | 57836 | 6 | route_id, service_id, trip_headsign, direction_id, shape_id, trip_id |
| stop_times.txt | required | True | 1540686 | 6 | trip_id, arrival_time, departure_time, stop_id, stop_sequence, stop_headsign |
| stops.txt | required | True | 9960 | 9 | stop_name, parent_station, zone_id, stop_id, stop_desc, stop_lat, stop_lon, location_type, platform_code |
| calendar.txt | required | True | 1 | 10 | monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date, service_id |
| calendar_dates.txt | optional | False | 0 | 0 |  |
| frequencies.txt | optional | False | 0 | 0 |  |
| shapes.txt | optional | True | 2492304 | 5 | shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence, shape_dist_traveled |
| agency.txt | optional | True | 1 | 5 | agency_id, agency_name, agency_url, agency_timezone, agency_lang |
| feed_info.txt | optional | True | 1 | 8 | feed_publisher_name, feed_publisher_url, feed_lang, feed_start_date, feed_end_date, feed_version, feed_contact_email, feed_contact_url |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| routes.txt | route with no trips | 18 | 0.41 |  |
| stops.txt | stop never used in stop_times | 12 | 0.12 |  |
| stop_times.txt | identical arrival time at consecutive stops | 25 | 0.0 | High values suggest times were interpolated/estimated by the publisher |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 1 | 100.0 | 1 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Chennai – Chennai unified feed (buses + others)

Download size: 9.82 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 5402 | 8 | route_id, route_short_name, route_long_name, route_type, agency_id, route_desc, route_color, route_text_color |
| trips.txt | required | True | 48435 | 6 | trip_id, route_id, service_id, direction_id, trip_headsign, shape_id |
| stop_times.txt | required | True | 1389081 | 5 | trip_id, arrival_time, departure_time, stop_id, stop_sequence |
| stops.txt | required | True | 6542 | 10 | stop_id, stop_name, stop_lat, stop_lon, stop_desc, zone_id, location_type, parent_station, platform_code, stop_code |
| calendar.txt | required | True | 12 | 10 | service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date |
| calendar_dates.txt | optional | True | 4 | 3 | date, service_id, exception_type |
| frequencies.txt | optional | False | 0 | 0 |  |
| shapes.txt | optional | True | 4231 | 4 | shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence |
| agency.txt | optional | True | 3 | 8 | agency_id, agency_name, agency_url, agency_timezone, agency_phone, agency_lang, agency_fare_url, agency_email |
| feed_info.txt | optional | True | 1 | 8 | feed_publisher_name, feed_publisher_url, feed_lang, feed_start_date, feed_end_date, feed_version, feed_contact_email, feed_contact_url |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| routes.txt | route_short_name shared by >1 route_id (directions/variants) | 3338 | 61.79 | Not an error: one bus line is often split into several route_ids |
| routes.txt | route_type is not a bus code (3 / 700-799 / 200-299 / 11) | 791 | 14.64 | Metro/rail/ferry rows mixed in with buses |
| routes.txt | route with no trips | 677 | 12.53 |  |
| stops.txt | stop never used in stop_times | 840 | 12.84 |  |
| stop_times.txt | time >= 24:00:00 (valid GTFS: trip runs past midnight) | 1904 | 0.14 | Valid in GTFS; must be handled when extracting hour-of-day |
| stop_times.txt | arrival later than departure at same stop | 4 | 0.0 |  |
| stop_times.txt | time goes backwards within a trip | 19 | 0.0 |  |
| calendar.txt | service already expired (end_date < 2026-10-18) | 1 | 8.33 | calendar covers 2021-04-20 to 2170-08-20 |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 2 | 16.67 | 12 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Delhi – Delhi buses (DTC / cluster)

Download size: 19.78 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 2964 | 5 | agency_id, route_id, route_long_name, route_short_name, route_type |
| trips.txt | required | True | 78515 | 4 | route_id, service_id, trip_id, shape_id |
| stop_times.txt | required | True | 3276092 | 5 | trip_id, arrival_time, departure_time, stop_id, stop_sequence |
| stops.txt | required | True | 6342 | 6 | stop_id, stop_code, stop_name, stop_lat, stop_lon, zone_id |
| calendar.txt | required | True | 1 | 10 | start_date, end_date, monday, tuesday, wednesday, thursday, friday, saturday, sunday, service_id |
| calendar_dates.txt | optional | False | 0 | 0 |  |
| frequencies.txt | optional | False | 0 | 0 |  |
| shapes.txt | optional | False | 0 | 0 |  |
| agency.txt | optional | True | 2 | 7 | agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone, agency_fare_url |
| feed_info.txt | optional | False | 0 | 0 |  |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| trips.txt | duplicate key ['trip_id'] | 8 | 0.01 |  |
| stops.txt | stop never used in stop_times | 75 | 1.18 |  |
| stop_times.txt | time >= 24:00:00 (valid GTFS: trip runs past midnight) | 20505 | 0.63 | Valid in GTFS; must be handled when extracting hour-of-day |
| stop_times.txt | identical arrival time at consecutive stops | 30025 | 0.92 | High values suggest times were interpolated/estimated by the publisher |
| calendar.txt | service already expired (end_date < 2026-10-18) | 1 | 100.0 | calendar covers 2022-01-01 to 2024-01-01 |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 1 | 100.0 | 1 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Hyderabad – TGSRTC

Download size: 10.55 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 1031 | 4 | route_id, route_long_name, agency_id, route_type |
| trips.txt | required | True | 44892 | 5 | route_id, trip_id, service_id, direction_id, trip_short_name |
| stop_times.txt | required | True | 1132807 | 6 | trip_id, stop_sequence, stop_id, departure_time, arrival_time, timepoint |
| stops.txt | required | True | 5028 | 6 | stop_id, stop_name, zone_id, stop_lat, stop_lon, stop_desc |
| calendar.txt | required | True | 1 | 10 | service_id, start_date, end_date, monday, tuesday, wednesday, thursday, friday, saturday, sunday |
| calendar_dates.txt | optional | False | 0 | 0 |  |
| frequencies.txt | optional | False | 0 | 0 |  |
| shapes.txt | optional | False | 0 | 0 |  |
| agency.txt | optional | True | 1 | 5 | agency_id, agency_name, agency_url, agency_timezone, agency_lang |
| feed_info.txt | optional | True | 1 | 8 | feed_publisher_name, feed_publisher_url, feed_contact_email, feed_contact_url, feed_lang, feed_start_date, feed_end_date, feed_version |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| stop_times.txt | time >= 24:00:00 (valid GTFS: trip runs past midnight) | 327387 | 28.9 | Valid in GTFS; must be handled when extracting hour-of-day |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 1 | 100.0 | 1 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Kochi – Kochi buses and boats

Download size: 5.48 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 473 | 9 | route_id, agency_id, route_short_name, route_long_name, route_desc, route_type, route_url, route_color, route_text_color |
| trips.txt | required | True | 933 | 6 | route_id, service_id, trip_id, trip_headsign, direction_id, shape_id |
| stop_times.txt | required | True | 46648 | 6 | trip_id, arrival_time, departure_time, stop_id, timepoint, stop_sequence |
| stops.txt | required | True | 3258 | 12 | stop_id, stop_code, stop_name, stop_desc, stop_lat, stop_lon, zone_id, stop_url, location_type, parent_station, stop_timezone, wheelchair_boarding |
| calendar.txt | required | True | 1 | 10 | service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date |
| calendar_dates.txt | optional | False | 0 | 0 |  |
| frequencies.txt | optional | True | 935 | 4 | trip_id, start_time, end_time, headway_secs |
| shapes.txt | optional | True | 550480 | 4 | shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence |
| agency.txt | optional | True | 4 | 8 | agency_id, agency_name, agency_url, agency_timezone, agency_lang, agency_phone, agency_fare_url, agency_email |
| feed_info.txt | optional | True | 1 | 9 | feed_publisher_name, feed_publisher_url, feed_lang, feed_start_date, feed_end_date, feed_version, default_lang, feed_contact_email, feed_contact_url |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| routes.txt | route_type is not a bus code (3 / 700-799 / 200-299 / 11) | 8 | 1.69 | Metro/rail/ferry rows mixed in with buses |
| calendar.txt | service already expired (end_date < 2026-10-18) | 1 | 100.0 | calendar covers 2022-09-26 to 2023-03-25 |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 1 | 100.0 | 1 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Pune – PMPML

Download size: 4.86 MB

| file | kind | available | records | columns | column_names |
|---|---|---|---|---|---|
| routes.txt | required | True | 315 | 5 | route_id, agency_id, route_short_name, route_long_name, route_type |
| trips.txt | required | True | 10128 | 6 | route_id, service_id, trip_id, trip_headsign, direction_id, shape_id |
| stop_times.txt | required | True | 429302 | 6 | trip_id, arrival_time, departure_time, stop_id, stop_sequence, timepoint |
| stops.txt | required | True | 6745 | 4 | stop_id, stop_name, stop_lat, stop_lon |
| calendar.txt | required | True | 1 | 10 | service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date |
| calendar_dates.txt | optional | False | 0 | 0 |  |
| frequencies.txt | optional | False | 0 | 0 |  |
| shapes.txt | optional | True | 256823 | 4 | shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence |
| agency.txt | optional | True | 1 | 6 | agency_id, agency_name, agency_url, agency_timezone, agency_phone, agency_email |
| feed_info.txt | optional | True | 1 | 6 | feed_publisher_name, feed_publisher_url, feed_lang, feed_start_date, feed_end_date, feed_contact_url |


### Data-quality observations (only checks with at least one finding)

| file | check | count | pct | note |
|---|---|---|---|---|
| stop_times.txt | time >= 24:00:00 (valid GTFS: trip runs past midnight) | 179 | 0.04 | Valid in GTFS; must be handled when extracting hour-of-day |
| calendar.txt | service runs all 7 days (no weekday/weekend distinction) | 1 | 100.0 | 1 service_id(s) in calendar.txt |


_Checks that found nothing are in `module1_quality_issues.csv`._


---
## Key observations (computed from the checks above)

* **Weekday/weekend cannot be separated** in these feeds (every service runs all 7 days, usually one service_id): ahmedabad (100%), bengaluru (100%), delhi (100%), hyderabad (100%), kochi (100%), pune (100%). The planned 'weekday vs weekend' feature will need another source or must be dropped for these cities.
* **Schedules already expired** (share of calendar rows with end_date before today): chennai (8.33%), delhi (100%), kochi (100%). These describe a past timetable, not today's.
* **Many times beyond 24:00:00** (valid GTFS, but must be handled when deriving hour-of-day): hyderabad (28.9%).
* **Duplicate keys:** delhi trips.txt (8).
* **Non-bus rows mixed into routes.txt:** chennai (14.64%), kochi (1.69%).
* GTFS contains **no passenger counts or occupancy** in any city – this limitation is unchanged by these checks.


---
## How to read these findings

* 'time >= 24:00:00' is **valid GTFS** (trip continues after midnight) – it must be handled later, not removed.
* A very high count of 'identical arrival time at consecutive stops' suggests the publisher interpolated/estimated stop times – such timings must not be treated as measured.
* 'service already expired' means the schedule dates in calendar.txt are in the past; the *pattern* of service can still be studied, but it is not a current timetable.
* 'trip with no stop_times' in a feed that has frequencies.txt usually means a frequency template rather than an error.
* Decisions on how to treat each issue (drop / fix / keep) are deferred to the data-cleaning module and will be justified there.
