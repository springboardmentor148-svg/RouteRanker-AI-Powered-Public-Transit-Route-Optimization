"""Prepare the RouteRanker route_features tables for machine-learning use.

Requires pandas and numpy. The script auto-detects route-level CSVs in data/raw,
data, or beside this script. It keeps route identifiers as metadata and creates
reproducible city-stratified train
and validation splits, fits imputations and robust scaling on training rows only, and
writes prepared data plus audit logs.

Run from this submission folder:
    python module4_preprocessing.py
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SEED = 42
VALIDATION_FRACTION = 0.20

# Curated route-level features. IDs and source labels stay out of the model.
BASE_NUMERIC = [
    "n_trips",
    "median_stops_per_trip",
    "median_trip_duration_min",
    "service_span_h",
    "n_active_hours",
    "peak_hour_trips",
    "trips_per_active_hour",
    "median_headway_min",
    "weekend_to_weekday_ratio",
    "length_km",
    "n_unique_stops",
    "stops_per_km",
    "max_stop_overlap",
    "overlap_share_of_route",
    "mean_routes_per_stop",
]
HOUR_COLUMNS = ["first_departure_h", "last_departure_h", "peak_hour"]
DAYPART_COLUMNS = ["trips_morning", "trips_afternoon", "trips_evening", "trips_night"]
LOG1P_COLUMNS = [
    "n_trips",
    "median_stops_per_trip",
    "median_trip_duration_min",
    "service_span_h",
    "n_active_hours",
    "peak_hour_trips",
    "trips_per_active_hour",
    "median_headway_min",
    "length_km",
    "n_unique_stops",
    "stops_per_km",
    "mean_routes_per_stop",
]
CYCLIC_FEATURES = [
    "first_departure_sin",
    "first_departure_cos",
    "last_departure_sin",
    "last_departure_cos",
    "peak_hour_sin",
    "peak_hour_cos",
]
BOUNDED_FEATURES = [
    "weekend_to_weekday_ratio",
    "max_stop_overlap",
    "overlap_share_of_route",
    "share_morning",
    "share_afternoon",
    "share_evening",
    "share_night",
    "sparse_schedule",
]
CATEGORICAL_COLUMN = "length_method"
EXCLUDED_COLUMNS = {
    "city": "Kept as metadata and used to stratify the holdout; excluded from X so clusters are not driven by city membership.",
    "route_id": "Kept as an identifier for traceability; never treated as a numeric model feature.",
    "route_name": "Kept as descriptive metadata; high-cardinality names are not model features.",
    "route_type": "Excluded because every supplied route has the same value (3), so it carries no variation.",
    "trips_from_frequency": "Excluded because every supplied route has value 0.",
    "has_time_backwards_trip": "Excluded because every supplied route has value False.",
    "n_directions": "Excluded from X because the entire Delhi file lacks this field; cross-city imputation would add a city-specific bias.",
    "length_km_shape": "Excluded from X because 62.6% of rows lack a value; kept in the source CSV and missing-value log.",
    "length_km_stops": "Excluded in favor of the chosen length_km field to avoid feeding two alternative length estimates.",
    "avg_trip_duration_min": "Excluded in favor of median_trip_duration_min, which is less sensitive to extreme schedule durations.",
    "avg_speed_kmh": "Excluded because the source flags 873 rows as having implausible speeds; the original flag remains metadata.",
    "overlap_partner": "Route reference/identifier, not a numeric or categorical signal for the model.",
    "overlap_partner_name": "Route reference/identifier, not a numeric or categorical signal for the model.",
    "n_service_ids": "Excluded because it is nearly constant (1 for all but seven routes).",
    "trips_monday": "Exact duplicate of n_trips in the supplied data; excluded to avoid double-counting service volume.",
    "trips_tuesday": "Exact duplicate of n_trips in the supplied data; excluded to avoid double-counting service volume.",
    "trips_wednesday": "Exact duplicate of n_trips in the supplied data; excluded to avoid double-counting service volume.",
    "trips_thursday": "Exact duplicate of n_trips in the supplied data; excluded to avoid double-counting service volume.",
    "trips_friday": "Exact duplicate of n_trips in the supplied data; excluded to avoid double-counting service volume.",
    "trips_saturday": "Exact duplicate of n_trips in the supplied data; excluded to avoid double-counting service volume.",
    "trips_sunday": "Daily schedule count omitted in favor of the weekend_to_weekday_ratio summary feature.",
    "avg_trips_per_weekday": "Omitted as a second service-volume summary alongside n_trips.",
    "avg_trips_per_weekend_day": "Omitted as a second service-volume summary alongside n_trips.",
    "speed_implausible": "Retained as data-quality metadata; not used as a route-behavior feature.",
    "source_file": "Retained for provenance; not a model feature.",
}


def has_route_tables(directory: Path) -> bool:
    return directory.is_dir() and any(directory.glob("route_features*.csv"))


def resolve_data_directory(requested: Path | None) -> Path:
    """Find route-feature CSVs relative to the script when no folder is passed."""
    if requested is not None:
        directory = requested.expanduser().resolve()
        if not has_route_tables(directory):
            raise FileNotFoundError(
                f"No route_features*.csv files found in {directory}. "
                "Place the five route-level CSVs in that folder or pass --data-dir."
            )
        return directory

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir / "data" / "raw",
        script_dir / "data",
        script_dir,
        Path.cwd() / "data" / "raw",
        Path.cwd() / "data",
        Path.cwd(),
    ]
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate not in seen and has_route_tables(candidate):
            return candidate
        seen.add(candidate)

    expected = script_dir / "data" / "raw"
    raise FileNotFoundError(
        "No route_features*.csv input files were found. Put the five route-level "
        f"CSV files in {expected}, beside this script, or pass --data-dir <folder>."
    )


def load_route_tables(data_dir: Path) -> tuple[pd.DataFrame, list[str]]:
    paths = sorted(data_dir.glob("route_features*.csv"), key=lambda p: p.name.casefold())
    if not paths:
        raise FileNotFoundError(
            f"No route_features*.csv files found in {data_dir}. "
            "The input filenames may include spaces or copy suffixes; keep the "
            "route_features prefix and check --data-dir."
        )

    frames: list[pd.DataFrame] = []
    for path in paths:
        frame = pd.read_csv(path, dtype={"route_id": "string", "route_name": "string"})
        if "city" not in frame.columns or "route_id" not in frame.columns:
            raise ValueError(f"{path.name} must include city and route_id columns")
        frame["city"] = frame["city"].astype("string").str.strip().str.casefold()
        frame["route_id"] = frame["route_id"].astype("string").str.strip()
        if "route_name" in frame.columns:
            frame["route_name"] = frame["route_name"].astype("string")
        frame["source_file"] = path.name
        frames.append(frame)

    routes = pd.concat(frames, ignore_index=True, sort=False)
    duplicate_key = routes.duplicated(["city", "route_id"], keep=False)
    if duplicate_key.any():
        examples = routes.loc[duplicate_key, ["city", "route_id", "source_file"]].head(10)
        raise ValueError("Duplicate city/route_id keys found; review before preprocessing:\n" + examples.to_string(index=False))
    return routes, [path.name for path in paths]


def make_split(routes: pd.DataFrame, seed: int, validation_fraction: float) -> tuple[list[int], list[int]]:
    rng = np.random.default_rng(seed)
    train_indices: list[int] = []
    validation_indices: list[int] = []
    for city, positions in routes.groupby("city", sort=True).indices.items():
        shuffled = rng.permutation(np.asarray(positions, dtype=int))
        validation_count = max(1, int(round(len(shuffled) * validation_fraction)))
        if validation_count >= len(shuffled):
            raise ValueError(f"Not enough routes in {city} for the requested split")
        validation_indices.extend(shuffled[:validation_count].tolist())
        train_indices.extend(shuffled[validation_count:].tolist())
    return sorted(train_indices), sorted(validation_indices)


def build_base_features(routes: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    required = set(BASE_NUMERIC + HOUR_COLUMNS + DAYPART_COLUMNS + [CATEGORICAL_COLUMN, "sparse_schedule"])
    missing = sorted(required - set(routes.columns))
    if missing:
        raise ValueError(f"Route data is missing required fields: {missing}")

    base = pd.DataFrame(index=routes.index)
    for column in BASE_NUMERIC + HOUR_COLUMNS + DAYPART_COLUMNS:
        base[column] = pd.to_numeric(routes[column], errors="coerce")

    trips = base["n_trips"].replace(0, np.nan)
    for source, target in zip(DAYPART_COLUMNS, ["share_morning", "share_afternoon", "share_evening", "share_night"]):
        base[target] = base[source] / trips
    base["sparse_schedule"] = routes["sparse_schedule"].astype("boolean").astype("float64")

    # Convert clock values to circular features; source values above 24 hours
    # wrap to their time-of-day while the raw source values remain untouched.
    for source, target in zip(HOUR_COLUMNS, ["first_departure", "last_departure", "peak_hour"]):
        hour = base[source] % 24
        radians = 2 * np.pi * hour / 24
        base[f"{target}_sin"] = np.sin(radians)
        base[f"{target}_cos"] = np.cos(radians)
    base = base.drop(columns=HOUR_COLUMNS + DAYPART_COLUMNS)

    category = routes[CATEGORICAL_COLUMN].astype("string").str.strip()
    return base, category


def fit_imputations(
    base: pd.DataFrame,
    routes: pd.DataFrame,
    train_indices: list[int],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    train_city = routes.loc[train_indices, "city"]
    global_medians: dict[str, float] = {}
    city_headway_medians: dict[str, float] = {}
    transformed = base.copy()

    headway_train = base.loc[train_indices, "median_headway_min"]
    global_headway = float(headway_train.median())
    if not np.isfinite(global_headway):
        raise ValueError("median_headway_min has no non-missing training values")
    city_headway = base.loc[train_indices].groupby(train_city)["median_headway_min"].median()
    city_headway_medians = {str(city): float(value) for city, value in city_headway.items() if pd.notna(value)}

    for index in transformed.index:
        if pd.isna(transformed.at[index, "median_headway_min"]):
            city = str(routes.at[index, "city"])
            transformed.at[index, "median_headway_min"] = city_headway_medians.get(city, global_headway)

    for column in transformed.columns:
        values = pd.to_numeric(transformed.loc[train_indices, column], errors="coerce")
        median = float(values.median())
        if not np.isfinite(median):
            raise ValueError(f"Feature {column} has no non-missing training values")
        global_medians[column] = median
        transformed[column] = pd.to_numeric(transformed[column], errors="coerce").fillna(median)

    return transformed, {
        "numeric_training_medians": global_medians,
        "median_headway_city_training_medians": city_headway_medians,
        "median_headway_global_training_fallback": global_headway,
        "categorical_length_method_fill": str(routes.loc[train_indices, CATEGORICAL_COLUMN].mode(dropna=True).iloc[0]),
    }


def slug(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return result or "category"


def transform_features(
    base: pd.DataFrame,
    category: pd.Series,
    routes: pd.DataFrame,
    train_indices: list[int],
    validation_indices: list[int],
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    imputed, imputation_info = fit_imputations(base, routes, train_indices)
    for column in LOG1P_COLUMNS:
        if (imputed[column] < 0).any():
            raise ValueError(f"{column} contains negative values; review before applying log1p")
        imputed[column] = np.log1p(imputed[column])

    numeric_columns = list(imputed.columns)
    scaled_columns = [column for column in numeric_columns if column not in CYCLIC_FEATURES]
    scaler_center = imputed.loc[train_indices, scaled_columns].median()
    q75 = imputed.loc[train_indices, scaled_columns].quantile(0.75)
    q25 = imputed.loc[train_indices, scaled_columns].quantile(0.25)
    scaler_iqr = q75 - q25
    scaler_iqr = scaler_iqr.where(scaler_iqr.abs() > 1e-12, 1.0)
    scaled = imputed[numeric_columns].copy()
    scaled[scaled_columns] = (imputed[scaled_columns] - scaler_center) / scaler_iqr

    cat_values = category.copy()
    cat_mode = imputation_info["categorical_length_method_fill"]
    cat_values = cat_values.fillna(cat_mode).astype("string")
    categories = sorted(cat_values.loc[train_indices].unique().tolist())
    dummy_names: list[str] = []
    cat_matrix = pd.DataFrame(index=routes.index)
    for value in categories:
        name = f"length_method__{slug(str(value))}"
        if name in dummy_names:
            raise ValueError("Categorical values produce colliding one-hot column names")
        dummy_names.append(name)
        cat_matrix[name] = (cat_values == value).astype("float64")

    feature_columns = numeric_columns + dummy_names
    matrix = pd.concat([scaled, cat_matrix], axis=1)[feature_columns]
    if not np.isfinite(matrix.to_numpy(dtype=float)).all():
        raise ValueError("Prepared feature matrix contains missing or infinite values")

    train = matrix.loc[train_indices].reset_index(drop=True)
    validation = matrix.loc[validation_indices].reset_index(drop=True)
    info = {
        "seed": seed,
        "numeric_features_robust_scaled": scaled_columns,
        "cyclic_features": CYCLIC_FEATURES,
        "one_hot_features": dummy_names,
        "length_method_categories_fit_on_training": categories,
        "robust_scaler_medians_fit_on_training": {key: float(value) for key, value in scaler_center.items()},
        "robust_scaler_iqrs_fit_on_training": {key: float(value) for key, value in scaler_iqr.items()},
        **imputation_info,
    }
    return train, validation, info


def write_audit_files(
    routes: pd.DataFrame,
    X_all: pd.DataFrame,
    split_labels: pd.Series,
    manifest: dict[str, Any],
    report_dir: Path,
) -> None:
    missing_rows = []
    for column in routes.columns:
        count = int(routes[column].isna().sum())
        if column == "median_headway_min":
            action = "Imputed with the median from training rows in the same city; used the overall training median only if a city had no training value."
        elif column == "n_directions":
            action = "Not imputed; excluded from model features because the entire Delhi source file lacks this field."
        elif column == "length_km_shape":
            action = "Not imputed; excluded from model features because 62.6% of records are missing."
        elif column in {"overlap_partner", "overlap_partner_name"}:
            action = "Not imputed; identifier/reference fields are excluded from model features."
        elif count:
            action = "Not imputed; excluded from model features or retained only as metadata."
        else:
            action = "No missing values found in the selected route-level input."
        in_feature_matrix = column in BASE_NUMERIC + HOUR_COLUMNS + DAYPART_COLUMNS + ["sparse_schedule", CATEGORICAL_COLUMN]
        missing_rows.append({
            "field": column,
            "missing_before": count,
            "percent_missing_before": round(100 * count / max(len(routes), 1), 2),
            "missing_after_in_feature_matrix": 0 if in_feature_matrix else "not applicable - field not used directly in X",
            "handling_decision": action,
        })
    pd.DataFrame(missing_rows).to_csv(report_dir / "module4_missing_value_log.csv", index=False)

    decisions: dict[str, str] = dict(EXCLUDED_COLUMNS)
    for column in BASE_NUMERIC:
        decisions[column] = "Selected as a route-level numeric feature; missing values are fitted on training rows, log1p is applied where non-negative and skewed, then robust-scaled using training median and IQR."
    for column in HOUR_COLUMNS:
        decisions[column] = "Converted to sine and cosine time-of-day features using hour modulo 24; raw source column retained in the raw CSV."
    for column in DAYPART_COLUMNS:
        decisions[column] = "Converted to a share of n_trips; avoids using absolute period counts as a second copy of route volume."
    decisions["length_method"] = "One-hot encoded using categories observed in the training split; kept as descriptive source metadata in the prepared file."
    decisions["sparse_schedule"] = "Selected as a binary route-schedule feature and robust-scaled with the other numeric features."
    rows = []
    for column in routes.columns:
        rows.append({"field": column, "decision": decisions.get(column, "Retained only in raw inputs; not selected as a model feature."), "model_feature": column in BASE_NUMERIC + HOUR_COLUMNS + DAYPART_COLUMNS + ["sparse_schedule", CATEGORICAL_COLUMN]})
    for column in CYCLIC_FEATURES:
        rows.append({"field": column, "decision": "Engineered from the corresponding hour field; stored in the final feature matrix in [-1, 1] before downstream modeling.", "model_feature": True})
    for column in ["share_morning", "share_afternoon", "share_evening", "share_night"]:
        rows.append({"field": column, "decision": "Engineered as period trips divided by n_trips; robust-scaled using training rows.", "model_feature": True})
    for category, column in zip(manifest["encoding"]["length_method_categories_fit_on_training"], manifest["encoding"]["one_hot_features"]):
        rows.append({"field": column, "decision": f"One-hot indicator for length_method category: {category}.", "model_feature": True})
    pd.DataFrame(rows).to_csv(report_dir / "module4_feature_decisions.csv", index=False)

    cities = manifest["split"]["by_city"]
    city_lines = "\n".join(f"- {city}: {counts['train']:,} train, {counts['validation']:,} validation" for city, counts in cities.items())
    missing_lines = "\n".join(
        f"- `{item['field']}`: {item['missing_before']:,} missing ({item['percent_missing_before']:.2f}%). {item['handling_decision']}"
        for item in missing_rows if item["missing_before"]
    ) or "- No missing input values."
    report = f"""# Module 4 - RouteRanker preprocessing report

## Prepared data

- Route rows: {manifest['rows']['input']:,}; cities: {', '.join(manifest['city_counts'].keys())}.
- Model input columns: {manifest['rows']['features']:,}.
- Train/validation rows: {manifest['split']['train_rows']:,} / {manifest['split']['validation_rows']:,} (80/20 within each city, seed {SEED}).
- The source contains scheduled-service features. It has no passenger counts, occupancy, or demand labels, so none were created.

## Decisions

- `city`, `route_id`, and `route_name` are retained as metadata. They are not part of X; route IDs are identifiers, not numeric measurements.
- `length_method` is one-hot encoded. City is used to stratify the split but left out of X so geographic membership does not dominate clustering.
- `first_departure_h`, `last_departure_h`, and `peak_hour` are represented as sine/cosine pairs. Source hour values above 24 wrap to their time of day for this representation.
- Period trip counts are converted to shares of `n_trips`.
- Skewed non-negative numeric fields use `log1p`, then numeric fields use robust scaling (training median and IQR). Imputation and scaling are fit using training rows only. One-hot indicators remain 0/1.
- No route rows were removed. The 80/20 split is a reproducible validation holdout for downstream work; unsupervised clustering has no target label and should not be described as supervised evaluation.

## Missing values

{missing_lines}

See `module4_missing_value_log.csv` for all fields and `module4_feature_decisions.csv` for every inclusion or exclusion.

## City-stratified split

{city_lines}

## Source quality notes

- The source schema differs: Delhi has no `n_directions` field; it is excluded from X rather than imputed from other cities.
- `length_km_shape` is missing in most records and is excluded from X. The selected `length_km` field remains.
- The source marks {manifest['quality']['speed_implausible_rows']:,} rows as having implausible speed; `avg_speed_kmh` is excluded from X and the original quality flag is retained in metadata.
- Extreme route duration and distance values are retained for traceability; log1p and robust scaling limit their influence. Review the source and domain meaning before making operational claims.

## Output files

- `data/processed/routes_ml_ready.csv`: metadata followed by the complete prepared feature matrix.
- `data/processed/X_train.csv`, `data/processed/X_validation.csv`: feature-only splits ready for downstream unsupervised analysis.
- `data/processed/route_split_manifest.csv`: row identifiers and split assignment.
- `module4_preprocessing_manifest.json`: fitted parameters, feature list, and row counts.

## Reproduce

From this folder run `python module4_preprocessing.py`. Install `numpy` and `pandas` from `requirements.txt` if needed.
"""
    (report_dir / "module4_preprocessing_report.md").write_text(report, encoding="utf-8")


def run(data_dir: Path, output_dir: Path, seed: int, validation_fraction: float) -> dict[str, Any]:
    processed_dir = output_dir / "data" / "processed"
    report_dir = output_dir / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    routes, input_files = load_route_tables(data_dir)
    if not routes["city"].notna().all() or not routes["route_id"].notna().all():
        raise ValueError("city and route_id must be present for every record")
    train_indices, validation_indices = make_split(routes, seed, validation_fraction)
    base, category = build_base_features(routes)
    X_train, X_validation, encoding_info = transform_features(base, category, routes, train_indices, validation_indices, seed)

    split_values = pd.Series("", index=routes.index, dtype="string")
    split_values.loc[train_indices] = "train"
    split_values.loc[validation_indices] = "validation"
    all_feature_rows = pd.concat([X_train.set_axis(train_indices), X_validation.set_axis(validation_indices)]).sort_index()

    metadata_columns = [column for column in ["city", "route_id", "route_name", "route_type", "length_method", "speed_implausible", "source_file"] if column in routes.columns]
    prepared = pd.concat([routes[metadata_columns], split_values.rename("split"), all_feature_rows], axis=1)
    prepared.to_csv(processed_dir / "routes_ml_ready.csv", index=False)
    X_train.to_csv(processed_dir / "X_train.csv", index=False)
    X_validation.to_csv(processed_dir / "X_validation.csv", index=False)
    split_manifest = routes[[column for column in ["city", "route_id", "route_name", "source_file"] if column in routes.columns]].copy()
    split_manifest.insert(0, "record_index", np.arange(len(routes), dtype=int))
    split_manifest["split"] = split_values.to_numpy()
    split_manifest.to_csv(processed_dir / "route_split_manifest.csv", index=False)

    by_city: dict[str, dict[str, int]] = {}
    for city in sorted(routes["city"].dropna().unique().tolist()):
        city_mask = routes["city"] == city
        by_city[str(city)] = {
            "rows": int(city_mask.sum()),
            "train": int((city_mask & (split_values == "train")).sum()),
            "validation": int((city_mask & (split_values == "validation")).sum()),
        }
    manifest: dict[str, Any] = {
        "project": "RouteRanker Module 4 Data Preprocessing",
        "input_files": input_files,
        "rows": {"input": int(len(routes)), "features": int(X_train.shape[1]), "train": int(len(X_train)), "validation": int(len(X_validation))},
        "city_counts": {city: counts["rows"] for city, counts in by_city.items()},
        "split": {"seed": seed, "validation_fraction": validation_fraction, "train_rows": int(len(X_train)), "validation_rows": int(len(X_validation)), "by_city": by_city},
        "quality": {
            "duplicate_city_route_keys": int(routes.duplicated(["city", "route_id"]).sum()),
            "speed_implausible_rows": int(routes["speed_implausible"].fillna(False).astype(bool).sum()) if "speed_implausible" in routes.columns else 0,
            "hour_values_over_24": {column: int((pd.to_numeric(routes[column], errors="coerce") > 24).sum()) for column in HOUR_COLUMNS},
            "length_km_shape_missing": int(routes["length_km_shape"].isna().sum()) if "length_km_shape" in routes.columns else None,
            "n_directions_missing": int(routes["n_directions"].isna().sum()) if "n_directions" in routes.columns else int(len(routes)),
        },
        "encoding": encoding_info,
        "feature_columns": list(X_train.columns),
        "identifiers_excluded_from_X": ["city", "route_id", "route_name", "source_file"],
        "no_target_label": True,
    }
    (processed_dir / "module4_preprocessing_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    write_audit_files(routes, all_feature_rows, split_values, manifest, report_dir)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess RouteRanker route_features tables.")
    parser.add_argument("--data-dir", type=Path, default=None, help="Folder containing route_features*.csv (auto-detected relative to the script folder by default)")
    parser.add_argument("--output-dir", type=Path, default=None, help="Folder for processed data and reports (defaults to the script folder)")
    parser.add_argument("--seed", type=int, default=SEED, help=f"Random seed (default: {SEED})")
    parser.add_argument("--validation-fraction", type=float, default=VALIDATION_FRACTION, help=f"Validation share within each city (default: {VALIDATION_FRACTION})")
    parser.add_argument("--preview-rows", type=int, default=5, help="Number of processed rows to display in the terminal (default: 5)")
    parser.add_argument("--show-all-rows", action="store_true", help="Print every prepared row in the terminal; can produce a very large output")
    args = parser.parse_args()
    if not 0 < args.validation_fraction < 1:
        parser.error("--validation-fraction must be greater than 0 and less than 1")
    if args.preview_rows < 1:
        parser.error("--preview-rows must be at least 1")
    return args


def print_terminal_results(manifest: dict[str, Any], output_dir: Path, preview_rows: int, show_all_rows: bool) -> None:
    """Print the preprocessing summary and a preview of the generated CSV."""
    processed_dir = output_dir / "data" / "processed"
    prepared_path = processed_dir / "routes_ml_ready.csv"
    missing_path = output_dir / "reports" / "module4_missing_value_log.csv"
    prepared = pd.read_csv(prepared_path)
    missing = pd.read_csv(missing_path)

    print("\n=== Module 4 preprocessing results ===")
    print(f"Rows prepared: {manifest['rows']['input']:,}")
    print(f"Cities: {', '.join(manifest['city_counts'])}")
    print(f"Feature columns: {manifest['rows']['features']}")
    print(f"Training / validation rows: {manifest['rows']['train']:,} / {manifest['rows']['validation']:,}")
    print("\nMissing input values that required review:")
    nonzero_missing = missing.loc[missing["missing_before"].fillna(0).astype(int) > 0]
    if nonzero_missing.empty:
        print("  None")
    else:
        for _, item in nonzero_missing.iterrows():
            action = str(item["handling_decision"]).strip()
            print(f"  {item['field']}: {int(item['missing_before']):,} ({item['percent_missing_before']:.2f}%) — {action}")

    encoding = manifest["encoding"]
    print("\nPreprocessing applied:")
    print("  Numeric features: training-set median imputation where needed, log1p for selected skewed fields, then robust scaling.")
    print("  Categorical feature: length_method one-hot encoded from categories in the training split.")
    print("  Hour features: sine/cosine encoding; period trip counts converted to shares.")
    print(f"  One-hot columns: {', '.join(encoding.get('one_hot_features', [])) or 'none'}")
    print(f"\nPrepared CSV preview ({'all rows' if show_all_rows else f'first {min(preview_rows, len(prepared))} rows'}):")
    with pd.option_context("display.max_columns", None, "display.width", 240, "display.max_colwidth", 32):
        shown = prepared if show_all_rows else prepared.head(preview_rows)
        print(shown.to_string(index=False))
    print(f"\nComplete prepared dataset: {prepared_path}")


def main() -> int:
    args = parse_args()
    data_dir = resolve_data_directory(args.data_dir)
    output_dir = args.output_dir.expanduser().resolve() if args.output_dir else Path(__file__).resolve().parent
    manifest = run(data_dir, output_dir, args.seed, args.validation_fraction)
    print(f"Prepared {manifest['rows']['input']:,} route rows from {len(manifest['city_counts'])} cities.")
    print(f"Feature matrix: {manifest['rows']['features']} columns; train={manifest['rows']['train']:,}, validation={manifest['rows']['validation']:,}.")
    print(f"Saved outputs under {output_dir}")
    print_terminal_results(manifest, output_dir, args.preview_rows, args.show_all_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
