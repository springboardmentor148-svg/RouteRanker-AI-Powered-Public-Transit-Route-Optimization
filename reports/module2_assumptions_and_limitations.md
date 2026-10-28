# RouteRanker Module 2: Assumptions and Limitations

1. GTFS files describe scheduled transit service, not actual passenger counts.
2. Scheduled trips and departures must not be interpreted as passenger occupancy or crowding.
3. A trip's departure features use the first stop in stop_sequence.
4. GTFS times above 24:00 are retained as extended service hours.
5. Clock hour is service hour modulo 24; time-period labels use the clock hour.
6. Operating days are derived from matching trips.service_id to calendar.service_id.
7. Calendar exceptions are not applied unless calendar_dates.txt is available and implemented.
8. Missing or invalid data are reported; they are not automatically replaced with zero.
9. Route IDs and trip IDs are identifiers, not numeric measurements.
10. No shapes.txt file was found in the data directory. Route distances, where available,
    are approximate straight-line distances along consecutive stop coordinates. They are
    not road distances and can be inaccurate when coordinates are missing or stops are
    ordered incorrectly.
11. Operating-day flags indicate whether any matched service is active on a day; they
    do not prove that a bus runs on every calendar date in the feed's date range.
12. This script does not calculate passenger demand or true crowding.
13. Headway is calculated from scheduled first-stop departure times within each route_id and service_id group; it is not an observed real-world interval.
14. The first trip in each route/service group has no previous departure, so its headway is blank.
15. A zero headway means two or more trips share the same scheduled departure time; negative headways are not expected after sorting departures by time.
