
# ================================================================
# ROUTERANKER - MILESTONE 3
# Model Selection, Training and Inference
# ================================================================

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import joblib

from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans, DBSCAN
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    silhouette_score
)

from xgboost import XGBClassifier


# ------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------

INPUT_FILE = "reports/combined_route_features.csv"

REPORT_DIR = "reports"
MODEL_DIR = "models"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 70)
print("ROUTERANKER - MILESTONE 3")
print("MODEL SELECTION, TRAINING AND INFERENCE")
print("=" * 70)


# ------------------------------------------------
# 2. LOAD DATA
# ------------------------------------------------

print("\n[1/9] Loading route features...")

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        "Missing reports/combined_route_features.csv"
    )

df = pd.read_csv(INPUT_FILE)

df.columns = df.columns.str.strip()

if "city" not in df.columns:
    raise ValueError("Missing city column.")

if "route_id" not in df.columns:
    raise ValueError("Missing route_id column.")

df = df.drop_duplicates(
    subset=["city", "route_id"]
).reset_index(drop=True)

print("Routes loaded:", len(df))
print("Cities:", df["city"].nunique())


# ------------------------------------------------
# 3. PREPARE FEATURES
# ------------------------------------------------

print("\n[2/9] Preparing features...")

excluded_columns = [
    "city",
    "route_id",
    "route_short_name",
    "route_long_name",
    "route_type",
    "operational_proxy_label",
    "operational_proxy_score"
]

numeric_df = df.select_dtypes(include=[np.number]).copy()

numeric_df = numeric_df.drop(
    columns=[
        c for c in excluded_columns
        if c in numeric_df.columns
    ],
    errors="ignore"
)

numeric_df = numeric_df.replace(
    [np.inf, -np.inf], np.nan
)

numeric_df = numeric_df.dropna(
    axis=1, how="all"
)

numeric_df = numeric_df.loc[
    :, numeric_df.nunique(dropna=True) > 1
]

if numeric_df.shape[1] == 0:
    raise ValueError("No usable numeric features found.")

numeric_df = numeric_df.fillna(
    numeric_df.median()
)

numeric_df = numeric_df.astype(float)

print("Feature count:", numeric_df.shape[1])


# ------------------------------------------------
# 4. CREATE OPERATIONAL PROXY LABELS
# ------------------------------------------------

print("\n[3/9] Creating operational proxy labels...")

score = pd.Series(0.0, index=df.index)

feature_weights = {
    "scheduled_trip_count": 0.35,
    "average_trip_duration_minutes": 0.20,
    "average_stops_per_trip": 0.15,
    "average_headway_minutes": -0.20,
    "median_shape_distance_km": 0.10
}

available_weights = {}

for feature, weight in feature_weights.items():

    if feature in numeric_df.columns:

        percentile = numeric_df[feature].rank(
            pct=True
        )

        score += percentile * weight

        available_weights[feature] = weight

if not available_weights:
    raise ValueError(
        "No proxy scoring features found."
    )

score = score / sum(
    abs(w) for w in available_weights.values()
)

df["operational_proxy_score"] = score

low_threshold = score.quantile(0.33)
high_threshold = score.quantile(0.67)

df["operational_proxy_label"] = np.where(
    score <= low_threshold,
    "Low",
    np.where(
        score <= high_threshold,
        "Medium",
        "High"
    )
)

label_encoder = LabelEncoder()

y = label_encoder.fit_transform(
    df["operational_proxy_label"]
)

print("Proxy label distribution:")
print(
    df["operational_proxy_label"].value_counts()
)


# ------------------------------------------------
# 5. STANDARDIZATION
# ------------------------------------------------

print("\n[4/9] Standardizing features...")

scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    numeric_df
)

X = pd.DataFrame(
    X_scaled,
    columns=numeric_df.columns
)

joblib.dump(
    scaler,
    "models/route_feature_scaler.joblib"
)

joblib.dump(
    list(numeric_df.columns),
    "models/route_feature_columns.joblib"
)


# ------------------------------------------------
# 6. K-MEANS CLUSTERING
# ------------------------------------------------

print("\n[5/9] Running K-Means clustering...")

kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

kmeans_labels = kmeans.fit_predict(X)

df["kmeans_cluster"] = kmeans_labels

kmeans_silhouette = silhouette_score(
    X,
    kmeans_labels
)

print(
    "K-Means Silhouette Score:",
    round(kmeans_silhouette, 4)
)

joblib.dump(
    kmeans,
    "models/kmeans_route_model.joblib"
)

df.to_csv(
    "reports/kmeans_route_clusters.csv",
    index=False
)


# ------------------------------------------------
# 7. DBSCAN CLUSTERING
# ------------------------------------------------

print("\n[6/9] Running DBSCAN clustering...")

dbscan = DBSCAN(
    eps=1.5,
    min_samples=5
)

dbscan_labels = dbscan.fit_predict(X)

df["dbscan_cluster"] = dbscan_labels

non_noise = dbscan_labels != -1

unique_clusters = np.unique(
    dbscan_labels[non_noise]
)

dbscan_silhouette = np.nan

if (
    non_noise.sum() > 1
    and len(unique_clusters) > 1
):

    dbscan_silhouette = silhouette_score(
        X[non_noise],
        dbscan_labels[non_noise]
    )

print(
    "DBSCAN clusters:",
    len(unique_clusters)
)

print(
    "DBSCAN noise routes:",
    int((dbscan_labels == -1).sum())
)

print(
    "DBSCAN Silhouette:",
    dbscan_silhouette
)

joblib.dump(
    dbscan,
    "models/dbscan_route_model.joblib"
)

df.to_csv(
    "reports/dbscan_route_clusters.csv",
    index=False
)


# ------------------------------------------------
# 8. TRAIN RANDOM FOREST AND XGBOOST
# ------------------------------------------------

print("\n[7/9] Training classification models...")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

models = {

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    ),

    "XGBoost": XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.05,
        objective="multi:softprob",
        num_class=3,
        eval_metric="mlogloss",
        random_state=42,
        n_jobs=1,
        use_label_encoder=False
    )
}

metrics = []

trained_models = {}

for name, model in models.items():

    print("\nTraining:", name)

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(
        X_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        average="weighted",
        zero_division=0
    )

    metrics.append({
        "Model": name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1
    })

    trained_models[name] = model

    print("Accuracy:", round(accuracy, 4))
    print("Precision:", round(precision, 4))
    print("Recall:", round(recall, 4))
    print("F1 Score:", round(f1, 4))


# ------------------------------------------------
# 9. MODEL SELECTION
# ------------------------------------------------

metrics_df = pd.DataFrame(metrics)

metrics_df = metrics_df.sort_values(
    "F1_Score",
    ascending=False
)

metrics_df.to_csv(
    "reports/milestone3_model_metrics.csv",
    index=False
)

best_model_name = metrics_df.iloc[0]["Model"]

best_model = trained_models[
    best_model_name
]

print("\nBest model:", best_model_name)

joblib.dump(
    trained_models["Random Forest"],
    "models/random_forest_route_model.joblib"
)

joblib.dump(
    trained_models["XGBoost"],
    "models/xgboost_route_model.joblib"
)


# ------------------------------------------------
# 10. ROUTE INFERENCE
# ------------------------------------------------

print("\n[8/9] Generating route predictions...")

predicted_classes = best_model.predict(
    X
)

predicted_labels = label_encoder.inverse_transform(
    predicted_classes
)

df["predicted_operational_category"] = (
    predicted_labels
)

df["predicted_operational_category"] = (
    df["predicted_operational_category"]
)


# ------------------------------------------------
# 11. OPTIMIZATION RECOMMENDATIONS
# ------------------------------------------------

def recommendation(category):

    if category == "Low":

        return (
            "Review service demand, route utilization "
            "and possible frequency reduction."
        )

    elif category == "Medium":

        return (
            "Monitor route performance and evaluate "
            "schedule adjustments."
        )

    else:

        return (
            "Review service frequency, capacity "
            "and possible additional trips."
        )


df["optimization_recommendation"] = (
    df["predicted_operational_category"]
    .apply(recommendation)
)

df.to_csv(
    "reports/milestone3_route_predictions.csv",
    index=False
)

df.to_csv(
    "reports/milestone3_optimization_recommendations.csv",
    index=False
)


# ------------------------------------------------
# 12. SUMMARY
# ------------------------------------------------

summary = pd.DataFrame({

    "Metric": [
        "Total Routes",
        "Total Cities",
        "Feature Count",
        "KMeans Silhouette",
        "DBSCAN Clusters",
        "DBSCAN Noise Routes",
        "DBSCAN Silhouette",
        "Best Model"
    ],

    "Value": [
        len(df),
        df["city"].nunique(),
        X.shape[1],
        kmeans_silhouette,
        len(unique_clusters),
        int((dbscan_labels == -1).sum()),
        dbscan_silhouette,
        best_model_name
    ]

})

summary.to_csv(
    "reports/milestone3_summary.csv",
    index=False
)

print("\n[9/9] Milestone 3 pipeline completed!")

print("\nMODEL METRICS")
print(metrics_df.to_string(index=False))

print("\nSUMMARY")
print(summary.to_string(index=False))

print("\nGenerated reports:")
print("reports/kmeans_route_clusters.csv")
print("reports/dbscan_route_clusters.csv")
print("reports/milestone3_model_metrics.csv")
print("reports/milestone3_route_predictions.csv")
print("reports/milestone3_optimization_recommendations.csv")
print("reports/milestone3_summary.csv")

print("\nGenerated models:")
print("models/kmeans_route_model.joblib")
print("models/dbscan_route_model.joblib")
print("models/random_forest_route_model.joblib")
print("models/xgboost_route_model.joblib")
print("models/route_feature_scaler.joblib")
print("models/route_feature_columns.joblib")

print("\n" + "=" * 70)
print("END OF MILESTONE 3")
print("=" * 70)
