# Module 4 - RouteRanker preprocessing report

## Prepared data

- Route rows: 12,660; cities: bengaluru, chennai, delhi, hyderabad, pune.
- Model input columns: 29.
- Train/validation rows: 10,128 / 2,532 (80/20 within each city, seed 42).
- The source contains scheduled-service features. It has no passenger counts, occupancy, or demand labels, so none were created.

## Decisions

- `city`, `route_id`, and `route_name` are retained as metadata. They are not part of X; route IDs are identifiers, not numeric measurements.
- `length_method` is one-hot encoded. City is used to stratify the split but left out of X so geographic membership does not dominate clustering.
- `first_departure_h`, `last_departure_h`, and `peak_hour` are represented as sine/cosine pairs. Source hour values above 24 wrap to their time of day for this representation.
- Period trip counts are converted to shares of `n_trips`.
- Skewed non-negative numeric fields use `log1p`, then numeric fields use robust scaling (training median and IQR). Imputation and scaling are fit using training rows only. One-hot indicators remain 0/1.
- No route rows were removed. The 80/20 split is a reproducible validation holdout for downstream work; unsupervised clustering has no target label and should not be described as supervised evaluation.

## Missing values

- `n_directions`: 2,964 missing (23.41%). Not imputed; excluded from model features because the entire Delhi source file lacks this field.
- `median_headway_min`: 2,153 missing (17.01%). Imputed with the median from training rows in the same city; used the overall training median only if a city had no training value.
- `length_km_shape`: 7,929 missing (62.63%). Not imputed; excluded from model features because 62.6% of records are missing.
- `overlap_partner`: 15 missing (0.12%). Not imputed; identifier/reference fields are excluded from model features.
- `overlap_partner_name`: 15 missing (0.12%). Not imputed; identifier/reference fields are excluded from model features.

See `module4_missing_value_log.csv` for all fields and `module4_feature_decisions.csv` for every inclusion or exclusion.

## City-stratified split

- bengaluru: 3,533 train, 883 validation
- chennai: 3,147 train, 787 validation
- delhi: 2,371 train, 593 validation
- hyderabad: 825 train, 206 validation
- pune: 252 train, 63 validation

## Source quality notes

- The source schema differs: Delhi has no `n_directions` field; it is excluded from X rather than imputed from other cities.
- `length_km_shape` is missing in most records and is excluded from X. The selected `length_km` field remains.
- The source marks 873 rows as having implausible speed; `avg_speed_kmh` is excluded from X and the original quality flag is retained in metadata.
- Extreme route duration and distance values are retained for traceability; log1p and robust scaling limit their influence. Review the source and domain meaning before making operational claims.

## Output files

- `data/processed/routes_ml_ready.csv`: metadata followed by the complete prepared feature matrix.
- `data/processed/X_train.csv`, `data/processed/X_validation.csv`: feature-only splits ready for downstream unsupervised analysis.
- `data/processed/route_split_manifest.csv`: row identifiers and split assignment.
- `module4_preprocessing_manifest.json`: fitted parameters, feature list, and row counts.

## Reproduce

From this folder run `python module4_preprocessing.py`. Install `numpy` and `pandas` from `requirements.txt` if needed.
