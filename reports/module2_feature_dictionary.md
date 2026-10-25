# Module 2 - Feature dictionary

_Generated 2026-10-25._ `direct` = a field copied from the GTFS files; `derived` = calculated by us. IDs (route_id, trip_id, stop_id) are identifiers, never numeric measurements.

**Time periods (clearly defined rules):** morning 05:00-11:59; afternoon 12:00-16:59; evening 17:00-20:59; night 21:00-04:59. GTFS times can exceed 24:00:00 (trip runs past midnight); they are converted to seconds first and the clock hour is `(seconds // 3600) % 24`.


## route_features.csv

| feature | data type | numeric / categorical | direct / derived | source file(s) | meaning and calculation |
|---|---|---|---|---|---|
| city | text | categorical | derived | folder name | City the feed belongs to (added when saving). |
| route_id | text | identifier | direct | routes.txt | Route identifier. An ID, not a measurement; never used as a number. In many Indian feeds one route_id = one direction/variant. |
| route_name | text | categorical | derived | routes.txt | route_short_name, else route_long_name, else route_id (label only). |
| route_type | integer code | categorical | direct | routes.txt | GTFS vehicle type code (3 = bus). |
| n_trips | integer | numeric | derived | trips.txt (+stop_times.txt) | COUNT of DISTINCT trip_id of the route (not rows of stop_times). Counts all services in the feed together; frequency templates are expanded to explicit trips. |
| n_unique_stops | integer | numeric | derived | stop_times.txt + trips.txt | Distinct stop_id served by any trip of the route. |
| median_stops_per_trip | float | numeric | derived | stop_times.txt | Median number of stop calls per trip. |
| n_service_ids | integer | numeric | derived | trips.txt | Distinct service_id (calendar patterns) used by the route's trips. |
| n_directions | integer | numeric | derived | trips.txt | Distinct direction_id values (missing if the feed has no direction_id). |
| trips_from_frequency | integer | numeric | derived | frequencies.txt | Trips created by expanding frequencies.txt templates (0 if the feed lists every trip). |
| first_departure_h | float (hours) | numeric | derived | stop_times.txt | Earliest first-stop departure over all trips, decimal hours (can exceed 24 = after midnight). |
| last_departure_h | float (hours) | numeric | derived | stop_times.txt | Latest first-stop departure, decimal hours. |
| service_span_h | float (hours) | numeric | derived | stop_times.txt | last_departure_h - first_departure_h: length of the scheduled operating day. |
| n_active_hours | integer | numeric | derived | stop_times.txt | Number of clock hours (0-23) in which at least one trip starts. |
| peak_hour | integer 0-23 | categorical | derived | stop_times.txt | Clock hour with the most trip starts (ties: earliest hour). |
| peak_hour_trips | integer | numeric | derived | stop_times.txt | Number of trips starting in peak_hour. |
| trips_per_active_hour | float | numeric | derived | stop_times.txt | TRIP FREQUENCY: n_trips / n_active_hours (scheduled trips per hour in hours the route operates). |
| trips_morning | integer | numeric | derived | stop_times.txt | Trips starting 05:00-11:59. |
| trips_afternoon | integer | numeric | derived | stop_times.txt | Trips starting 12:00-16:59. |
| trips_evening | integer | numeric | derived | stop_times.txt | Trips starting 17:00-20:59. |
| trips_night | integer | numeric | derived | stop_times.txt | Trips starting 21:00-04:59. |
| median_headway_min | float (minutes) | numeric | derived | stop_times.txt | HEADWAY: median gap between consecutive scheduled departures of the same route_id and service_id (gaps of 0 = simultaneous departures are ignored). Missing if fewer than 2 distinct departure times. |
| trips_monday, trips_tuesday, trips_wednesday, trips_thursday, trips_friday, trips_saturday, trips_sunday | integer | numeric | derived | trips.txt + calendar.txt | Trips whose service runs on that weekday (one column per day). Missing columns if the feed has no calendar.txt. calendar_dates.txt exceptions are NOT applied. |
| avg_trips_per_weekday | float | numeric | derived | calendar.txt | Mean of trips_monday..trips_friday. |
| avg_trips_per_weekend_day | float | numeric | derived | calendar.txt | Mean of trips_saturday and trips_sunday. |
| weekend_to_weekday_ratio | float | numeric | derived | calendar.txt | avg_trips_per_weekend_day / avg_trips_per_weekday (missing if no weekday trips). 1.0 means the schedule is identical on all days. |
| length_km | float (km) | numeric | derived | shapes.txt else stops.txt | ESTIMATED route length of the longest scheduled variant: shape path length when shapes.txt has it and it passes the sanity check (0.5x-3x the stop-based length), else stop-to-stop straight-line length. See length_method. |
| length_km_stops | float (km) | numeric | derived | stops.txt + stop_times.txt | Sum of straight-line (haversine) distances between consecutive stops of the longest trip. A lower bound of road distance. |
| length_km_shape | float (km) | numeric | derived | shapes.txt | Length of the shape polyline (haversine along shape points) of the route's longest shape. Missing if the feed has no shapes or the trip has no shape_id. |
| length_method | text | categorical | derived | - | How length_km was obtained: shapes.txt / stop coordinates (straight-line, approximate) / stop coordinates (shape failed sanity check). |
| stops_per_km | float | numeric | derived | - | n_unique_stops / length_km (length clipped at 0.5 km to avoid division blow-ups). |
| avg_trip_duration_min | float (min) | numeric | derived | stop_times.txt | Mean scheduled duration (last arrival - first departure). |
| median_trip_duration_min | float (min) | numeric | derived | stop_times.txt | Median scheduled duration. |
| avg_speed_kmh | float | numeric | derived | - | length_km / median_trip_duration_min (scheduled, not measured speed). |
| speed_implausible | boolean | categorical | derived | - | True if avg_speed_kmh > 80 or < 3 - flags a possible data problem; the row is kept. |
| overlap_partner | text | identifier | derived | stop_times.txt | route_id of the route sharing the most stops (excludes routes with the same name and opposite-direction twins). |
| overlap_partner_name | text | categorical | derived | - | route_name of overlap_partner. |
| max_stop_overlap | float 0-1 | numeric | derived | stop_times.txt | Jaccard similarity of the stop sets of the route and overlap_partner. Shared stops do NOT prove redundancy. |
| overlap_share_of_route | float 0-1 | numeric | derived | stop_times.txt | Share of this route's stops that the partner also serves. |
| mean_routes_per_stop | float | numeric | derived | stop_times.txt | Average number of routes calling at the stops of this route (connectivity of its stops). |
| has_time_backwards_trip | boolean | categorical | derived | stop_times.txt | True if any trip of the route has arrival times going backwards (data-quality flag). |
| sparse_schedule | boolean | categorical | derived | - | True if n_trips < 3. Descriptive flag only; NOT a statement that the route is inefficient. |


## route_hour_features.csv

| feature | data type | numeric / categorical | direct / derived | source file(s) | meaning and calculation |
|---|---|---|---|---|---|
| route_id / hour | text / integer 0-23 | identifier | derived | stop_times.txt | One row per route and clock hour in which the route has a trip start or a stop call. |
| trips_all | integer | numeric | derived | trips.txt | Distinct trips whose first departure is in that hour (all services of the feed). |
| trips_typical_weekday | integer | numeric | derived | calendar.txt | As trips_all but only trips whose service runs on Wednesday (a typical weekday). |
| trips_typical_sunday | integer | numeric | derived | calendar.txt | As trips_all but only trips whose service runs on Sunday. |
| median_headway_min | float (min) | numeric | derived | stop_times.txt | Median gap before trips starting in this hour (same route_id and service_id). |
| scheduled_stop_visits | integer | numeric | derived | stop_times.txt | Number of scheduled stop calls with arrival in that hour. This is timetable activity, NOT passenger counts. |
| period | text | categorical | derived | - | morning 05:00-11:59, afternoon 12:00-16:59, evening 17:00-20:59, night 21:00-04:59. |


## trip_features.csv

| feature | data type | numeric / categorical | direct / derived | source file(s) | meaning and calculation |
|---|---|---|---|---|---|
| start_hour / start_minute | integer | numeric | derived | stop_times.txt | Hour (0-23) and minute of the first-stop departure; GTFS times >= 24:00:00 are wrapped (25:10 -> hour 1). |
| departure_clock | text HH:MM | categorical | derived | stop_times.txt | start_hour:start_minute as text. |
| period | text | categorical | derived | - | Time period of the first departure (rules above). |
| starts_after_midnight | boolean | categorical | derived | stop_times.txt | True if the departure time is written as >= 24:00:00. |
| duration_min | float | numeric | derived | stop_times.txt | Scheduled duration = last arrival - first departure. |
| runs_monday .. runs_sunday | boolean | categorical | derived | calendar.txt | Whether the trip's service runs on that weekday. |
| service_day_type | text | categorical | derived | calendar.txt | weekday_only / weekend_only / weekday_and_weekend / unknown (service not in calendar.txt). |
| from_frequency / time_backwards | boolean | categorical | derived | frequencies.txt / stop_times.txt | Trip created from a frequency template / arrival times go backwards (flag). |


## stop_usage.csv

| feature | data type | numeric / categorical | direct / derived | source file(s) | meaning and calculation |
|---|---|---|---|---|---|
| scheduled_visits | integer | numeric | derived | stop_times.txt | Total scheduled stop calls at the stop. NOT passenger boardings. |
| n_routes | integer | numeric | derived | stop_times.txt + trips.txt | Distinct routes calling at the stop. |
| peak_hour / peak_hour_visits | integer | numeric | derived | stop_times.txt | Clock hour with the most scheduled calls and their number. |
| stop_id, stop_name, stop_lat, stop_lon | text / float | identifier | direct | stops.txt | Direct fields; coordinates validated (inside India, not 0,0). |


**Undocumented columns (should be empty):** none
