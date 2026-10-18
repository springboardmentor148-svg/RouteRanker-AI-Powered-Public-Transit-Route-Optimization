# Module 1 – How the GTFS files are connected

```
calendar.txt ──service_id──▶ trips.txt ◀──route_id── routes.txt
                              │
                           trip_id
                              ▼
stops.txt ◀──stop_id── stop_times.txt  (one row per stop visit of a trip, ordered by stop_sequence)
```

| Link | Meaning | Join key |
|---|---|---|
| routes → trips | one route has many scheduled trips (directions, times of day) | `route_id` |
| trips → stop_times | one trip visits an ordered list of stops with arrival/departure times | `trip_id` (+ `stop_sequence`) |
| stop_times → stops | each visit refers to a physical stop with coordinates | `stop_id` |
| trips → calendar | decides on which weekdays/date range the trip runs | `service_id` |
| frequencies → trips (optional) | 'a bus every N seconds' template for a trip | `trip_id` |
| shapes → trips (optional) | road geometry of a trip | `shape_id` |

**Example:** a trip may reach Stop A at 08:00, Stop B at 08:15, Stop C at 08:30 – three rows in `stop_times.txt` with the same `trip_id`, increasing `stop_sequence`, and three different `stop_id`s that are looked up in `stops.txt` for names and coordinates.

## Measured on the collected feeds

| city | routes | trips | trips_per_route_median | trips_per_route_max | stop_times | stops_per_trip_median | stops | stop_times_matching_stops_pct | services_in_calendar | trips_matching_calendar_pct |
|---|---|---|---|---|---|---|---|---|---|---|
| ahmedabad | 978 | 14323 | 8.0 | 134 | 646854 | 43.0 | 3235 | 100.0 | 1 | 100.0 |
| bengaluru | 4434 | 57836 | 3.0 | 398 | 1540686 | 26.0 | 9960 | 100.0 | 1 | 100.0 |
| chennai | 5402 | 48435 | 3.0 | 210 | 1389081 | 28.0 | 6542 | 100.0 | 12 | 100.0 |
| delhi | 2964 | 78515 | 18.0 | 170 | 3276092 | 43.0 | 6342 | 100.0 | 1 | 100.0 |
| hyderabad | 1031 | 44892 | 8.0 | 2087 | 1132807 | 25.0 | 5028 | 100.0 | 1 | 100.0 |
| kochi | 473 | 933 | 2.0 | 3 | 46648 | 50.0 | 3258 | 100.0 | 1 | 100.0 |
| pune | 315 | 10128 | 22.0 | 175 | 429302 | 42.0 | 6745 | 100.0 | 1 | 100.0 |


`trips_per_route_*` shows that routes have many trips; `stops_per_trip_median` the typical trip length; the two `*_matching_*_pct` columns show how cleanly the identifiers link (100 = every reference resolves). Gaps are listed in the inventory report.

## Things to keep in mind
* A *route_id* in many Indian feeds is a **route pattern** (one direction/variant), not a whole bus line; several route_ids can share a `route_short_name`.
* GTFS holds **scheduled** service only – no passenger counts, occupancy or live traffic. Nothing in this module estimates or invents them.
