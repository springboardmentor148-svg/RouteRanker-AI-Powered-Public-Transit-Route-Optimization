
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, davies_bouldin_score

PROJECT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_DIR / "data" / "processed"
MODEL_DIR = PROJECT_DIR / "models"
VIS_DIR = PROJECT_DIR / "visualizations"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
VIS_DIR.mkdir(parents=True, exist_ok=True)

# Load datasets
X = pd.read_csv(DATA_DIR / "module5_clustering_features.csv")
route_info = pd.read_csv(DATA_DIR / "module4_processed_dataset.csv")

if len(X) != len(route_info):
    raise ValueError("Dataset row counts do not match.")

# Experiment with DBSCAN parameters
experiment_results = []

for eps in [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]:
    for min_samples in [5, 10, 15]:

        model = DBSCAN(
            eps=eps,
            min_samples=min_samples
        )

        labels = model.fit_predict(X)

        cluster_count = len(set(labels)) - (1 if -1 in labels else 0)
        noise_count = int(np.sum(labels == -1))

        experiment_results.append({
            "eps": eps,
            "min_samples": min_samples,
            "clusters": cluster_count,
            "noise_points": noise_count
        })

results_df = pd.DataFrame(experiment_results)

results_df.to_csv(
    DATA_DIR / "dbscan_parameter_results.csv",
    index=False
)

# Train final DBSCAN model
dbscan = DBSCAN(eps=0.3, min_samples=10)
labels = dbscan.fit_predict(X)

joblib.dump(
    dbscan,
    MODEL_DIR / "dbscan_final_model.pkl"
)

# Identify core, border and noise points
core_mask = np.zeros(len(X), dtype=bool)
core_mask[dbscan.core_sample_indices_] = True

noise_mask = labels == -1
border_mask = (~core_mask) & (~noise_mask)

# Save cluster labels
output = route_info[
    ["route_id", "route_short_name", "city"]
].copy()

output["Cluster"] = labels

output.to_csv(
    DATA_DIR / "dbscan_cluster_labels.csv",
    index=False
)

# Save point types
point_types = output.copy()

point_types["Point_Type"] = np.select(
    [core_mask, border_mask, noise_mask],
    ["Core", "Border", "Noise"],
    default="Unknown"
)

point_types.to_csv(
    DATA_DIR / "dbscan_point_types.csv",
    index=False
)

# Save noise routes
noise_routes = point_types[
    point_types["Point_Type"] == "Noise"
]

noise_routes.to_csv(
    DATA_DIR / "dbscan_noise_routes.csv",
    index=False
)

# Evaluate DBSCAN after excluding noise points
non_noise_mask = labels != -1
non_noise_labels = labels[non_noise_mask]
non_noise_X = X.loc[non_noise_mask]

if len(np.unique(non_noise_labels)) >= 2:
    silhouette = silhouette_score(
        non_noise_X, non_noise_labels
    )

    db_index = davies_bouldin_score(
        non_noise_X, non_noise_labels
    )
else:
    silhouette = np.nan
    db_index = np.nan

# PCA visualization
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

plt.figure(figsize=(8, 6))
plt.scatter(
    X_pca[:, 0],
    X_pca[:, 1],
    c=labels,
    cmap="viridis",
    s=10
)
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("DBSCAN Route Clusters")
plt.savefig(
    VIS_DIR / "dbscan_cluster_visualization.png",
    dpi=300
)
plt.close()

# Print results
print("DBSCAN implementation completed.")
print("\nParameter Experiment Results:")
print(results_df.to_string(index=False))

print("\nFinal DBSCAN Evaluation")
print("Clusters:", len(set(labels)) - (1 if -1 in labels else 0))
print("Silhouette Score:", silhouette)
print("Davies-Bouldin Index:", db_index)
print("Core Points:", int(core_mask.sum()))
print("Border Points:", int(border_mask.sum()))
print("Noise Points:", int(noise_mask.sum()))
print("Total Points:", len(X))

print("\nDBSCAN files saved successfully.")
