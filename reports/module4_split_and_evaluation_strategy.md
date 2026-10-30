# Module 4 - Training / validation split and evaluation strategy

_Generated 2026-10-30._

## There is no supervised target

Classification would need a valid label such as 'overcrowded' or 'underutilised'. GTFS has no passenger data, so such a label can only be an assumption and the mentor's rules forbid unsupported performance labels. **No target was created.** For KMeans and DBSCAN no target is needed. If real ridership data becomes available, a supervised task can be added later.

## The split

* **80:20 split, 10,466 training and 2,600 validation routes** (`random_state=42`, reproducible).
* **Grouped by city and route name:** many routes are the up/down/variant patterns of one bus line and look almost identical. A purely random split would put near-copies on both sides and make validation look better than it is, so all routes with the same name in a city stay on the same side.
* **Fit on training only:** medians, skewness decisions, means/standard deviations, category lists and the constant/correlation filters are learned from the training routes and applied unchanged to the validation routes (no leakage).

City balance of the split (share of routes):

| city | train | validation |
|---|---|---|
| bengaluru | 0.338 | 0.339 |
| chennai | 0.307 | 0.279 |
| delhi | 0.225 | 0.235 |
| ahmedabad | 0.071 | 0.086 |
| kochi | 0.036 | 0.033 |
| pune | 0.023 | 0.027 |


## Evaluation strategy for the next module (clustering)

No accuracy can be computed without ground truth. Clusters will be judged by:

1. **Internal measures** on the training data (silhouette score; for DBSCAN the share of noise routes) to choose k / eps.
2. **Generalisation:** validation routes are assigned to the training clusters and the silhouette is compared with the training value; a large drop means the clusters are not stable.
3. **Stability:** repeat with different random seeds and compare cluster assignments.
4. **Interpretation:** cluster profiles (median trips, stops, length, periods) per city; clusters are *groups of similar scheduled service*, not 'good' or 'bad' routes.

## Suitability check (a sanity check only, not a Module 5 result)

A quick KMeans with k=4 on a 4,000-route training sample gives a silhouette of 0.17; assigning a 2,000-route validation sample to those centres gives 0.15. The tables contain no missing or infinite values, so they can be used by KMeans and DBSCAN. The numbers say nothing about route quality.
