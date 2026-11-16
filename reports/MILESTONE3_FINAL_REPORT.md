# ROUTERANKER - MILESTONE 3 FINAL REPORT

## Model Selection, Training and Inference

## 1. Dataset

- Total routes analyzed: 10,514
- Cities analyzed: 8
- Numeric features: 16
- Dataset: combined_route_features.csv

## 2. Clustering Results

- K-Means: 3 clusters
- K-Means silhouette score: 0.6725
- DBSCAN: 9 identified clusters
- DBSCAN noise routes: 167
- DBSCAN silhouette score: 0.7196

## 3. Classification Results

         Model  Accuracy  Precision    Recall  F1_Score
       XGBoost  0.972896   0.973093  0.972896  0.972954
 Random Forest  0.970994   0.970983  0.970994  0.970988

Best classification model: XGBoost

Best model F1 score: 0.973

## 4. Feature Importance

                                 Feature  Importance
                    scheduled_trip_count    0.300507
               headway_observation_count    0.238315
           average_trip_duration_minutes    0.103988
                  average_stops_per_trip    0.084373
                 average_headway_minutes    0.059120
               maximum_shape_distance_km    0.042358
                trips_flagged_for_review    0.033982
                    unflagged_trip_count    0.028726
                  median_headway_minutes    0.027879
 average_unflagged_trip_duration_minutes    0.025217

## 5. Route Inference and Recommendations

- Generated predicted operational categories for all routes.
- Generated rule-based optimization recommendations.
- Produced city-level category analysis.


## 6. Important Methodological Limitation

The operational categories are proxy labels constructed from route features. They are not observed passenger demand, occupancy, actual congestion, or measured service efficiency labels. Classification scores therefore measure agreement with these engineered categories and should not be interpreted as real-world prediction accuracy.


Clustering scores indicate separation under the chosen feature representation and parameters. They do not independently prove transport optimization effectiveness.


## 7. Generated Visualizations

- visuals/milestone3_model_comparison.png
- visuals/milestone3_kmeans_clusters.png
- visuals/milestone3_dbscan_clusters.png
- visuals/milestone3_feature_importance.png
- visuals/milestone3_city_categories.png


## 8. Conclusion

Milestone 3 implemented clustering, classification, model evaluation, route inference, and initial optimization recommendation generation. The current implementation is a prototype based on operational proxy labels. Future validation should incorporate actual ridership, service performance, passenger capacity, and route-level operational outcomes.
