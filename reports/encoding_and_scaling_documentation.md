# RouteRanker Module 4: Feature Encoding and Scaling Documentation

**Project:** AI-Based Public Transit Route Optimization for Indian Cities (RouteRanker)  
**Target Algorithms:** Unsupervised Clustering (KMeans, DBSCAN) and Latent Transit Archetype Discovery  
**Training Partition:** 7,386 active routes (80.0%)  
**Validation Partition:** 1,847 active routes (20.0%)  
**Final Feature Matrix Dimensions:** 12 orthogonal dimensions (8 scaled numerical + 4 unscaled binary)

---

## 1. Categorical Feature Encoding

### A. Feature Selected for Encoding: `dominant_time_period`
To capture the operational diurnal orientation of each transit service without double-counting volume, each route was categorized based on the time window with the highest scheduled trip departure share:
* `morning` (05:00 to 11:59): 5,309 train routes (71.9%) / 1,328 val routes (71.9%)
* `afternoon` (12:00 to 16:59): 1,253 train routes (17.0%) / 313 val routes (16.9%)
* `evening` (17:00 to 20:59): 586 train routes (7.9%) / 147 val routes (8.0%)
* `night` (21:00 to 04:59): 238 train routes (3.2%) / 59 val routes (3.2%)

### B. Methodology: One-Hot Encoding vs. Label Encoding
* **Why Label Encoding Fails for KMeans & DBSCAN:**
  Assigning arbitrary integers (e.g. `afternoon = 0`, `evening = 1`, `morning = 2`, `night = 3`) imposes a spurious linear metric space. In Euclidean distance:
  $$d(\text{afternoon}, \text{night}) = |0 - 3| = 3 \quad \text{vs} \quad d(\text{afternoon}, \text{evening}) = |0 - 1| = 1$$
  This would falsely inform the clustering algorithm that late-night service is three times farther from afternoon service than evening service. Transit time windows have no ordinal hierarchy.
* **Why One-Hot Encoding is Required:**
  One-Hot Encoding projects each time window into an orthogonal unit vector in 4-dimensional space:
  - $\text{afternoon} = [1, 0, 0, 0]$
  - $\text{evening} = [0, 1, 0, 0]$
  - $\text{morning} = [0, 0, 1, 0]$
  - $\text{night} = [0, 0, 0, 1]$
  The pairwise Euclidean distance between any two distinct time windows is identical:
  $$d = \sqrt{(1 - 0)^2 + (0 - 1)^2} = \sqrt{2} \approx 1.414$$
  Every operational category is weighted with unbiased geometric neutrality.

### C. Fit-on-Train Procedure (Rule 5):
The `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` was fitted strictly on `train_df[['dominant_time_period']]`. The fitted encoder was then used to transform both `train_df` and `val_df`.

### D. Features Kept in Metadata Lookup (Rule 3):
* **`city`:** Excluded from the model matrix to prevent artificial geographic segregation (approved in Phase 2).
* **`length_method`:** Excluded from the model matrix as a data engineering provenance attribute (`shape` vs `stop_straight_line_estimate`).
* **`operating_days`:** Invariant across active routes (9,232 out of 9,233 routes run 7 days).

---

## 2. Mathematical Transformations: Log-Transform (`np.log1p`)

Prior to distance scaling, heavily skewed features were transformed using $f(x) = \ln(1 + x)$:

| Feature | Raw Skewness | `np.log1p` Skewness | Absolute Skew Reduction | Action Taken | Operational Justification |
|---|---:|---:|---:|:---:|---|
| **`trip_count`** | **+3.711** | **+0.544** | **3.167** | **Transformed with `np.log1p`** | Compresses long exponential tail into a near-Gaussian distribution, preventing high-frequency trunk lines from dominating Euclidean distance. |
| **`route_length_km`** | **+88.828** | **-0.352** | **88.476** | **Transformed with `np.log1p`** | Stabilizes extreme spatial reach variations after 99th percentile capping ($82.60$ km). |
| `stop_count` | +0.895 | -1.019 | -0.124 | Kept on linear scale | Naturally balanced; log1p introduces left skew. |
| `service_span_hours` | -0.015 | -0.946 | -0.931 | Kept on linear scale | Already perfectly symmetric; log1p would corrupt symmetry. |
| `first_departure_hour` | +1.297 | -1.584 | -0.287 | Kept on linear scale | Bounded uniform clock hour distribution ($0$ to $23$). |
| `morning_trip_share` | +0.313 | -0.152 | 0.161 | Kept on linear scale | Naturally bounded in $[0, 1]$; already symmetric. |
| `evening_trip_share` | +1.663 | +1.107 | 0.555 | Kept on linear scale | Naturally bounded in $[0, 1]$. |
| `night_trip_share` | +3.826 | +3.195 | 0.631 | Kept on linear scale | Naturally bounded in $[0, 1]$. |

---

## 3. Feature Scaling Methodology

### A. Evaluated Scalers & Rationale:
* **`MinMaxScaler` (Rejected):** Maps features into $[0, 1]$ based on minimum and maximum. Because our dataset contains valid-but-unusual extreme services (e.g. 50-meter depot turnarounds and 80-km peri-urban loops), Min-Max scaling compresses 95% of standard routes into a tiny interval $[0.0, 0.05]$, destroying model resolution.
* **`StandardScaler` (Evaluated):** Centers around the mean ($\mu$) and divides by standard deviation ($\sigma$). While effective on log-transformed features, remaining outliers still shift the mean and inflate variance.
* **`RobustScaler` (Selected & Applied):**
  $$x_{\text{scaled}} = \frac{x - \text{median}}{\text{IQR}} = \frac{x - Q_2}{Q_3 - Q_1}$$
  Centers by the **median** ($50\%$) and scales by the **Interquartile Range** ($Q_3 - Q_1$). The scale of the central 50% of routes is normalized without being influenced by valid-but-unusual services (depot runs, station shuttles, long loops).

### B. Fit-on-Train Procedure & Leakage Prevention (Rule 5):
1. `RobustScaler` was fitted **strictly on the 7,386 routes of `train_df`**.
2. Median and IQR statistics learned from `train_df` were stored in the scaler object.
3. Both `train_df` and `val_df` were transformed using these training parameters.
4. **Validation Check:**
   - Training scaled medians: **`0.000` across all numerical features**.
   - Validation scaled medians: centered within $\pm 0.02$ of `0.000`.
   - Confirms that validation data was evaluated against training baseline statistics with **zero data leakage**.

### C. Unscaled Binary Columns:
The 4 one-hot encoded binary features (`period_afternoon`, `period_evening`, `period_morning`, `period_night`) were **not scaled**. They remain strictly in $[0.0, 1.0]$ binary space to preserve orthogonal unit geometric distance.

---

## 4. Persisted Pipeline Artifact Locations

All fitted transformers, parameter files, and feature lists are persisted in `processed/pipeline/` for future Streamlit deployment:

| Artifact File | Path | Format | Contents / Stored Parameters |
|---|---|:---:|---|
| **Feature Scaler** | `processed/pipeline/feature_scaler.joblib` | Joblib Binary | Fitted `RobustScaler` storing training medians and IQRs for the 8 numerical features |
| **One-Hot Encoder** | `processed/pipeline/one_hot_encoder.joblib` | Joblib Binary | Fitted `OneHotEncoder` storing categories for `dominant_time_period` |
| **Trajectory Length Cap** | `processed/pipeline/length_cap.json` | JSON | `{"fitted_training_quantile": 0.99, "fitted_length_cap_km": 82.6022, "random_seed": 42}` |
| **Model Feature List** | `processed/pipeline/feature_list.json` | JSON | Ordered list of the 12 features passed into KMeans and DBSCAN |
| **Global Feature List** | `processed/feature_list.json` | JSON | Sibling copy of feature list for global project access |
