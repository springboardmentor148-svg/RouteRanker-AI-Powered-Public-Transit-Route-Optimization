# RouteRanker — Module 2
## Assumptions and Limitations

### 1. Assumptions

1. The GTFS files supplied for each city represent the available
   public transit schedule information for that dataset.

2. route_id identifies a route within its city, and trip_id
   identifies a scheduled trip within its source dataset.

3. Distinct trip counts represent the number of unique scheduled
   trips associated with a route, not passenger numbers.

4. Stops served are counted using distinct stop IDs referenced
   by the route's trips in stop_times.txt.

5. Scheduled departure activity is measured using the first
   recorded stop of each trip, ordered by stop_sequence.

6. Clock-hour analysis groups departure times into hours 0–23.
   GTFS times above 24 hours are mapped to their corresponding
   clock hour for hourly activity analysis.

7. Operating-day features are calculated from calendar.txt.
   They are considered reliable only where the required service
   calendar records and daily flags are available and valid.

8. Route distance uses GTFS shape geometry when a usable shape
   can be linked to trips. Otherwise, the implementation may
   estimate distance from consecutive stop coordinates.

9. Missing optional GTFS fields are retained as missing when
   they cannot be derived reliably. Missing distances are not
   automatically replaced with zero.

10. Raw GTFS source files are kept separate from processed
    feature-engineered outputs.

### 2. Limitations

1. Some city datasets do not contain calendar_dates.txt.
   Service exceptions and special-date changes are therefore
   not fully represented in the operating-day analysis.

2. Some datasets lack shapes.txt or have trips with missing
   or unmatched shape_id values. Reliable shape-based distance
   estimates may not be available for every route.

3. Stop-coordinate distance estimates use straight-line
   distances between consecutive stops. They do not represent
   actual road distance and may underestimate the true journey.

4. A route's estimated distance may vary across trips. The
   route-level value is a summary of available trip estimates,
   not a guarantee that every trip follows the same path.

5. Hourly departure counts describe scheduled trips recorded
   in the supplied GTFS data. They do not establish actual
   service operation, delays, cancellations, or real-time traffic.

6. Trip counts are not the same as trip frequency or headway.
   Headway requires the time differences between consecutive
   scheduled departures and has not been calculated here.

7. GTFS schedule data does not provide passenger counts or
   vehicle occupancy. It cannot independently establish
   passenger demand or overcrowding.

8. Missing values, inconsistent identifiers, and duplicate
   records may affect individual calculations. The data quality
   reports should be reviewed before using the dataset for
   further modelling.

9. Calendar service analysis uses calendar.txt. Because
   calendar_dates.txt exceptions are not incorporated into
   the current operating-day calculation, special service
   dates may be missed.

10. Route-ranking and shortest-path recommendations are not
    established by this feature-engineering dataset alone.
    A separate routing and ranking method is required.

### 3. Interpretation Notes

- Route IDs are identifiers, not numerical measurements.
- A missing distance means that a usable estimate was unavailable.
- An hourly count of zero means no departure was recorded in
  that hour when hourly data is available.
- A missing operating-day value should not be interpreted as
  zero operating days.
- Results depend on the completeness and consistency of the
  source GTFS data.

### 4. Output Files

The Module 2 processing workflow produces route profiles,
time-feature files, hourly departure counts, operating-day
summaries, distance estimates, a combined feature-engineered
dataset, a feature dictionary, and data quality reports.

These outputs should be checked before they are used in
subsequent RouteRanker modules.
