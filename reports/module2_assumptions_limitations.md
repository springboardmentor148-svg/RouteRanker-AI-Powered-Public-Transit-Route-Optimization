# Module 2 - Assumptions and limitations

_Generated 2026-10-25._

## What the features are - and are not

* All features come from **scheduled** GTFS data. `n_trips`, `trips_per_active_hour`, `median_headway_min` and `scheduled_stop_visits` describe the planned service. They are **not passenger counts, occupancy or demand**, and no ridership is estimated anywhere in this module.
* A route with few scheduled trips is not automatically inefficient, and a route with many is not automatically overcrowded.

## Assumptions and decisions

* **Bus scope:** routes whose route_type is not a bus code (3, 700-799, 200-299, 11) are excluded from the cleaned tables (visible in the cleaning report); they stay in the raw files.
* **Distinct trips:** `n_trips` counts distinct `trip_id`. Feeds with several service patterns (e.g. seasonal or holiday schedules) are counted together, so `n_trips` can exceed the trips run on one actual day; `trips_monday..trips_sunday` give the per-weekday view from calendar.txt.
* **Frequency-based feeds** (Kochi) are expanded into explicit trips; each expanded trip is a *scheduled* departure derived from the published headway.
* **Time periods** use the fixed rules in the feature dictionary and are based on the trip's first departure.
* **Route length** uses `shapes.txt` when present and plausible (0.5x-3x of the stop-based length); otherwise the straight-line sum between consecutive stops of the longest trip. Straight-line length is shorter than the road distance. Shares by city:

| city | stop coordinates (straight-line, approximate) | shapes.txt | stop coordinates (shape failed sanity check) |
|---|---|---|---|
| ahmedabad | 100.0% | 0.0% | 0.0% |
| bengaluru | 0.0% | 99.0% | 1.0% |
| chennai | 100.0% | 0.0% | 0.0% |
| delhi | 100.0% | 0.0% | 0.0% |
| hyderabad | 100.0% | 0.0% | 0.0% |
| kochi | 0.0% | 100.0% | 0.0% |
| pune | 0.0% | 99.4% | 0.6% |

* **Overlap** is based on shared stops (Jaccard similarity) and excludes routes with the same name and opposite-direction twins. Shared stops do not prove that two routes are redundant.

## Limitations

* **No passenger data** in any collected feed. Overcrowding / underutilisation cannot be concluded from schedules alone.
* **Weekday vs weekend:** computed from calendar.txt only. `calendar_dates.txt` exceptions (holidays) are not applied. Cities whose services all run every day show a ratio of exactly 1.0 - that is what the schedule says, not a computation artefact: ahmedabad, bengaluru, delhi, hyderabad, kochi, pune.
* **Expired schedules:** Delhi and Kochi calendars are from 2022-24 (see Module 1 report). The features describe that past timetable.
* **Community-compiled feeds** (Ahmedabad, Bengaluru, Chennai, Kochi) may have been generated from public timetables or estimates by their maintainers; timing quality is unverified. Identical consecutive arrival times seen in Module 1 suggest interpolated times in some feeds.
* **Stop usage** = scheduled calls per stop, not boardings.
* Lepton Software / Datarade data could not be obtained (paid), so results cover 7 cities, not 23.

## Timing plausibility check (what the schedules themselves look like)

| city | median_trip_min | share_trips_over_8h | speed_p10_kmh | speed_p90_kmh |
|---|---|---|---|---|
| ahmedabad | 75.00 | 0.01 | 11.50 | 46.10 |
| bengaluru | 60.00 | 0.00 | 13.40 | 26.50 |
| chennai | 51.00 | 0.00 | 14.60 | 31.20 |
| delhi | 89.50 | 0.00 | 15.00 | 15.00 |
| hyderabad | 768.20 | 0.68 | 1.00 | 5.80 |
| kochi | 65.00 | 0.00 | 20.80 | 22.40 |
| pune | 61.40 | 0.00 | 18.20 | 20.60 |

Scheduled speed = estimated route length / median scheduled trip duration.

* **delhi:** scheduled speed is almost identical for every route (10th-90th percentile: 15.0-15.0 km/h), which suggests that stop times may have been *generated with a near-constant speed* rather than taken from an operational timetable (to be verified with the publisher). If so, durations in this feed describe a model schedule, not measured operations.
* **hyderabad:** 68% of trips last more than 8 hours (median 768 min) and the typical scheduled speed is implausibly low. The feed's 'trips' therefore appear to be whole vehicle duties (many round trips chained under one trip_id), so trip counts and headways of this city are **not comparable** with cities whose trips are single runs. To be confirmed with the publisher.
* **kochi:** scheduled speed is almost identical for every route (10th-90th percentile: 20.8-22.4 km/h), which suggests that stop times may have been *generated with a near-constant speed* rather than taken from an operational timetable (to be verified with the publisher). If so, durations in this feed describe a model schedule, not measured operations.
* **pune:** scheduled speed is almost identical for every route (10th-90th percentile: 18.2-20.6 km/h), which suggests that stop times may have been *generated with a near-constant speed* rather than taken from an operational timetable (to be verified with the publisher). If so, durations in this feed describe a model schedule, not measured operations.
* **Chennai:** shapes.txt exists but only contains 13 metro (CMRL) shapes; bus trips carry no shape_id, so bus route lengths come from stop coordinates.