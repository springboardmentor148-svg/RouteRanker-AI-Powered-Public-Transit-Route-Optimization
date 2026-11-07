from pathlib import Path
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

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

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

model = RandomForestClassifier(
    n_estimators=300,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
precision = precision_score(
    y_test, predictions, labels=[1, 3],
    average="macro", zero_division=0
)
recall = recall_score(
    y_test, predictions, labels=[1, 3],
    average="macro", zero_division=0
)
f1 = f1_score(
    y_test, predictions, labels=[1, 3],
    average="macro", zero_division=0
)

results = pd.DataFrame([{
    "Model": "Random Forest",
    "Accuracy": accuracy,
    "Precision_macro": precision,
    "Recall_macro": recall,
    "F1_macro": f1
}])

results.to_csv(
    OUTPUT_DIR / "random_forest_evaluation_module4.csv",
    index=False
)

joblib.dump(
    model,
    MODEL_DIR / "random_forest_classifier_module4.pkl"
)

print("Random Forest training completed!")
print("Training records:", len(X_train))
print("Testing records:", len(X_test))
print("Features used:", len(feature_columns))
print("\nEvaluation results:")
print(results.to_string(index=False))
print("\nConfusion Matrix (labels: Metro=1, Bus=3):")
print(confusion_matrix(y_test, predictions, labels=[1, 3]))
print("\nClassification Report:")
print(classification_report(
    y_test, predictions, labels=[1, 3],
    target_names=["Metro", "Bus"], zero_division=0
))
print("\nModel saved successfully.")
