# RouteRanker — Module 6
## Assumptions and Limitations

### 1. Model inference assumptions

- The saved KMeans and DBSCAN models from Module 5 are reused.
- The same three model features are used:
  trip_count, distinct_stop_count, average_stops_per_trip.
- The Module 4 feature representation is preserved.
- No new scaler is fitted for inference.
- KMeans assigns records using the saved cluster centroids.
- DBSCAN does not provide a native predict method. Approximate
  assignment uses saved core samples and the original epsilon radius.

### 2. Data alignment assumptions

- The eligible route-profile dataset contains 9,338 records.
- The 341 records with missing model features are excluded.
- The eligible route records were validated against the Module 4
  feature dataset.
- Numeric standardized feature values matched within numerical
  floating-point tolerance.
- City and route identifiers are used to associate predictions
  with route-level and hourly schedule records.

### 3. Candidate identification assumptions

- Low scheduled trip-count candidates are identified using the
  city-specific 10th percentile.
- High scheduled trip-count candidates are identified using the
  city-specific 90th percentile.
- DBSCAN noise and ambiguous assignments are additional review flags.
- These indicators do not prove route inefficiency.

### 4. Simulation assumptions

- An illustrative 10 percent increase is applied to low-trip-count
  candidate routes.
- Additional whole trips are distributed proportionally across
  existing hourly schedule records for each route.
- The original hourly dataset is preserved.
- The simulation is stored separately from the original schedule.
- The scenario is not an operational recommendation.

### 5. Data limitations

- Independent unseen route data was not available for this run.
- Passenger counts and passenger demand were not available.
- Vehicle capacity and occupancy data were not available.
- Actual operating costs and vehicle availability were not available.
- Reliable route-overlap and connectivity validation was not
  established for merging or splitting routes.
- Distance and geographic coverage were not included in the
  simulation comparison.
- Schedule-based trip counts represent planned service, not
  actual passenger usage.

### 6. Interpretation limitations

- KMeans cluster numbers are labels, not performance rankings.
- DBSCAN noise points are unusual in feature space, not necessarily
  bad or inefficient routes.
- High scheduled trip counts do not automatically mean overcrowding.
- Low scheduled trip counts do not automatically mean insufficient
  service.
- The simulated increase does not demonstrate improved passenger
  outcomes.

### 7. Future improvements

- Validate predictions using independent unseen GTFS data.
- Integrate passenger demand and vehicle capacity information.
- Include route geometry, route distance and stop coverage.
- Evaluate service changes using operational constraints.
- Validate route merging and splitting using stop overlap,
  connectivity and passenger journey information.
- Compare simulated schedules against observed operational outcomes.