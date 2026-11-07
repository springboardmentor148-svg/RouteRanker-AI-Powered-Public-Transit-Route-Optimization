# Module 5 - Algorithm comparison, observations and possible planning use

_Generated 2026-11-07._

## Comparison

| algorithm | type | result | noise | silhouette (train / validation) | Davies-Bouldin (train / validation) | role in this project |
|---|---|---|---|---|---|---|
| KMeans | unsupervised | 7 clusters | 0% (every route assigned) | 0.18 / 0.18 | 1.65 / 1.66 | Gives a complete grouping of routes by scheduled-service pattern; needs K; clusters are weakly separated |
| DBSCAN | unsupervised | 4 clusters | 1.0% noise (train), 1.0% (validation) | 0.31 (non-noise) | 1.00 (non-noise) | Finds unusual routes; one dominant dense region, so weak as a segmentation |


*DBSCAN's silhouette is computed on the non-noise routes only and nearly all of them sit in one large cluster, so its higher value is **not** evidence that DBSCAN groups routes better than KMeans.*


| variant | model | accuracy | precision_macro | recall_macro | f1_macro |
|---|---|---|---|---|---|
| all features | Random Forest | 0.96 | 0.97 | 0.93 | 0.95 |
| all features | XGBoost | 0.97 | 0.97 | 0.95 | 0.96 |
| without length_method flags | Random Forest | 0.91 | 0.94 | 0.90 | 0.91 |
| without length_method flags | XGBoost | 0.93 | 0.94 | 0.93 | 0.93 |


*Clustering and classification cannot be compared with each other: clustering has no ground truth (internal measures only), classification was run on a different, real label (the city).* Random Forest and XGBoost: see the classification report; both separate the cities well, with XGBoost slightly better on macro F1 with all features.

## Main observations

1. The training routes do **not** form clearly separated groups (silhouette 0.15-0.18 for every K); scheduled service varies along a continuum, so any K is a convenient partition rather than a natural one.
2. The largest KMeans clusters hold 2,968 routes (cluster 1), 2,923 routes (cluster 2), 1,263 routes (cluster 5).
3. DBSCAN marks about 1% of routes as noise; these unusual routes are the most useful DBSCAN output.
4. The cities can be told apart from schedule features alone (classification diagnostic), so clusters partly reflect how each feed is written.
5. No cluster, noise flag or classifier output says anything about passengers, crowding or efficiency.

## Possible uses for route planning (candidates to investigate, not recommendations)

A cluster is not an optimisation recommendation. The groups below tell planners **where to look first**; ridership data and operator knowledge are needed before any change.

* **Review the noise routes first** (131 routes, `tables/module5_dbscan_noise_routes.csv`): check whether each is a data problem, a special service or a genuinely unusual route.
* **Very sparse service groups:** KMeans clusters 3, 4, 5, 6 have a median of at most 2 scheduled trips (3,367 routes). With ridership data, planners could check whether these are variants that could be consolidated with a main route or are intentional limited services.
* **High shared-stop groups:** clusters 2, 4, 5 have the highest stop overlap with other routes; corridors served by many similar routes are candidates for timetable coordination studies - again only after checking passenger flows.
* **Compare within, not across, feeds:** use clusters per city, because the feeds are not directly comparable.

## Limitations

* Scheduled data only; no ridership, occupancy, capacity or delay data.
* Several feeds are community-made or old; Hyderabad was excluded in Module 4 and Delhi/Kochi/Pune show near-constant scheduled speeds.
* Weak cluster separation: results depend on K, eps and min_samples and should be read as exploratory.
* DBSCAN has no native predict function; validation routes were assigned by their nearest core point within eps.
* The supervised task uses the city as target and does not measure route quality.

## Next module
Turn the model outputs into route-planning suggestions and integrate the pipeline, once the mentor confirms what real ridership or performance data (if any) can be used.