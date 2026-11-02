
# Module 4: Data Preprocessing
## RouteRanker – AI-Powered Public Transit Route Optimization

### 1. Objective
Prepare the Module 2 route-level feature data for future machine learning
and clustering analysis.

### 2. Dataset
- Source: Module 2 Feature Engineering outputs.
- Cities: Bangalore, Hyderabad, Delhi, Mumbai and Pune.
- Original route records: 9,679.
- Routes with complete numerical statistics: 9,338.
- Routes excluded from this modelling dataset due to unavailable statistics: 341.

### 3. Missing Value Handling
- Missing trip_count, distinct_stop_count and average_stops_per_trip
  were not imputed.
- The 341 routes without these statistics were excluded from this
  numerical modelling dataset.
- Original route data was preserved.
- Optional descriptive fields were not required in the selected feature set.

### 4. Categorical Encoding
- City was one-hot encoded into five columns:
  city_Bangalore, city_Delhi, city_Hyderabad, city_Mumbai and city_Pune.
- Each row was verified to have exactly one city indicator.
- route_id and stop_id are identifiers, not numerical measurements.
- Constant route_type and service_count features were excluded.

### 5. Feature Scaling
- StandardScaler was applied to trip_count, distinct_stop_count
  and average_stops_per_trip.
- City indicator columns were kept as binary values.
- Scaling is intended for future distance-based methods such as K-Means.
- For future supervised learning, the data must be split first and
  the scaler fitted only on the training data.

### 6. Duplicate Investigation
- Exact duplicate feature rows: 3,038.
- Rows involved in repeated feature combinations: 4,227.
- These combinations belong to distinct city-route identifiers.
- All records were retained because different routes can have
  identical feature values.

### 7. Outlier Handling
- Potential outliers were investigated against the original GTFS data.
- Verified high route statistics were retained.
- Suspicious headway and trip-duration values were flagged for review.
- No potentially valid records were automatically deleted.

### 8. Assumptions and Limitations
- GTFS describes scheduled transit service, not actual passenger demand.
- Passenger counts, occupancy and actual ridership were not available
  and were not fabricated.
- Some routes lack complete trip statistics.
- Some GTFS time values require further source validation.
- Identical feature values do not necessarily mean duplicate routes.
- The current dataset does not contain a verified target label.
- The processed dataset is suitable as an initial input for
  exploratory unsupervised analysis, subject to feature review.

### 9. Output
File: route_features_scaled.csv
Location: data/processed/module4/
Shape: 9,338 rows x 8 columns.

### 10. Conclusion
Module 4 preprocessing was completed for the selected route-level
features. Missing values, categorical encoding, scaling, outliers
and repeated feature combinations were investigated and documented.
The processed dataset is saved for subsequent analysis

### Feature Selection Explanation

The following features were selected for the initial route-level machine learning dataset:

**Numerical features:**
- `trip_count`: Represents the number of trips associated with a route.
- `distinct_stop_count`: Represents the number of distinct stops served by a route.
- `average_stops_per_trip`: Represents the average number of stops per trip.

**Categorical feature:**
- `city`: One-hot encoded into five columns: Bangalore, Delhi, Hyderabad, Mumbai and Pune.

**Excluded features:**
- `route_id`: Identifier, not a numerical measurement. It should be retained separately for route identification.
- `agency_id`: Identifier; not included in the initial feature set.
- `route_type`: Excluded because it has only one unique value in the selected dataset.
- `service_count`: Excluded because it is constant.
- Route names: Descriptive text not included in the initial numerical modelling dataset.

Routes with unavailable numerical statistics were excluded from this modelling dataset without changing the original data.

### Machine Learning Strategy

The current processed dataset is prepared for initial unsupervised learning and clustering analysis.

- No target variable is created because the available GTFS data does not provide verified passenger-demand or occupancy labels.
- The dataset may be used for exploratory clustering methods such as K-Means.
- StandardScaler was applied to the three numerical features.
- City indicator columns were retained as binary values.
- The clustering results will require interpretation and validation before making conclusions about transit performance.

A supervised 80:20 training/validation split is not applicable to this current unsupervised dataset.

For future supervised machine learning, a valid target must first be obtained. The data should then be split into training and validation sets, and preprocessing transformations should be fitted only on the training data to avoid data leakage.
