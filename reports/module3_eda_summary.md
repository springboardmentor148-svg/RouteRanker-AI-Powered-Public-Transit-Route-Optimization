# RouteRanker — Module 3: Exploratory Data Analysis

## Objective
Explore the GTFS-based route and service indicators for Ahmedabad, Chennai,
Hyderabad, Mumbai, and Pune to understand scheduled service patterns and
identify data that may need further review.

## Route comparison
Routes differ in scheduled trip counts, stop counts, and estimated
straight-line distances. Comparisons should be made within each city because
the cities have different service scales and route records.

## Routes without scheduled trips
The route feature data contains:
- Ahmedabad: 6 routes with zero scheduled trips
- Chennai: 677 routes with zero scheduled trips
- Hyderabad: 0 routes with zero scheduled trips
- Mumbai: 323 routes with zero scheduled trips
- Pune: 0 routes with zero scheduled trips

These records should be reviewed against the source GTFS data. A route with
zero scheduled trips is not automatically an underused or inefficient route.

## Outlier screening
The IQR check flagged:
- Ahmedabad: 76 routes
- Chennai: 699 routes
- Hyderabad: 138 routes
- Mumbai: 58 routes
- Pune: 2 routes

These are statistical flags for further review, not confirmed errors or
inefficient routes.

## Stop-location exploration
Stop coordinates were available for all five cities. The saved plot
`module3_stop_location_map.png` shows stop locations by city. No `shapes.txt`
was found, so the current data supports plotting stop locations but not
drawing actual GTFS route paths.

## Interpretation limits
Scheduled trip counts describe the timetable data, not actual operated trips
or passenger demand. Estimated straight-line distance is not the road distance
or actual route length. These indicators should not be treated as direct
measures of overcrowding or route efficiency.

## Next step
Use the reviewed and documented route indicators as inputs for Module 4
preprocessing, while retaining the noted data limitations.

## Hourly service pattern
The hourly summary was grouped by clock hour using service hour modulo 24,
so GTFS service times after midnight are included in their corresponding
clock-hour group. The busiest clock hour in the combined summary was 07:00,
with 14,564 scheduled trips.

The reported time-period totals were:
- Morning (05:00–11:59): 88,210 scheduled trips
- Afternoon (12:00–16:59): 61,010 scheduled trips
- Evening (17:00–20:59): 46,485 scheduled trips
- Night/early morning (remaining hours): 21,153 scheduled trips

These totals represent scheduled service in the GTFS data, not passenger
demand or confirmed operated trips.

## Weekday/weekend comparison
For Chennai, the calendar-based summary showed an average of 48,255 scheduled
trips per weekday and 47,896 per weekend day. The weekend-day average was
359 trips lower (about 0.7%).

This comparison is based on calendar service assignments. It does not confirm
that trips operated as scheduled or measure passenger demand. Comparable
weekday/weekend findings were not established for the other cities in this
summary.

## Saved hourly chart
The hourly-pattern chart is saved as `module3_hourly_trip_pattern.png`.
