# RouteRanker - Module 5 model development and evaluation

## Data and scope

The prepared Module 4 table contains 12,660 scheduled-route records from Bengaluru, Chennai, Delhi, Hyderabad, and Pune, with 29 model features. K-Means and DBSCAN were fit on the 10,128-row training partition; the 2,532-row validation partition was assigned after fitting. The feature matrix excludes city, route IDs, route names, and other identifiers.

The source is a schedule dataset. Scheduled trips and headways describe planned service; they are not passenger counts, occupancy, or observed demand. This work does not create a demand label or claim that a cluster is an optimization decision.

## K-Means

K-Means was fit for K=2, 3, 4, and 5 with k-means++ initialization and five restarts per K. The elbow chart and internal metrics are saved under visualizations/ and results/.

| K | Within-cluster sum of squares | Silhouette (sampled) | Davies-Bouldin |
|---:|---:|---:|---:|
| 2 | 172757.76 | 0.5318 | 0.8064 |
| 3 | 150635.52 | 0.2127 | 1.5683 |
| 4 | 133497.56 | 0.1786 | 1.6612 |
| 5 | 121279.92 | 0.1877 | 1.6447 |

The elbow heuristic selects K=3. K=2 has the strongest sampled silhouette (0.5318) and lowest Davies-Bouldin value (0.8064), while the elbow heuristic selects K=3; this is a tradeoff between tighter two-group separation and the three-group elbow split. For K=3, the largest training cluster has 7,094 routes and the smallest has 837. The selected K-Means model assigns every route to a cluster. These internal metrics do not prove that groups match passenger needs.

## DBSCAN

DBSCAN parameters were tuned on a deterministic sample by varying epsilon from k-distance quantiles and min_samples in 5, 10, 20. The final fit uses eps=3.07337 and min_samples=20.

- Training clusters (excluding noise): 1
- Training cluster sizes: 9,966 in the largest and 9,966 in the smallest
- Training noise points: 162 (1.6%)
- Silhouette on non-noise points: not defined (fewer than two non-noise clusters)
- Davies-Bouldin on non-noise points: not defined (fewer than two non-noise clusters)

The largest group contains 98.4% of training routes, so this setting gives one dominant density group and one much smaller group rather than balanced segmentation. Treat the smaller group and noise as review leads, not route categories. Noise is a density result, not proof of a bad or incorrect route. The validation labels use nearest-core-point assignment within epsilon because DBSCAN has no native predict method; this is an explicit approximation.

## Supervised models

Random Forest and XGBoost classifier implementations are included in src/route_ranker/module5_supervised.py. They were not trained because no ground-truth route category or demand label is present in the supplied dataset. results/classification_metrics.csv records this as not evaluated. Add valid labels to data/labels/route_labels.csv to run classification; the template and instructions are included. Accuracy, macro precision, macro recall, macro F1, and a confusion matrix are then produced on a held-out test split.

## Algorithm comparison and observations

K-Means requires a chosen K and assigns every route, which makes its cluster profiles straightforward to compare. DBSCAN discovers dense groups without fixing their number and flags low-density routes, but its result depends on feature scaling and epsilon; distance concentration in 29 dimensions can make density groups unstable. Its dominant cluster in this run shows that DBSCAN adds little balanced segmentation under the selected setting. See results/algorithm_comparison.csv and results/dbscan_tuning.csv for the evaluated settings.

Cluster profiles are in results/cluster_profiles.csv and show schedule features only.

## Route-planning suggestions and limits

The ranked file results/route_review_candidates.csv uses a transparent schedule-only signal: within-city relative headway (65%) plus the inverse relative scheduled-trip count (35%). It is a shortlist for human review, not a demand score and not a recommendation to remove or add service. Compare the shortlisted routes with passenger counts by time of day, occupancy, transfer patterns, fleet availability, operating costs, road conditions, and community access before changing a route or timetable.

## Reproduction

From the project folder, install requirements.txt and run `python run_module5.py`. The script recreates the cluster models, CSV results, SVG visualizations, and this report. Optional supervised training is run with `python run_module5.py --labels data/labels/route_labels.csv` after supplying valid labels and installing requirements-supervised.txt.
