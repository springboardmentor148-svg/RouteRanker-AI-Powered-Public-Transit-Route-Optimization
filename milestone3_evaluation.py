
# ================================================================
# ROUTERANKER - MILESTONE 3 EVALUATION
# Visualizations, Feature Importance and Final Report
# ================================================================

import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

REPORT_DIR = "reports"
VISUAL_DIR = "visuals"
MODEL_DIR = "models"

os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(VISUAL_DIR, exist_ok=True)

print("=" * 70)
print("ROUTERANKER - MILESTONE 3 EVALUATION")
print("=" * 70)


# ------------------------------------------------
# 1. LOAD RESULTS
# ------------------------------------------------

predictions = pd.read_csv(
    "reports/milestone3_route_predictions.csv"
)

metrics = pd.read_csv(
    "reports/milestone3_model_metrics.csv"
)

kmeans = pd.read_csv(
    "reports/kmeans_route_clusters.csv"
)

dbscan = pd.read_csv(
    "reports/dbscan_route_clusters.csv"
)

xgb = joblib.load(
    "models/xgboost_route_model.joblib"
)

feature_columns = joblib.load(
    "models/route_feature_columns.joblib"
)

print("\nRoutes:", len(predictions))
print("Cities:", predictions["city"].nunique())
print("Features:", len(feature_columns))


# ------------------------------------------------
# 2. MODEL COMPARISON CHART
# ------------------------------------------------

print("\n[1/6] Creating model comparison chart...")

plt.figure(figsize=(9, 6))

metrics.set_index("Model")[
    ["Accuracy", "Precision", "Recall", "F1_Score"]
].plot(kind="bar", figsize=(10, 6))

plt.title("RouteRanker - Classification Model Comparison")
plt.ylabel("Score")
plt.xlabel("Model")
plt.ylim(0, 1.05)
plt.xticks(rotation=0)
plt.legend(loc="lower right")
plt.tight_layout()

plt.savefig(
    "visuals/milestone3_model_comparison.png",
    dpi=300
)

plt.close()


# ------------------------------------------------
# 3. K-MEANS CLUSTER DISTRIBUTION
# ------------------------------------------------

print("\n[2/6] Creating K-Means chart...")

counts = kmeans["kmeans_cluster"].value_counts().sort_index()

plt.figure(figsize=(8, 5))

counts.plot(kind="bar")

plt.title("K-Means Route Cluster Distribution")
plt.xlabel("Cluster")
plt.ylabel("Number of Routes")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    "visuals/milestone3_kmeans_clusters.png",
    dpi=300
)

plt.close()


# ------------------------------------------------
# 4. DBSCAN CLUSTER DISTRIBUTION
# ------------------------------------------------

print("\n[3/6] Creating DBSCAN chart...")

counts = dbscan["dbscan_cluster"].value_counts().sort_index()

plt.figure(figsize=(10, 5))

counts.plot(kind="bar")

plt.title("DBSCAN Route Cluster Distribution")
plt.xlabel("Cluster (-1 = Noise)")
plt.ylabel("Number of Routes")
plt.xticks(rotation=0)
plt.tight_layout()

plt.savefig(
    "visuals/milestone3_dbscan_clusters.png",
    dpi=300
)

plt.close()


# ------------------------------------------------
# 5. XGBOOST FEATURE IMPORTANCE
# ------------------------------------------------

print("\n[4/6] Creating feature importance chart...")

importance = pd.DataFrame({
    "Feature": feature_columns,
    "Importance": xgb.feature_importances_
})

importance = importance.sort_values(
    "Importance",
    ascending=False
)

importance.to_csv(
    "reports/milestone3_feature_importance.csv",
    index=False
)

top_features = importance.head(15).sort_values(
    "Importance",
    ascending=True
)

plt.figure(figsize=(10, 7))

plt.barh(
    top_features["Feature"],
    top_features["Importance"]
)

plt.title("XGBoost - Top 15 Feature Importance")
plt.xlabel("Importance")
plt.ylabel("Feature")
plt.tight_layout()

plt.savefig(
    "visuals/milestone3_feature_importance.png",
    dpi=300
)

plt.close()


# ------------------------------------------------
# 6. CITY CATEGORY ANALYSIS
# ------------------------------------------------

print("\n[5/6] Creating city analysis...")

city_analysis = pd.crosstab(
    predictions["city"],
    predictions["predicted_operational_category"]
)

city_analysis.to_csv(
    "reports/milestone3_city_category_analysis.csv"
)

city_analysis.plot(
    kind="bar",
    stacked=True,
    figsize=(12, 7)
)

plt.title("Predicted Operational Categories by City")
plt.xlabel("City")
plt.ylabel("Number of Routes")
plt.xticks(rotation=45)
plt.legend(title="Category")
plt.tight_layout()

plt.savefig(
    "visuals/milestone3_city_categories.png",
    dpi=300
)

plt.close()


# ------------------------------------------------
# 7. FINAL REPORT
# ------------------------------------------------

print("\n[6/6] Writing final report...")

best_model = metrics.sort_values(
    "F1_Score",
    ascending=False
).iloc[0]

report = []

report.append("# ROUTERANKER - MILESTONE 3 FINAL REPORT\n")

report.append(
    "## Model Selection, Training and Inference\n"
)

report.append("## 1. Dataset\n")

report.append(
    "- Total routes analyzed: 10,514\n"
    "- Cities analyzed: 8\n"
    "- Numeric features: 16\n"
    "- Dataset: combined_route_features.csv\n"
)

report.append(
    "## 2. Clustering Results\n"
)

report.append(
    "- K-Means: 3 clusters\n"
    "- K-Means silhouette score: 0.6725\n"
    "- DBSCAN: 9 identified clusters\n"
    "- DBSCAN noise routes: 167\n"
    "- DBSCAN silhouette score: 0.7196\n"
)

report.append(
    "## 3. Classification Results\n"
)

# FIXED: Compatible with pandas 1.1.5
report.append(
    metrics.to_string(index=False)
)

report.append(
    "\nBest classification model: "
    + str(best_model["Model"])
    + "\n"
)

report.append(
    "Best model F1 score: "
    + str(round(best_model["F1_Score"], 4))
    + "\n"
)

report.append(
    "## 4. Feature Importance\n"
)

# FIXED: Compatible with pandas 1.1.5
report.append(
    importance.head(10).to_string(index=False)
)

report.append(
    "\n## 5. Route Inference and Recommendations\n"
)

report.append(
    "- Generated predicted operational categories for all routes.\n"
    "- Generated rule-based optimization recommendations.\n"
    "- Produced city-level category analysis.\n"
)

report.append(
    "\n## 6. Important Methodological Limitation\n"
)

report.append(
    "The operational categories are proxy labels constructed "
    "from route features. They are not observed passenger "
    "demand, occupancy, actual congestion, or measured "
    "service efficiency labels. Classification scores "
    "therefore measure agreement with these engineered "
    "categories and should not be interpreted as real-world "
    "prediction accuracy.\n"
)

report.append(
    "\nClustering scores indicate separation under the "
    "chosen feature representation and parameters. "
    "They do not independently prove transport "
    "optimization effectiveness.\n"
)

report.append(
    "\n## 7. Generated Visualizations\n"
)

report.append(
    "- visuals/milestone3_model_comparison.png\n"
    "- visuals/milestone3_kmeans_clusters.png\n"
    "- visuals/milestone3_dbscan_clusters.png\n"
    "- visuals/milestone3_feature_importance.png\n"
    "- visuals/milestone3_city_categories.png\n"
)

report.append(
    "\n## 8. Conclusion\n"
)

report.append(
    "Milestone 3 implemented clustering, classification, "
    "model evaluation, route inference, and initial "
    "optimization recommendation generation. "
    "The current implementation is a prototype based "
    "on operational proxy labels. Future validation "
    "should incorporate actual ridership, service "
    "performance, passenger capacity, and route-level "
    "operational outcomes.\n"
)

with open(
    "reports/MILESTONE3_FINAL_REPORT.md",
    "w",
    encoding="utf-8"
) as f:

    f.write("\n".join(report))


# ------------------------------------------------
# 8. COMPLETION
# ------------------------------------------------

print("\n" + "=" * 70)
print("MILESTONE 3 EVALUATION COMPLETED")
print("=" * 70)

print("\nGenerated report:")
print("reports/MILESTONE3_FINAL_REPORT.md")

print("\nGenerated charts:")
print("visuals/milestone3_model_comparison.png")
print("visuals/milestone3_kmeans_clusters.png")
print("visuals/milestone3_dbscan_clusters.png")
print("visuals/milestone3_feature_importance.png")
print("visuals/milestone3_city_categories.png")

print("\nGenerated analysis:")
print("reports/milestone3_feature_importance.csv")
print("reports/milestone3_city_category_analysis.csv")

print("\n" + "=" * 70)
print("END OF MILESTONE 3 EVALUATION")
print("=" * 70)
