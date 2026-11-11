
# RouteRanker — Module 4: Data Preprocessing

## Objective
Prepare the feature-engineered route dataset for the planned clustering stage.

## Dataset and filtering
- Original dataset: 8322 rows.
- Routes with scheduled trips: 7316.
- Routes with distance available: 7312.
- Routes with no scheduled trips excluded from the distance-ready dataset: 1006.
- Routes without distance excluded from the distance-ready dataset: 4.

The original dataset was preserved. The distance-ready dataset was used for this preprocessing workflow.

## Missing values
- The original dataset contained missing values in route names, distance-related fields, operating-day fields, and service-hour fields.
- Routes with no scheduled trips were excluded from the distance-ready dataset because they had no scheduled service to analyze.
- Four routes had scheduled trips but no distance values; they were excluded from the distance-ready dataset used here.
- Missing route names were labeled "Unknown".
- The selected model features had 0 missing values before the missing-value handling step, so no numerical imputation was required.

## Feature selection and transformation
- Selected 15 features: numerical service measures, route type, city, and operating-day indicators.
- Route IDs and route names were retained as identifiers/details, not used as model features.
- Numerical and day-of-week features were scaled using Min-Max Scaling.
- City and route type were transformed using One-Hot Encoding.
- The processed feature matrix contains 7312 rows and 20 columns.

## Training and evaluation strategy
RouteRanker is planned to use clustering. Clustering does not require target labels, so no target column or classification-style 80:20 split was created in this module. The clustering evaluation strategy will be documented in the modelling module. If a validation split is used later, preprocessing must be fitted on the training data and then applied to validation data.

## Assumptions and limitations
- Scheduled trip counts describe planned service, not actual passenger demand or overcrowding.
- Distance values are estimated straight-line route distances, not measured road distances.
- Routes excluded from this distance-ready dataset remain in the original dataset.
- No passenger counts or unsupported route-performance labels were created.

## Saved outputs
- `data/processed/module4_processed_features.csv`
- `data/processed/module4_processed_dataset.csv`
- `data/processed/module4_preprocessing_pipeline.pkl`
- `reports/module4_data_preprocessing_report.md`

## Conclusion
The distance-ready route features were checked, selected, scaled, and encoded for the next clustering stage. The original dataset was preserved, and the preprocessing outputs were saved for reproducibility.
