# Module 5 - Clustering report (KMeans and DBSCAN)

_Generated 2026-11-07._ Data: Module-4 preprocessed routes (10,466 training, 2,600 validation; 25 standardised features; Hyderabad excluded in Module 4). **A cluster is a group of routes with similar *scheduled* service - not a performance class and not an optimisation recommendation.** GTFS has no passenger data, so nothing here says that a route is overcrowded or underutilised.

## How the algorithms work (short)

* **KMeans:** choose K; place K centroids; assign each route to its nearest centroid; move each centroid to the mean of its routes; repeat until assignments stop changing. Needs scaled features (done in Module 4) because it uses Euclidean distance.
* **DBSCAN:** a route is a *core point* if at least `min_samples` routes lie within distance `eps`; clusters grow by connecting core points and their neighbours; routes that belong to no dense region are *noise* (-1). No K is needed.

## KMeans

### Choosing K (training routes, K = 2..10)

| k | inertia | silhouette | davies_bouldin | smallest_cluster_share |
|---|---|---|---|---|
| 2 | 148,095.49 | 0.16 | 1.95 | 0.37 |
| 3 | 129,605.22 | 0.16 | 1.99 | 0.24 |
| 4 | 120,278.92 | 0.16 | 1.86 | 0.13 |
| 5 | 112,681.17 | 0.15 | 1.94 | 0.12 |
| 6 | 105,766.37 | 0.17 | 1.68 | 0.08 |
| 7 | 100,799.28 | 0.18 | 1.65 | 0.03 |
| 8 | 96,190.97 | 0.15 | 1.75 | 0.03 |
| 9 | 91,968.45 | 0.16 | 1.68 | 0.03 |
| 10 | 88,314.34 | 0.16 | 1.70 | 0.03 |


![k selection](figures/module5/m5_01_kmeans_k_selection.png)

* **Elbow method:** the inertia curve bends most at K = 5.
* **Silhouette:** the values are low for every K (0.15-0.18); the highest is K = 7. Low scores mean the routes form a continuum rather than clearly separated groups.
* **Davies-Bouldin:** lowest (best) at K = 7 (1.65).
* **Decision:** K = **7** (best silhouette for K in 3-8 with no cluster smaller than 2% of the routes). The elbow K = 5 and K = 3 (the mentor's example) give similar quality, so the choice is a convenience for interpretation, not a sharp optimum.
* **Stability** (adjusted Rand index between runs with different random starts, 1 = identical): K=3: 0.99, K=5: 0.95, K=7: 0.81.

### Final KMeans (K = 7)

Silhouette: training 0.181, validation 0.180. Davies-Bouldin: training 1.65, validation 1.66. Validation routes are assigned to the nearest training centroid, so a similar validation score means the clusters generalise to routes they were not built on.

![pca](figures/module5/m5_02_kmeans_pca_clusters.png)

*Each dot is a route; the 25 features are projected to 2 dimensions only for drawing, so clusters that overlap in the picture can still differ in other features.*

### What each cluster looks like (medians in original units)

| cluster | n_trips | n_unique_stops | length_km | service_span_h | trips_per_active_hour | median_headway_min | avg_speed_kmh | max_stop_overlap | mean_routes_per_stop | share_morning | share_afternoon | share_evening | routes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 6.00 | 9.00 | 4.06 | 9.43 | 1.33 | 39.00 | 16.58 | 0.50 | 44.62 | 0.41 | 0.20 | 0.00 | 1208 |
| 1 | 34.00 | 45.00 | 21.92 | 15.33 | 2.20 | 24.00 | 15.03 | 0.64 | 50.10 | 0.41 | 0.30 | 0.24 | 2968 |
| 2 | 5.00 | 48.00 | 24.98 | 11.58 | 1.00 | 122.50 | 19.28 | 0.76 | 70.57 | 0.50 | 0.25 | 0.25 | 2923 |
| 3 | 2.00 | 28.00 | 17.15 | 0.75 | 1.00 | 35.00 | 17.81 | 0.67 | 57.45 | 0.00 | 0.00 | 1.00 | 646 |
| 4 | 2.00 | 25.00 | 15.77 | 1.33 | 1.00 | 55.00 | 19.15 | 0.68 | 60.95 | 0.00 | 0.83 | 0.00 | 1129 |
| 5 | 1.00 | 31.00 | 19.18 | 0.00 | 1.00 | 40.00 | 19.09 | 0.68 | 69.31 | 1.00 | 0.00 | 0.00 | 1263 |
| 6 | 2.00 | 2.00 | 11.03 | 8.33 | 1.00 | 499.50 | 16.25 | 0.33 | 8.00 | 0.50 | 0.50 | 0.00 | 329 |


Most distinctive features of each cluster (mean standardised value; + = above the overall average):

| cluster | routes | share_of_train | most_distinctive_features_z |
|---|---|---|---|
| 0 | 1208 | 11.5% | avg_trip_duration_min (-1.85), length_km (-1.83), n_unique_stops (-1.44) |
| 1 | 2968 | 28.4% | n_active_hours (+1.31), n_trips (+1.27), trips_per_active_hour (+1.02) |
| 2 | 2923 | 27.9% | peak_period__morning (+0.84), median_headway_min (+0.82), trips_per_active_hour (-0.58) |
| 3 | 646 | 6.2% | share_evening (+2.42), share_morning (-1.42), service_span_h (-1.18) |
| 4 | 1129 | 10.8% | share_afternoon (+1.5), share_morning (-1.22), service_span_h (-0.99) |
| 5 | 1263 | 12.1% | share_morning (+1.79), service_span_h (-1.28), share_afternoon (-1.13) |
| 6 | 329 | 3.1% | n_unique_stops (-2.48), mean_routes_per_stop (-2.4), median_headway_min (+1.6) |


![profile](figures/module5/m5_04_kmeans_profile_heatmap.png)

![sizes](figures/module5/m5_03_kmeans_sizes_and_cities.png)

*Cluster composition by city shows whether a cluster is a real service pattern or mostly one feed: cluster 0: chennai 52%; cluster 1: delhi 44%; cluster 2: bengaluru 46%; cluster 3: chennai 40%; cluster 4: chennai 44%; cluster 5: bengaluru 45%; cluster 6: bengaluru 88%.*

## DBSCAN

### Parameter experiments (eps x min_samples)

| eps | min_samples | clusters | noise_pct | largest_cluster_share | silhouette_non_noise |
|---|---|---|---|---|---|
| 0.80 | 5 | 92 | 80.70 | 0.03 | 0.17 |
| 1.00 | 5 | 90 | 63.20 | 0.10 | 0.04 |
| 1.30 | 5 | 73 | 38.00 | 0.20 | -0.09 |
| 1.60 | 5 | 46 | 20.20 | 0.68 | -0.30 |
| 2.00 | 5 | 11 | 7.10 | 0.91 | -0.01 |
| 2.50 | 5 | 7 | 1.90 | 0.97 | 0.17 |
| 3.00 | 5 | 1 | 0.70 | 0.99 |  |
| 0.80 | 10 | 23 | 91.20 | 0.02 | 0.37 |
| 1.00 | 10 | 35 | 76.00 | 0.07 | 0.22 |
| 1.30 | 10 | 33 | 49.60 | 0.17 | 0.09 |
| 1.60 | 10 | 15 | 28.40 | 0.62 | -0.18 |
| 2.00 | 10 | 5 | 10.20 | 0.88 | -0.02 |
| 2.50 | 10 | 5 | 2.90 | 0.97 | 0.20 |
| 3.00 | 10 | 4 | 1.00 | 0.98 | 0.31 |
| 0.80 | 20 | 3 | 96.50 | 0.01 | 0.79 |
| 1.00 | 20 | 11 | 86.80 | 0.04 | 0.42 |
| 1.30 | 20 | 20 | 62.90 | 0.14 | 0.13 |
| 1.60 | 20 | 11 | 39.00 | 0.28 | 0.09 |
| 2.00 | 20 | 5 | 15.40 | 0.82 | -0.01 |
| 2.50 | 20 | 2 | 4.30 | 0.95 | 0.25 |
| 3.00 | 20 | 1 | 1.70 | 0.98 |  |


![grid](figures/module5/m5_06_dbscan_parameter_grid.png)

![kdist](figures/module5/m5_05_dbscan_kdistance.png)

*Small eps labels most routes as noise (many tiny clusters); large eps merges nearly everything into one cluster. The k-distance plot shows the distance scale of the data: the 'knee' marks where routes stop having close neighbours.*

**Decision:** eps = **3.0**, min_samples = **10** (best silhouette of the non-noise routes among settings with at least 2 clusters and 1-15% noise).

### Final DBSCAN

* Clusters found: **4**; the largest holds 99% of the training routes.
* Noise: **1.0%** of training routes and **1.0%** of validation routes (validation routes are noise when no training core point is within eps).
* Silhouette of the non-noise routes: 0.307; Davies-Bouldin: 1.00.
* **Reading:** with these features DBSCAN finds one large dense region plus a few small groups, so it is not a good *segmentation* tool here; its value is **finding unusual routes**.

### Noise-point analysis (noise is not an error)

| city | noise_routes | share |
|---|---|---|
| ahmedabad | 11 | 0.01 |
| bengaluru | 98 | 0.02 |
| chennai | 15 | 0.00 |
| delhi | 4 | 0.00 |
| kochi | 0 | 0.00 |
| pune | 3 | 0.01 |


Median features of noise routes versus all other routes:

| feature | noise routes (median) | other routes (median) |
|---|---|---|
| n_trips | 4.00 | 6.00 |
| n_unique_stops | 5.00 | 36.00 |
| length_km | 5.00 | 19.26 |
| service_span_h | 8.08 | 10.42 |
| trips_per_active_hour | 1.50 | 1.00 |
| median_headway_min | 20.00 | 52.50 |
| avg_speed_kmh | 13.49 | 17.90 |
| max_stop_overlap | 0.46 | 0.67 |
| mean_routes_per_stop | 17.00 | 56.83 |
| share_morning | 0.35 | 0.43 |
| share_afternoon | 0.26 | 0.29 |
| share_evening | 0.00 | 0.20 |


Features that push routes out of the dense region (mean standardised value of noise routes): avg_trip_duration_min (-1.7), n_unique_stops (-1.6), mean_routes_per_stop (-1.2), median_stops_per_trip (-1.0), length_km (-0.8).

![noise](figures/module5/m5_07_dbscan_noise_pca.png)

All 131 noise routes (training and validation) are listed in `tables/module5_dbscan_noise_routes.csv`. Before calling any of them wrong, check whether it is (a) a data problem (e.g. invalid speed - 51 noise routes have no valid scheduled speed), (b) a special service (very long or very many stops) or (c) just a rare combination of normal values.
