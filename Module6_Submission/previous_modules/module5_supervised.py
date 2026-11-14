"""Optional Random Forest and XGBoost classification when valid labels exist.

The delivered route schedule data has no ground-truth class or demand target.
This module records that gap and trains models only after the user supplies
route labels in data/labels/route_labels.csv.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def route_key(frame: pd.DataFrame) -> pd.Series:
    return frame["city"].astype(str).str.casefold() + "::" + frame["route_id"].astype(str).str.replace(r"\.0$", "", regex=True)


def no_label_results(root: Path, status: str, note: str) -> list[dict[str, Any]]:
    rows = [{"model": model, "status": status, "accuracy": "", "precision_macro": "", "recall_macro": "", "f1_macro": "",
             "test_rows": "", "confusion_matrix_file": "", "note": note} for model in ("Random Forest", "XGBoost")]
    (root / "results").mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(root / "results" / "classification_metrics.csv", index=False)
    return rows


def evaluate_model(name: str, model: Any, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray,
                   class_names: list[str], merged_test: pd.DataFrame, feature_columns: list[str], root: Path,
                   sample_weight: np.ndarray | None = None) -> dict[str, Any]:
    from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
    from joblib import dump

    if sample_weight is None:
        model.fit(X_train, y_train)
    else:
        model.fit(X_train, y_train, sample_weight=sample_weight)
    predictions = model.predict(X_test).astype(int)
    cm = confusion_matrix(y_test, predictions, labels=np.arange(len(class_names)))
    safe_name = name.casefold().replace(" ", "_")
    matrix_name = f"{safe_name}_confusion_matrix.csv"
    matrix_frame = pd.DataFrame(cm, index=[f"actual_{item}" for item in class_names], columns=[f"predicted_{item}" for item in class_names])
    matrix_frame.to_csv(root / "results" / matrix_name, index=True, index_label="class")
    predictions_frame = merged_test[[column for column in ["city", "route_id", "route_name"] if column in merged_test]].copy()
    predictions_frame["actual_label"] = [class_names[index] for index in y_test]
    predictions_frame["predicted_label"] = [class_names[index] for index in predictions]
    predictions_frame.to_csv(root / "results" / f"{safe_name}_test_predictions.csv", index=False)
    dump({"model": model, "feature_columns": feature_columns, "class_names": class_names}, root / "models" / f"{safe_name}_model.joblib")
    return {"model": name, "status": "TRAINED", "accuracy": accuracy_score(y_test, predictions),
            "precision_macro": precision_score(y_test, predictions, average="macro", zero_division=0),
            "recall_macro": recall_score(y_test, predictions, average="macro", zero_division=0),
            "f1_macro": f1_score(y_test, predictions, average="macro", zero_division=0), "test_rows": len(y_test),
            "confusion_matrix_file": matrix_name, "note": "Held-out stratified test split; features contain only Module 4 inputs."}


def run(root: Path, labels_path: Path | None = None, seed: int = 42) -> list[dict[str, Any]]:
    root = root.resolve()
    prepared_path = root / "data" / "processed" / "routes_ml_ready.csv"
    labels_path = labels_path or (root / "data" / "labels" / "route_labels.csv")
    if not labels_path.exists() or not prepared_path.exists():
        return no_label_results(root, "NOT_EVALUATED_NO_GROUND_TRUTH_LABELS",
                                "The project contains no route category or passenger-demand labels. Add valid labels to data/labels/route_labels.csv.")
    labels = pd.read_csv(labels_path)
    required = {"city", "route_id", "label"}
    if not required.issubset(labels.columns):
        return no_label_results(root, "SKIPPED_INVALID_LABEL_FILE", "Label CSV must contain city, route_id, and label columns.")
    labels = labels.dropna(subset=["city", "route_id", "label"]).copy()
    if labels.empty or labels["label"].nunique() < 2:
        return no_label_results(root, "NOT_EVALUATED_INSUFFICIENT_LABEL_CLASSES", "At least two valid label classes with multiple examples are required.")
    labels["route_key"] = route_key(labels)
    if labels["route_key"].duplicated().any():
        return no_label_results(root, "SKIPPED_DUPLICATE_ROUTE_LABELS", "Each city and route_id must have exactly one ground-truth label.")
    prepared = pd.read_csv(prepared_path)
    manifest_path = prepared_path.parent / "module4_preprocessing_manifest.json"
    import json
    feature_columns = json.loads(manifest_path.read_text(encoding="utf-8")).get("feature_columns", []) if manifest_path.exists() else []
    feature_columns = [column for column in feature_columns if column in prepared.columns]
    if not feature_columns:
        return no_label_results(root, "SKIPPED_MISSING_FEATURES", "No prepared Module 4 model features were found.")
    prepared["route_key"] = route_key(prepared)
    merged = prepared.merge(labels[["route_key", "label"]], on="route_key", how="inner", validate="one_to_one")
    merged = merged.dropna(subset=feature_columns + ["label"]).copy()
    if merged["label"].nunique() < 2 or merged["label"].value_counts().min() < 2:
        return no_label_results(root, "NOT_EVALUATED_INSUFFICIENT_LABEL_SUPPORT", "Every class needs at least two labeled routes to create a stratified holdout.")

    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import LabelEncoder
        from sklearn.utils.class_weight import compute_sample_weight
    except ImportError:
        return no_label_results(root, "SKIPPED_OPTIONAL_DEPENDENCIES_MISSING", "Install requirements-supervised.txt to train/evaluate classifiers.")

    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(merged["label"].astype(str))
    class_names = [str(item) for item in label_encoder.classes_]
    X = merged[feature_columns].to_numpy(dtype=float)
    indices = np.arange(len(merged))
    try:
        train_indices, test_indices = train_test_split(indices, test_size=0.20, random_state=seed, stratify=y)
    except ValueError as error:
        return no_label_results(root, "SKIPPED_INVALID_CLASS_DISTRIBUTION", str(error))
    y_train, y_test = y[train_indices], y[test_indices]
    X_train, X_test = X[train_indices], X[test_indices]
    merged_test = merged.iloc[test_indices].reset_index(drop=True)
    root.joinpath("models").mkdir(parents=True, exist_ok=True)
    root.joinpath("results").mkdir(parents=True, exist_ok=True)
    model_rows = []
    random_forest = RandomForestClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=2,
                                           class_weight="balanced_subsample", random_state=seed, n_jobs=-1)
    model_rows.append(evaluate_model("Random Forest", random_forest, X_train, X_test, y_train, y_test, class_names,
                                     merged_test, feature_columns, root))
    try:
        from xgboost import XGBClassifier
        xgb_options = {"n_estimators": 350, "max_depth": 5, "learning_rate": 0.05, "subsample": 0.85,
                       "colsample_bytree": 0.85, "objective": "multi:softprob" if len(class_names) > 2 else "binary:logistic",
                       "eval_metric": "mlogloss", "random_state": seed, "n_jobs": -1}
        if len(class_names) > 2:
            xgb_options["num_class"] = len(class_names)
        xgb = XGBClassifier(**xgb_options)
        weights = compute_sample_weight(class_weight="balanced", y=y_train)
        model_rows.append(evaluate_model("XGBoost", xgb, X_train, X_test, y_train, y_test, class_names,
                                         merged_test, feature_columns, root, sample_weight=weights))
    except ImportError:
        model_rows.append({"model": "XGBoost", "status": "SKIPPED_OPTIONAL_DEPENDENCY_MISSING", "accuracy": "", "precision_macro": "",
                           "recall_macro": "", "f1_macro": "", "test_rows": "", "confusion_matrix_file": "",
                           "note": "Install requirements-supervised.txt to train XGBoost."})
    except Exception as error:
        model_rows.append({"model": "XGBoost", "status": "FAILED", "accuracy": "", "precision_macro": "", "recall_macro": "",
                           "f1_macro": "", "test_rows": "", "confusion_matrix_file": "", "note": str(error)})
    pd.DataFrame(model_rows).to_csv(root / "results" / "classification_metrics.csv", index=False)
    return model_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Train supervised RouteRanker classifiers when labels are available.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--labels", type=Path, default=None)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    for row in run(args.project_root, args.labels, args.seed):
        print(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
