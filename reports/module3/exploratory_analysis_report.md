# RouteRanker Module 3 — Vapi EDA

Service date: 2026-10-31
Route profiles: 22
Trip records: 461
Trips with usable departure times: 461

## Main observations

- Peak hour(s): [15], with 58 starts each. Lowest nonzero hour(s): [21], with 4 starts each. Hours with no recorded starts: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22, 23]. Zeros describe this dataset; they do not establish source completeness.
- Highest-count route(s): ['1832']; lowest-count route(s): ['1890', '1881', '1882', '1889', '1887', '1843', '1844', '1888']. A lower scheduled trip count alone does not prove underutilisation.
- Route(s) ['1868'] have the largest recorded stop count: 13. Completeness of recorded stop lists requires separate verification.
- 2 route(s) have median shape estimates below 1 km. This is a review threshold, not an invalidity rule.
- Shared-stop overlap uses intersection/union of recorded stop IDs. It ignores direction, order and nearby stops with different IDs. It does not establish redundancy.
- Not produced: original Vapi GTFS files were not uploaded.

## Data quality

Checks with findings: 0.
See tables/data_quality_summary.csv for counts and decisions.
No automatic correction of raw data was performed.

## Chart interpretations

### Vapi: distribution of scheduled_trip_count — 2026-10-31
File: charts/hist_scheduled_trip_count.png
22 routes have usable values. Minimum=9.00, maximum=62.00, mean=20.95, median=20.00. Differences describe the recorded route features.

### Vapi: spread of scheduled_trip_count — 2026-10-31
File: charts/box_scheduled_trip_count.png
Points beyond the box-plot whiskers are candidates for review, not automatically invalid observations.

### Vapi: distribution of distinct_stop_count — 2026-10-31
File: charts/hist_distinct_stop_count.png
22 routes have usable values. Minimum=2.00, maximum=13.00, mean=4.82, median=5.00. Differences describe the recorded route features.

### Vapi: spread of distinct_stop_count — 2026-10-31
File: charts/box_distinct_stop_count.png
Points beyond the box-plot whiskers are candidates for review, not automatically invalid observations.

### Vapi: distribution of median_trip_shape_length_km — 2026-10-31
File: charts/hist_median_trip_shape_length_km.png
22 routes have usable values. Minimum=0.20, maximum=22.08, mean=7.11, median=6.05. Differences describe the recorded route features.

### Vapi: spread of median_trip_shape_length_km — 2026-10-31
File: charts/box_median_trip_shape_length_km.png
Points beyond the box-plot whiskers are candidates for review, not automatically invalid observations.

### Vapi: distribution of departure_span_hours — 2026-10-31
File: charts/hist_departure_span_hours.png
22 routes have usable values. Minimum=6.90, maximum=8.97, mean=7.77, median=7.57. Differences describe the recorded route features.

### Vapi: spread of departure_span_hours — 2026-10-31
File: charts/box_departure_span_hours.png
Points beyond the box-plot whiskers are candidates for review, not automatically invalid observations.

### Vapi: recorded scheduled trip starts by service hour — 2026-10-31
File: charts/hourly_departures.png
Peak hour(s): [15], with 58 starts each. Lowest nonzero hour(s): [21], with 4 starts each. Hours with no recorded starts: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 22, 23]. Zeros describe this dataset; they do not establish source completeness.

### Vapi: scheduled trip starts by time period — 2026-10-31
File: charts/time_period_departures.png
Recorded starts: {'Morning': 0, 'Afternoon': 263, 'Evening': 194, 'Night': 4}. Morning=05–11, Afternoon=12–16, Evening=17–20, Night=21–04 by clock hour. Period lengths differ, so raw totals are not directly comparable hourly rates.

### Vapi: scheduled trips per route — 2026-10-31
File: charts/route_trip_comparison.png
Highest-count route(s): ['1832']; lowest-count route(s): ['1890', '1881', '1882', '1889', '1887', '1843', '1844', '1888']. A lower scheduled trip count alone does not prove underutilisation.

### Vapi: distinct stops per route — 2026-10-31
File: charts/route_stop_comparison.png
Route(s) ['1868'] have the largest recorded stop count: 13. Completeness of recorded stop lists requires separate verification.

### Vapi: Pearson correlation of route features — 2026-10-31
File: charts/correlation_heatmap.png
Positive values indicate features tend to increase together; negative values indicate opposite linear tendencies. Missing values use pairwise available observations. See sample-size table. Associations are descriptive, sensitive to outliers, and do not establish causation. Route IDs are excluded.

### Vapi: shape length versus scheduled trips — 2026-10-31
File: charts/length_vs_trips.png
Each point represents one route. Shape length may be incomplete; investigate very short geometry and outliers before interpreting the relationship.

## Further investigation

Verify short route geometry, sparse stop patterns, and any outliers against original source information.
Review shared-stop pairs in their direction and operating context.
No operational inefficiency is established by this EDA.