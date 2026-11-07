
# RouteRanker – Module 5: Machine Learning

## 1. Objective
Apply machine learning techniques to identify similar public transit
route patterns and detect unusual route records.

## 2. Dataset
- Total route records: 7,312
- Selected clustering features: 15
- Missing values: 0
- Infinite values: 0
- Cities: Ahmedabad, Chennai, Hyderabad, Mumbai, Pune

## 3. K-Means Clustering
K values tested: 2, 3, 4, 5.

Selected candidate: K = 4

- Silhouette Score: 0.865398
- Davies-Bouldin Index: 0.228795
- Inertia: 212.018324

Cluster distribution:
- Cluster 0: 6,525 routes
- Cluster 1: 180 routes
- Cluster 2: 227 routes
- Cluster 3: 380 routes

PCA explained variance:
- Component 1: 64.32%
- Component 2: 24.54%
- Combined: 88.86%

## 4. DBSCAN Clustering
Selected parameters:
- eps: 0.3
- min_samples: 10

Results:
- Number of clusters: 4
- Core points: 7,305
- Border points: 1
- Noise points: 6
- Silhouette Score: 0.864634
- Davies-Bouldin Index: 0.228631

Noise routes were identified in Chennai and Hyderabad.

## 5. Model Comparison
Both algorithms identified four clusters.

K-Means achieved a slightly higher Silhouette Score
(0.865398) than DBSCAN (0.864634).

DBSCAN achieved a slightly lower Davies-Bouldin Index
(0.228631) than K-Means (0.228795).

K-Means assigned all routes to clusters, while DBSCAN
identified six noise points. The evaluation scores are
very close, so both algorithms provide useful clustering results.

## 6. Supervised Classification

Supervised classification was performed using the genuine GTFS
route_type field as the target variable.

The classification task was to distinguish between:
- Metro: route_type 1
- Bus: route_type 3

The corrected dataset used 13 numerical features from Module 4.
Route identifiers, city columns and encoded route-type columns
were excluded from the model inputs.

Dataset details:
- Total Chennai routes: 4,721
- Training records: 3,776
- Testing records: 945
- Missing values: 0
- Train/test split: 80:20
- Random state: 42

### 6.1 Random Forest Classification

Model configuration:
- Estimators: 300
- Class weighting: Balanced
- Random state: 42

Evaluation results:
- Accuracy: 99.5767%
- Macro Precision: 98.9988%
- Macro Recall: 99.4929%
- Macro F1-score: 99.2438%

Confusion Matrix:

| | Predicted Metro | Predicted Bus |
|---|---:|---:|
| Actual Metro | 157 | 1 |
| Actual Bus | 3 | 784 |

### 6.2 XGBoost Classification

Model configuration:
- Estimators: 300
- Maximum depth: 5
- Learning rate: 0.05
- Evaluation metric: Log Loss
- Random state: 42

Evaluation results:
- Accuracy: 99.5767%
- Macro Precision: 98.7654%
- Macro Recall: 99.7459%
- Macro F1-score: 99.2476%

Confusion Matrix:

| | Predicted Metro | Predicted Bus |
|---|---:|---:|
| Actual Metro | 158 | 0 |
| Actual Bus | 4 | 783 |

### 6.3 Classification Model Comparison

| Metric | Random Forest | XGBoost |
|---|---:|---:|
| Accuracy | 99.5767% | 99.5767% |
| Macro Precision | 98.9988% | 98.7654% |
| Macro Recall | 99.4929% | 99.7459% |
| Macro F1-score | 99.2438% | 99.2476% |

Both models achieved the same accuracy.
Random Forest achieved slightly higher precision,
while XGBoost achieved slightly higher recall and F1-score.

Neither model was clearly superior across every metric.

**Classification limitation:** The experiment used Chennai routes only.
The models predict transport mode, not passenger demand,
overcrowding or route efficiency. Their results should not be
assumed to generalize to the other four cities.

## 7. Limitations
- GTFS data represents scheduled public transport services.
- Actual passenger counts were unavailable.
- Clusters do not directly prove overcrowding or inefficiency.
- Noise points are not necessarily incorrect routes.
- Further operational data is required for reliable
  route optimization recommendations.

## 8. Conclusion
K-Means and DBSCAN successfully identified four groups
of similar route patterns.

DBSCAN also detected six unusual route records.

The results provide a foundation for the next module,
which will focus on generating meaningful route
optimization suggestions.


## 9. Route Optimization Suggestions

Based on the K-Means cluster analysis, the following schedule-based
improvement opportunities were identified.

### Cluster-wise observations and suggestions

1. Cluster 0:
   - Contains 6,525 routes.
   - Average scheduled trips: 33.02.
   - Average route distance: 19.07 km.
   - Suggestion: Review departure timings and coordinate schedules
     where routes have overlapping service periods.

2. Cluster 1:
   - Contains 180 routes.
   - Average scheduled trips: 1.00.
   - Average route distance: 45.65 km.
   - Average operating days: 1.
   - Suggestion: Review operating-day patterns and verify whether
     the limited scheduled service matches the intended timetable.

3. Cluster 2:
   - Contains 227 routes.
   - Average scheduled trips: 3.63.
   - Average route distance: 43.63 km.
   - Average operating days: 6.
   - Suggestion: Review departure frequency and timetable coverage
     across the operating days.

4. Cluster 3:
   - Contains 380 routes.
   - Average scheduled trips: 1.00.
   - Average route distance: 39.58 km.
   - Average operating days: 7.
   - Suggestion: Examine the scheduled departure frequency and
     check whether additional timetable coordination is appropriate.

### DBSCAN noise-point investigation

DBSCAN identified six noise points. These routes should be
individually checked for unusual schedule patterns, route
characteristics and possible GTFS data inconsistencies.

A noise point does not automatically indicate an incorrect or
inefficient route.

### Limitations and recommendations

- The analysis is based on scheduled GTFS data.
- Actual passenger counts and passenger demand were not available.
- The results cannot establish overcrowding or underutilization.
- Any timetable or frequency changes should be reviewed using
  passenger demand, fleet availability, transfer connections
  and operational constraints before implementation.

These suggestions are preliminary opportunities for further
transport schedule analysis, not automatic route-change decisions.
