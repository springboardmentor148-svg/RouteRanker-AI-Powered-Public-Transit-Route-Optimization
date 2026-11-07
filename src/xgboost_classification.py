from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
from xgboost import XGBClassifier

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "data" / "processed" / "module5_classification_dataset_module4.csv"
MODEL_DIR = PROJECT_DIR / "models"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH)

feature_columns = [
    column for column in df.columns
    if column.startswith("numeric__")
]

X = df[feature_columns]
y = df["route_type"].astype(int)

# Metro = 1; Bus = 3.
# XGBoost uses binary labels: Metro = 1; Bus = 0.
y_binary = (y == 1).astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_binary,
    test_size=0.20,
    random_state=42,
    stratify=y_binary
)

metro_count = int((y_train == 1).sum())
bus_count = int((y_train == 0).sum())
scale_pos_weight = bus_count / metro_count

model = XGBClassifier(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions_binary = model.predict(X_test)

# Convert predictions back to the original GTFS route_type labels.
y_test_original = np.where(y_test == 1, 1, 3)
predictions = np.where(predictions_binary == 1, 1, 3)

accuracy = accuracy_score(y_test_original, predictions)
precision = precision_score(
    y_test_original, predictions, labels=[1, 3],
    average="macro", zero_division=0
)
recall = recall_score(
    y_test_original, predictions, labels=[1, 3],
    average="macro", zero_division=0
)
f1 = f1_score(
    y_test_original, predictions, labels=[1, 3],
    average="macro", zero_division=0
)

results = pd.DataFrame([{
    "Model": "XGBoost",
    "Accuracy": accuracy,
    "Precision_macro": precision,
    "Recall_macro": recall,
    "F1_macro": f1
}])

results.to_csv(
    OUTPUT_DIR / "xgboost_evaluation_module4.csv",
    index=False
)

joblib.dump(
    model,
    MODEL_DIR / "xgboost_classifier_module4.pkl"
)

print("XGBoost training completed!")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Features used:", len(feature_columns))
print("\nEvaluation results:")
print(results.to_string(index=False))
print("\nConfusion Matrix (labels: Metro=1, Bus=3):")
print(confusion_matrix(
    y_test_original, predictions, labels=[1, 3]
))
print("\nClassification Report:")
print(classification_report(
    y_test_original, predictions, labels=[1, 3],
    target_names=["Metro", "Bus"], zero_division=0
))
print("\nModel saved successfully.")
