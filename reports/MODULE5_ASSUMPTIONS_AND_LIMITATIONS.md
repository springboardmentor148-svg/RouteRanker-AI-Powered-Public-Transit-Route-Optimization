# Module 5: Machine Learning Model Development and Evaluation

## 1. Objective

The objective of Module 5 is to apply machine learning algorithms to the preprocessed public transportation route dataset and identify patterns among routes across five Indian cities.

## 2. Dataset

Input dataset: `data/processed/module4/route_features_scaled.csv`

- Total records: 9,338
- Total features: 8
- Numerical features used for clustering:
  - trip_count
  - distinct_stop_count
  - average_stops_per_trip
- City features: Bangalore, Delhi, Hyderabad, Mumbai and Pune.

## 3. Algorithms Used

### K-Means Clustering

K-Means was applied with three clusters based on the initial Elbow Method selection.

Results:
- Cluster 0: 4,420 records
- Cluster 1: 4,657 records
- Cluster 2: 261 records
- Silhouette Score: 0.4216
- Davies-Bouldin Index: 0.8486

### DBSCAN Clustering

DBSCAN was applied to identify dense route groups and unusual records.

Results:
- Number of clusters: 2
- Noise points: 126
- Noise percentage: 1.35%
- Silhouette Score: 0.7341
- Davies-Bouldin Index: 0.3053

## 4. Assumptions

1. The Module 4 preprocessed and scaled dataset is suitable for clustering.
2. The three selected numerical features represent useful route characteristics.
3. Standardized feature values allow comparison on a common scale.
4. DBSCAN noise points represent records outside sufficiently dense groups and are not automatically data errors.
5. Cluster labels are algorithm-generated group identifiers, not actual service-quality or passenger-demand labels.

## 5. Limitations

1. The dataset does not contain verified passenger-demand labels.
2. Supervised classification using Random Forest and XGBoost was not performed because a genuine target variable was unavailable.
3. K-Means requires the number of clusters to be selected in advance.
4. DBSCAN results depend on the eps and min_samples parameters.
5. Noise-point detection does not prove that a route is incorrect or inefficient.
6. The analysis uses route-level features and does not directly measure passenger satisfaction, real-time traffic or actual passenger demand.
7. Clustering evaluation scores depend on the selected features and parameter settings.

## 6. Conclusion

K-Means and DBSCAN were successfully applied to the five-city route dataset containing 9,338 records. K-Means identified three route groups, while DBSCAN identified two dense groups and 126 noise points.

In this experiment, DBSCAN achieved a higher Silhouette Score and a lower Davies-Bouldin Index than K-Means. These results suggest stronger separation among its non-noise clusters, although the evaluation populations differ.

The results provide an initial understanding of public transportation route patterns and can support further route analysis and optimization research.
