# Module 4 — Vapi preprocessing

## Results
- Source routes: 22
- Exact duplicate rows removed: 0
- Rows excluded because all selected measurements were missing: 0
- Usable routes: 22
- Training routes: 17
- Validation routes: 5
- Selected numerical features: scheduled_trip_count, distinct_stop_count, departure_span_hours
- Random seed: 42

## Missing values
Invalid numerical values were changed to missing in a working copy.
Remaining gaps in selected features use training-set medians.
Actual counts and medians are in missing_value_summary.csv.
Missing indicators are created only for columns missing during training.
Source recovery was not performed; imputation is a provisional baseline.
Valid zeros were preserved.

## Categories
Route IDs are identifiers and excluded from model inputs.
Constant categories were excluded because they provide no variation.
See categorical_decisions.csv.
Varying categories, if present, were omitted from this numerical baseline.

## Scaling
StandardScaler was fitted only on training rows after imputation.
Validation rows use the same fitted pipeline.
This supports a distance-based clustering baseline such as K-Means.
No model or unsupported target labels were created.

## Evaluation
The 80:20 split is exploratory, with only 5 validation routes.
Related route directions may cross the split.
It does not evaluate future dates or other cities.
DBSCAN would require a different evaluation strategy.

## Limitations
Only one Vapi service date is represented.
Distance and duration were excluded pending source geometry review.
Recorded morning-service absence and sparse stop patterns remain unverified.
Scheduled trips do not establish passenger demand or underutilisation.
Outliers were not automatically deleted.
Identifiers and the split column in processed_routes.csv must not enter a model.
Use X_train.csv and X_validation.csv as model inputs.