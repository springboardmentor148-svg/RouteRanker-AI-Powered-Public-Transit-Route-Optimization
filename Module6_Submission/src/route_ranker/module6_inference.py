"""Inference helpers for the previously trained RouteRanker Module 5 models.

This module never refits a clusterer or a scaler. Raw route-feature inputs are
transformed with the exact medians, log transforms, robust scaling parameters,
and one-hot categories stored in Module 4's preprocessing manifest.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


BASE_NUMERIC = [
    "n_trips", "median_stops_per_trip", "median_trip_duration_min", "service_span_h",
    "n_active_hours", "peak_hour_trips", "trips_per_active_hour", "median_headway_min",
    "weekend_to_weekday_ratio", "length_km", "n_unique_stops", "stops_per_km",
    "max_stop_overlap", "overlap_share_of_route", "mean_routes_per_stop",
]
HOUR_COLUMNS = ["first_departure_h", "last_departure_h", "peak_hour"]
DAYPART_COLUMNS = ["trips_morning", "trips_afternoon", "trips_evening", "trips_night"]
LOG1P_COLUMNS = [
    "n_trips", "median_stops_per_trip", "median_trip_duration_min", "service_span_h",
    "n_active_hours", "peak_hour_trips", "trips_per_active_hour", "median_headway_min",
    "length_km", "n_unique_stops", "stops_per_km", "mean_routes_per_stop",
]
CYCLIC_FEATURES = [
    "first_departure_sin", "first_departure_cos", "last_departure_sin",
    "last_departure_cos", "peak_hour_sin", "peak_hour_cos",
]
IDENTIFIER_COLUMNS = ["city", "route_id", "route_name", "split", "source_file"]


def _slug(value: str) -> str:
    import re

    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value or "category"


def load_preprocessing_manifest(project_root: Path) -> dict[str, Any]:
    candidates = [
        project_root / "data" / "processed" / "module4_preprocessing_manifest.json",
        project_root / "models" / "module4_preprocessing_manifest.json",
    ]
    manifest_path = next((path for path in candidates if path.is_file()), None)
    if manifest_path is None:
        raise FileNotFoundError(
            "Module 4 preprocessing manifest was not found. Expected it under "
            "data/processed/ or models/."
        )
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _boolean_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.astype("float64")
    normalized = series.astype("string").str.strip().str.casefold()
    mapped = normalized.map({"true": 1.0, "false": 0.0, "1": 1.0, "0": 0.0, "yes": 1.0, "no": 0.0})
    return mapped.astype("float64")


def prepare_features(raw_or_prepared: pd.DataFrame, manifest: dict[str, Any]) -> tuple[pd.DataFrame, np.ndarray, str]:
    """Return metadata and the Module 5 feature matrix for raw or prepared rows."""
    if raw_or_prepared.empty:
        raise ValueError("Inference input has no route rows.")
    feature_columns = list(manifest.get("feature_columns", []))
    if not feature_columns:
        raise ValueError("Preprocessing manifest does not declare feature_columns.")

    metadata = raw_or_prepared[[c for c in IDENTIFIER_COLUMNS if c in raw_or_prepared.columns]].copy()
    for required_id in ("city", "route_id"):
        if required_id not in metadata:
            raise ValueError(f"Inference input is missing required identifier column {required_id!r}.")
    metadata["city"] = metadata["city"].astype("string").str.strip().str.casefold()
    metadata["route_id"] = metadata["route_id"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)

    # A Module 4 prepared file already contains all model columns. Do not scale it twice.
    raw_signature = {"first_departure_h", "last_departure_h", "trips_morning", "length_method"}
    if set(feature_columns).issubset(raw_or_prepared.columns) and not raw_signature.issubset(raw_or_prepared.columns):
        feature_frame = raw_or_prepared[feature_columns].apply(pd.to_numeric, errors="coerce")
        if feature_frame.isna().any().any() or not np.isfinite(feature_frame.to_numpy(dtype=np.float64)).all():
            raise ValueError("Prepared inference data contains missing or nonnumeric model features.")
        return metadata.reset_index(drop=True), feature_frame.to_numpy(dtype=np.float64), "module4_prepared"

    required_raw = set(BASE_NUMERIC + HOUR_COLUMNS + DAYPART_COLUMNS + ["length_method", "sparse_schedule"])
    missing = sorted(required_raw - set(raw_or_prepared.columns))
    if missing:
        raise ValueError(
            "Raw inference data is missing fields required by the Module 4 preprocessing recipe: "
            + ", ".join(missing)
        )

    encoding = manifest.get("encoding", {})
    numeric_medians = encoding.get("numeric_training_medians", {})
    city_headway_medians = encoding.get("median_headway_city_training_medians", {})
    global_headway_median = encoding.get("median_headway_global_training_fallback")
    if global_headway_median is None:
        raise ValueError("Preprocessing manifest lacks the fitted global headway fallback.")
    base = pd.DataFrame(index=raw_or_prepared.index)
    for column in BASE_NUMERIC + HOUR_COLUMNS + DAYPART_COLUMNS:
        base[column] = pd.to_numeric(raw_or_prepared[column], errors="coerce")

    trips = base["n_trips"].replace(0, np.nan)
    for source, target in zip(DAYPART_COLUMNS, ["share_morning", "share_afternoon", "share_evening", "share_night"]):
        base[target] = base[source] / trips
    base["sparse_schedule"] = _boolean_numeric(raw_or_prepared["sparse_schedule"])

    for source, target in zip(HOUR_COLUMNS, ["first_departure", "last_departure", "peak_hour"]):
        hour = base[source] % 24
        radians = 2.0 * np.pi * hour / 24.0
        base[f"{target}_sin"] = np.sin(radians)
        base[f"{target}_cos"] = np.cos(radians)
    base = base.drop(columns=HOUR_COLUMNS + DAYPART_COLUMNS)

    cities = metadata["city"].astype(str)
    missing_headway = base["median_headway_min"].isna()
    for idx in base.index[missing_headway]:
        city = cities.loc[idx]
        base.at[idx, "median_headway_min"] = city_headway_medians.get(city, global_headway_median)

    for column in base.columns:
        if column not in numeric_medians:
            raise ValueError(f"Preprocessing manifest has no training imputation value for {column!r}.")
        base[column] = pd.to_numeric(base[column], errors="coerce").fillna(float(numeric_medians[column]))

    for column in LOG1P_COLUMNS:
        if (base[column] < 0).any():
            raise ValueError(f"Raw inference feature {column!r} contains negative values; log1p cannot be applied.")
        base[column] = np.log1p(base[column])

    scaler_medians = encoding.get("robust_scaler_medians_fit_on_training", {})
    scaler_iqrs = encoding.get("robust_scaler_iqrs_fit_on_training", {})
    scaled_columns = encoding.get("numeric_features_robust_scaled", [])
    scaled = base.copy()
    for column in scaled_columns:
        if column not in scaler_medians or column not in scaler_iqrs:
            raise ValueError(f"Fitted robust-scaler values are missing for {column!r}.")
        scale = float(scaler_iqrs[column])
        if abs(scale) <= 1e-12:
            scale = 1.0
        scaled[column] = (scaled[column] - float(scaler_medians[column])) / scale

    categories = encoding.get("length_method_categories_fit_on_training", [])
    category_fill = encoding.get("categorical_length_method_fill")
    if not categories or category_fill is None:
        raise ValueError("Preprocessing manifest lacks fitted length_method categories/fill value.")
    category = raw_or_prepared["length_method"].astype("string").str.strip().fillna(str(category_fill))
    for value in categories:
        name = f"length_method__{_slug(str(value))}"
        scaled[name] = (category == str(value)).astype("float64")
    missing_features = sorted(set(feature_columns) - set(scaled.columns))
    if missing_features:
        raise ValueError(f"Could not construct expected Module 5 features: {missing_features}")
    feature_frame = scaled[feature_columns].apply(pd.to_numeric, errors="coerce")
    values = feature_frame.to_numpy(dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("Preprocessing produced missing or infinite inference features.")
    return metadata.reset_index(drop=True), values, "raw_transformed_with_module4_manifest"


def _nearest_centroid(values: np.ndarray, centroids: np.ndarray, batch_size: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    labels = np.empty(len(values), dtype=np.int32)
    distances = np.empty(len(values), dtype=np.float64)
    for start in range(0, len(values), batch_size):
        stop = min(start + batch_size, len(values))
        difference = values[start:stop, None, :] - centroids[None, :, :]
        squared = np.einsum("ijk,ijk->ij", difference, difference)
        nearest = np.argmin(squared, axis=1)
        labels[start:stop] = nearest.astype(np.int32)
        distances[start:stop] = np.sqrt(squared[np.arange(stop - start), nearest])
    return labels, distances


def _nearest_dbscan_core(values: np.ndarray, core_samples: np.ndarray, core_labels: np.ndarray,
                         eps: float, batch_size: int = 128) -> tuple[np.ndarray, np.ndarray]:
    labels = np.full(len(values), -1, dtype=np.int32)
    nearest_distances = np.empty(len(values), dtype=np.float64)
    core_norm = np.einsum("ij,ij->i", core_samples, core_samples)[None, :]
    for start in range(0, len(values), batch_size):
        stop = min(start + batch_size, len(values))
        chunk = values[start:stop]
        squared = np.einsum("ij,ij->i", chunk, chunk)[:, None] + core_norm - 2.0 * (chunk @ core_samples.T)
        np.maximum(squared, 0.0, out=squared)
        nearest = np.argmin(squared, axis=1)
        distances = np.sqrt(squared[np.arange(stop - start), nearest])
        accepted = distances <= eps
        labels[start:stop] = np.where(accepted, core_labels[nearest], -1)
        nearest_distances[start:stop] = distances
    return labels, nearest_distances


def run_inference(project_root: Path, input_path: Path, output_path: Path | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    project_root = project_root.resolve()
    input_path = input_path.resolve()
    output_path = output_path or (project_root / "results" / "inference_assignments.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not input_path.is_file():
        raise FileNotFoundError(f"Inference CSV was not found: {input_path}")

    manifest = load_preprocessing_manifest(project_root)
    metadata, values, preprocessing_mode = prepare_features(pd.read_csv(input_path), manifest)
    feature_columns = list(manifest["feature_columns"])

    index_path = project_root / "models" / "model_index.json"
    if not index_path.is_file():
        raise FileNotFoundError(f"Module 5 model index was not found: {index_path}")
    model_index = json.loads(index_path.read_text(encoding="utf-8"))
    selected_k = int(model_index["selected_kmeans_k"])
    kmeans_path = project_root / "models" / f"kmeans_k{selected_k}.npz"
    kmeans_meta_path = kmeans_path.with_suffix(".json")
    if not kmeans_path.is_file() or not kmeans_meta_path.is_file():
        raise FileNotFoundError(f"Selected trained K-Means model or metadata is missing: {kmeans_path}")
    kmeans_info = json.loads(kmeans_meta_path.read_text(encoding="utf-8"))
    if kmeans_info.get("features") != feature_columns:
        raise ValueError("K-Means feature order does not match the saved Module 4 preprocessing manifest.")
    with np.load(kmeans_path, allow_pickle=False) as saved:
        centroids = np.asarray(saved["centroids"], dtype=np.float64)
    if centroids.shape != (selected_k, len(feature_columns)):
        raise ValueError(f"K-Means centroids have unexpected shape {centroids.shape}.")

    dbscan_meta_path = project_root / "models" / "dbscan_model.json"
    dbscan_path = project_root / "models" / str(model_index.get("dbscan_model", "dbscan_model.npz"))
    dbscan_info = json.loads(dbscan_meta_path.read_text(encoding="utf-8"))
    if dbscan_info.get("features") != feature_columns:
        raise ValueError("DBSCAN feature order does not match the saved Module 4 preprocessing manifest.")
    with np.load(dbscan_path, allow_pickle=False) as saved:
        core_samples = np.asarray(saved["core_samples"], dtype=np.float64)
        core_labels = np.asarray(saved["core_labels"], dtype=np.int32)
    if core_samples.ndim != 2 or core_samples.shape[1] != len(feature_columns) or len(core_labels) != len(core_samples):
        raise ValueError("Saved DBSCAN core sample arrays have unexpected shapes.")

    kmeans_labels, kmeans_distance = _nearest_centroid(values, centroids)
    dbscan_labels, dbscan_core_distance = _nearest_dbscan_core(
        values, core_samples, core_labels, float(dbscan_info["eps"])
    )
    assignments = metadata.copy()
    assignments["kmeans_cluster"] = kmeans_labels
    assignments["kmeans_distance_to_centroid"] = kmeans_distance
    assignments["dbscan_cluster"] = dbscan_labels
    assignments["dbscan_is_noise"] = dbscan_labels == -1
    assignments["dbscan_nearest_core_distance"] = dbscan_core_distance

    classifier_status: dict[str, str] = {}
    for display_name, filename, output_column in [
        ("Random Forest", "random_forest_model.joblib", "random_forest_prediction"),
        ("XGBoost", "xgboost_model.joblib", "xgboost_prediction"),
    ]:
        classifier_path = project_root / "models" / filename
        if not classifier_path.is_file():
            classifier_status[display_name] = "NOT_AVAILABLE_NO_TRAINED_LABELLED_MODEL"
            continue
        try:
            from joblib import load

            payload = load(classifier_path)
            classifier = payload["model"] if isinstance(payload, dict) and "model" in payload else payload
            class_names = payload.get("class_names", []) if isinstance(payload, dict) else []
            predicted = classifier.predict(values)
            assignments[output_column] = [
                str(class_names[int(value)]) if class_names and 0 <= int(value) < len(class_names) else str(value)
                for value in predicted
            ]
            classifier_status[display_name] = "PREDICTED"
        except Exception as error:  # optional dependency/model compatibility must not block clustering inference
            classifier_status[display_name] = f"SKIPPED_MODEL_LOAD_OR_PREDICT_ERROR: {type(error).__name__}: {error}"

    assignments.to_csv(output_path, index=False)
    def counts(labels: np.ndarray) -> dict[str, int]:
        unique, number = np.unique(labels, return_counts=True)
        return {str(int(label)): int(count) for label, count in zip(unique, number)}

    summary = {
        "input_file": str(input_path.relative_to(project_root)) if input_path.is_relative_to(project_root) else input_path.name,
        "output_file": str(output_path.relative_to(project_root)) if output_path.is_relative_to(project_root) else output_path.name,
        "input_rows": int(len(assignments)),
        "feature_count": int(len(feature_columns)),
        "preprocessing_mode": preprocessing_mode,
        "selected_kmeans_k": selected_k,
        "kmeans_cluster_counts": counts(kmeans_labels),
        "dbscan_eps": float(dbscan_info["eps"]),
        "dbscan_min_samples": int(dbscan_info["min_samples"]),
        "dbscan_cluster_counts_including_noise": counts(dbscan_labels),
        "dbscan_noise_rows": int(np.sum(dbscan_labels == -1)),
        "dbscan_noise_share": float(np.mean(dbscan_labels == -1)),
        "dbscan_assignment_method": "Nearest saved DBSCAN core sample within eps; approximate because DBSCAN has no native predict method.",
        "classification_status": classifier_status,
    }
    return assignments, summary
