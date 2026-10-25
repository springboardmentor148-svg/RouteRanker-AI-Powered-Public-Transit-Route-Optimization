# Module 3 - Findings and limitations

_Generated 2026-10-25._

## Patterns that need further investigation (candidates only)
A candidate is a route or pair that looks different in the **scheduled** data. None is a confirmed inefficiency: fewer trips does not mean underutilised, and overlapping routes may serve different passengers.

### Ahmedabad

* 117 route pairs share >= 80% of their stops (see `tables/ahmedabad_overlap_candidates.csv`).
* 174 routes have very few scheduled trips (lowest 10%, <= 2); 174 have fewer than 3 (`tables/ahmedabad_low_service_candidates.csv`).
* 27 routes have a scheduled speed outside 3-80 km/h (possible data problem).

### Bengaluru

* 1048 route pairs share >= 80% of their stops (see `tables/bengaluru_overlap_candidates.csv`). 1628 routes also share >= 80% of their path (shapes.txt).
* 1043 routes have very few scheduled trips (lowest 10%, <= 1); 2082 have fewer than 3 (`tables/bengaluru_low_service_candidates.csv`).
* 93 routes have a scheduled speed outside 3-80 km/h (possible data problem).

### Chennai

* 1118 route pairs share >= 80% of their stops (see `tables/chennai_overlap_candidates.csv`).
* 869 routes have very few scheduled trips (lowest 10%, <= 1); 1558 have fewer than 3 (`tables/chennai_low_service_candidates.csv`).
* 0 routes have a scheduled speed outside 3-80 km/h (possible data problem).

### Delhi

* 222 route pairs share >= 80% of their stops (see `tables/delhi_overlap_candidates.csv`).
* 424 routes have very few scheduled trips (lowest 10%, <= 4); 205 have fewer than 3 (`tables/delhi_low_service_candidates.csv`).
* 0 routes have a scheduled speed outside 3-80 km/h (possible data problem).
* Caveat: Scheduled speed is almost identical on all routes (10th-90th percentile 15.0-15.0 km/h), suggesting generated rather than operational stop times; durations and headways should be read as a model schedule.

### Hyderabad

* 99 route pairs share >= 80% of their stops (see `tables/hyderabad_overlap_candidates.csv`).
* 136 routes have very few scheduled trips (lowest 10%, <= 1); 269 have fewer than 3 (`tables/hyderabad_low_service_candidates.csv`).
* 778 routes have a scheduled speed outside 3-80 km/h (possible data problem).
* Caveat: 71% of routes have a median scheduled trip longer than 8 hours: the feed's 'trips' appear to be whole vehicle duties, so trip counts and headways are NOT comparable with cities whose trips are single runs.

### Kochi

* 114 route pairs share >= 80% of their stops (see `tables/kochi_overlap_candidates.csv`). 219 routes also share >= 80% of their path (shapes.txt).
* 464 routes have very few scheduled trips (lowest 10%, <= 34); 0 have fewer than 3 (`tables/kochi_low_service_candidates.csv`).
* 0 routes have a scheduled speed outside 3-80 km/h (possible data problem).
* Caveat: Scheduled speed is almost identical on all routes (10th-90th percentile 20.8-22.4 km/h), suggesting generated rather than operational stop times; durations and headways should be read as a model schedule.
* Caveat: Trip counts come from expanding frequency templates (a bus every N minutes), so routes look uniform because the publisher used a uniform pattern; this is not measured service.

### Pune

* 8 route pairs share >= 80% of their stops (see `tables/pune_overlap_candidates.csv`). 18 routes also share >= 80% of their path (shapes.txt).
* 44 routes have very few scheduled trips (lowest 10%, <= 5); 0 have fewer than 3 (`tables/pune_low_service_candidates.csv`).
* 2 routes have a scheduled speed outside 3-80 km/h (possible data problem).
* Caveat: Scheduled speed is almost identical on all routes (10th-90th percentile 18.2-20.6 km/h), suggesting generated rather than operational stop times; durations and headways should be read as a model schedule.

## What the dataset supports
* Distinct scheduled trips, stops, estimated lengths, operating spans and hourly/period patterns per route.
* Which routes share stops (all cities) or road corridors (cities with shapes).
* Which feeds have structural caveats (below).

## What it does not support
* Passenger demand, crowding, load factors, revenue, or any 'overcrowded' / 'underutilised' label.
* Whether overlapping routes are redundant, or whether a route should be merged, split or cut.
* Weekday-vs-weekend differences in feeds whose calendar says every day is identical.

## Assumptions and limitations of the analysis
* Time periods: morning 05:00-11:59, afternoon 12:00-16:59, evening 17:00-20:59, night 21:00-04:59, by first departure.
* `n_trips` counts distinct trips over all service patterns of a feed; per-weekday views come from calendar.txt (calendar_dates exceptions not applied).
* Route length from stop coordinates is a straight-line lower bound; shapes are used where available and plausible.
* Stop overlap = Jaccard similarity of stop sets; path overlap = Jaccard similarity of ~200 m grid cells along shapes.txt. Same-name and opposite-direction routes are excluded.
* Feeds are community-compiled or old (Delhi/Kochi calendars 2022-24); Hyderabad trips look like vehicle duties; Delhi, Kochi and Pune show near-constant scheduled speeds.
* 7 cities only: the Lepton/Datarade dataset (23 cities) is paid and was not available; Mumbai, Rajkot and Hubli-Dharwad have no open feed.

## Next step
Module 4 (data preprocessing) should decide, with the mentor, how to treat flagged rows and non-comparable feeds, and whether a real ridership source can be obtained before any model uses the word 'demand'.
