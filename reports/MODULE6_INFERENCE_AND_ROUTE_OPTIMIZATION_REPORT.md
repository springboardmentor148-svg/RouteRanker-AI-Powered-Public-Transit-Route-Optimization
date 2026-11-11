
# RouteRanker — Module 6
## Model Inference and Route Optimization

### 1. Objective

Module 6 applies the trained Module 5 clustering models to the available
route feature dataset, identifies routes for further investigation, and
evaluates an illustrative schedule-based optimization scenario.

### 2. Data and model inference

- Eligible route records: **9338**
- Hourly schedule records: **73039**
- Cities: Bangalore, Delhi, Hyderabad, Mumbai and Pune.
- KMeans model: loaded from the saved Module 5 model.
- DBSCAN model: loaded from the saved Module 5 model.
- KMeans inference: nearest-centroid prediction using the original
  three Module 5 features.
- DBSCAN inference: approximate assignment using saved core samples
  and the model's epsilon neighborhood.

The inference dataset contains the same records used during Module 5
training. Therefore, agreement with the original cluster assignments
validates reproduction of previous assignments, not generalization to
independent unseen data.

### 3. KMeans cluster distribution

|   kmeans_cluster |   route_count |
|-----------------:|--------------:|
|                0 |          4420 |
|                1 |          4657 |
|                2 |           261 |

Cluster identifiers are descriptive group labels. They are not route
quality rankings.

### 4. DBSCAN neighborhood assignment distribution

|   dbscan_cluster |   route_count |
|-----------------:|--------------:|
|               -1 |           126 |
|                0 |          9182 |
|                1 |            30 |

Noise points are routes that were not assigned to a DBSCAN core-point
neighborhood. Ambiguous assignments are flagged for further review.

### 5. Route optimization candidates

The candidate analysis uses city-specific scheduled trip-count
percentiles and clustering indicators.

Total candidate records: **2680**

| city      |   candidate_records |
|:----------|--------------------:|
| Bangalore |                1485 |
| Delhi     |                 723 |
| Hyderabad |                 261 |
| Mumbai    |                 133 |
| Pune      |                  78 |

These records are candidates for manual investigation. Low or high
scheduled trip counts and DBSCAN noise do not independently prove
that a route is inefficient.

### 6. Schedule simulation

An illustrative scenario increased scheduled trips by 10 percent for
routes flagged as low scheduled-trip-count candidates.

- Original scheduled trips: **290,443**
- Simulated scheduled trips: **292,174**
- Additional simulated trips: **1,731**
- Percentage increase: **0.60%**
- Routes receiving simulated increases: **1,711**

This scenario is an arithmetic simulation, not an operational
recommendation. Passenger demand and vehicle capacity were not
available to justify actual service increases.

### 7. City-wise comparison

| city      |   route_count |   original_trips |   simulated_trips |   additional_trips |   percentage_increase |
|:----------|--------------:|-----------------:|------------------:|-------------------:|----------------------:|
| Bangalore |          4416 |            57836 |             58879 |               1043 |                  1.8  |
| Delhi     |          2964 |            78507 |             78931 |                424 |                  0.54 |
| Hyderabad |          1031 |            44892 |             45028 |                136 |                  0.3  |
| Mumbai    |           612 |            99080 |             99164 |                 84 |                  0.08 |
| Pune      |           315 |            10128 |             10172 |                 44 |                  0.43 |

### 8. Visualizations

The following charts were generated:

- module6_original_vs_simulated.png
- module6_additional_trips_by_city.png
- module6_percentage_increase_by_city.png
- module6_kmeans_city_distribution.png
- module6_dbscan_noise_percentage.png
- module6_kmeans_cluster_profiles.png

### 9. Limitations

1. Independent unseen route data was not available for this inference run.
2. Passenger demand and vehicle capacity data were unavailable.
3. Scheduled trips represent service supply, not passenger demand.
4. Route merging and splitting were not simulated because sufficient
   route-overlap, connectivity and operational validation was not
   established.
5. The simulation does not establish that additional trips are needed.
6. Estimated distance and geographic coverage were not included in
   the simulation comparison.
7. The 341 route-profile records with missing model features were
   excluded from model inference.

### 10. Conclusion

Module 6 successfully loaded the saved Module 5 models, reproduced
cluster assignments for 9,338 eligible route records, generated
route-review candidates, and produced a separate simulated hourly
schedule.

The scenario increased scheduled trips by 0.60%.
All findings should be treated as analytical evidence for further
investigation rather than confirmed operational improvements.
