# RouteRanker Module 6: Inference and Route Optimization

## Scope and source data

This run reuses the saved Module 5 K-Means and DBSCAN models and the Module 4 preprocessing manifest. It does not retrain the clustering models or fit a new scaler. The held-out validation routes are used as unseen inference records; the prepared Module 4 source dataset remains unchanged.

- Unseen inference records: 2,532
- Feature count: 29
- Preprocessing used: raw_transformed_with_module4_manifest
- Selected K-Means K: 3
- DBSCAN eps / min_samples: 3.073366 / 20
- DBSCAN assignment: nearest saved core sample within eps. This is an approximation because DBSCAN has no native predict method.

## Inference results

K-Means assigns each inference route to its nearest saved centroid. Cluster counts on the held-out routes: `{"0": 216, "1": 1781, "2": 535}`.

DBSCAN assigns a route to the nearest saved core sample if the distance is within eps; otherwise it marks it as noise. Cluster counts including noise: `{"-1": 36, "0": 2496}`. Noise share: 1.42%. Noise is a density result, not proof of a bad route.

### Optional classification models

- Random Forest: NOT_AVAILABLE_NO_TRAINED_LABELLED_MODEL
- XGBoost: NOT_AVAILABLE_NO_TRAINED_LABELLED_MODEL

The supplied schedule dataset contains no ground-truth route-category or passenger-demand labels, so Random Forest and XGBoost were not trained. No classification labels or scores were invented.

## Routes for planner review

The output `results/potential_route_review.csv` combines independent evidence such as DBSCAN noise, a city-relative K-Means distance tail, high headway with low scheduled trip count, long length with long trip duration, and high route-overlap indicators. A single signal is not called inefficiency. The table is a screening list for human review and includes reasons per route.

The merge review list uses the source `overlap_partner`, `max_stop_overlap`, and `overlap_share_of_route` fields to identify pairs. These are pair-review candidates only. The available aggregate fields do not establish that a merge would preserve passenger coverage or capacity.

Split review candidates have both long route length and long trip duration relative to their city. Stop sequences, transfer connectivity, and passenger journeys are not included, so no split geometry is fabricated.

Trip-frequency review candidates have high median scheduled headway and low scheduled trip count relative to same-city quartiles. These remain schedule-only signals, not demand estimates.

## Simulated network comparison

The simulation adds one scheduled trip to each frequency-review route. It is a transparent sensitivity scenario, not an operational recommendation. It does not modify the source dataset. No merge or split is applied because connectivity and passenger coverage cannot be estimated from the available data.

| Metric | Current | Simulated | Change | Unit |
|---|---:|---:|---:|---|
| route_count | 12660.000 | 12660.000 | +0.000 | routes |
| total_scheduled_trips | 238410.000 | 240135.000 | +1725.000 | scheduled trip records |
| sum_route_length_km | 282298.456 | 282298.456 | +0.000 | route-km |
| mean_route_length_km | 22.298 | 22.298 | +0.000 | km/route |
| mean_scheduled_trips_per_route | 18.832 | 18.968 | +0.136 | trips/route |
| scheduled_trips_per_route_active_hour | 2.826 | 2.846 | +0.020 | trips/route-active-hour |
| mean_unique_stops_per_route | 40.747 | 40.747 | +0.000 | stops/route |
| frequency_adjusted_routes | 0.000 | 1725.000 | +1725.000 | routes |

The scenario changes scheduled-trip metrics only. Route count and sum of route lengths stay constant by design; passenger demand, occupancy, operating cost, fleet requirements, route coverage, and exact headway changes are not estimated.

## Outputs

- `results/inference_assignments.csv`: held-out unseen route predictions.
- `results/network_model_assignments.csv`: model assignments across the full route inventory for screening and comparison.
- `results/potential_route_review.csv`: routes with screening signals and evidence.
- `results/merge_review_candidates.csv` and `results/split_review_candidates.csv`: conditional planner review lists.
- `results/optimization_suggestions.csv`: evidence, proposal, and simulation status for each action.
- `data/simulation/simulated_network_frequency_scenario.csv`: separate simulated copy of the network.
- `results/current_vs_simulated_network_metrics.csv`: comparable current and scenario metrics.
- `visualizations/`: SVG cluster and network comparison charts.

## Limitations and next steps

The source records describe scheduled service, not passenger use. Route-overlap and route-length fields are aggregate; they cannot validate a merge or define split points. Before changing service, add reliable stop sequences, passenger counts by time period, transfer journeys, vehicle capacity, fleet constraints, operating costs, and service obligations. Compare all proposed outcomes with coverage and accessibility requirements.
