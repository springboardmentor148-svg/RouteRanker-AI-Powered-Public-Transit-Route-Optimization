
from pathlib import Path
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
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

# Experiment with K values
results = []

for k in [2, 3, 4, 5]:
    model = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = model.fit_predict(X)

    silhouette = silhouette_score(
        X, labels, sample_size=2000, random_state=42
    )
    db_index = davies_bouldin_score(X, labels)

    results.append({
        "K": k,
        "Inertia": model.inertia_,
        "Silhouette_Score": silhouette,
        "Davies_Bouldin_Index": db_index
    })

    joblib.dump(model, MODEL_DIR / f"kmeans_model_k{k}.pkl")

results_df = pd.DataFrame(results)
results_df.to_csv(DATA_DIR / "kmeans_evaluation_results.csv", index=False)

# Train final K-Means model with K=4
final_model = KMeans(n_clusters=4, random_state=42, n_init=10)
final_labels = final_model.fit_predict(X)

joblib.dump(final_model, MODEL_DIR / "kmeans_final_model.pkl")

# Save route cluster assignments
output = route_info[
    ["route_id", "route_short_name", "city"]
].copy()

output["Cluster"] = final_labels
output.to_csv(DATA_DIR / "kmeans_route_clusters.csv", index=False)

# Elbow visualization
plt.figure(figsize=(8, 5))
plt.plot(results_df["K"], results_df["Inertia"], marker="o")
plt.xlabel("Number of Clusters (K)")
plt.ylabel("Inertia")
plt.title("K-Means Elbow Method")
plt.xticks([2, 3, 4, 5])
plt.grid(True)
plt.savefig(VIS_DIR / "elbow_method.png", dpi=300)
plt.close()

# PCA visualization
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

plt.figure(figsize=(8, 6))
plt.scatter(
    X_pca[:, 0], X_pca[:, 1],
    c=final_labels, cmap="viridis", s=10
)
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("K-Means Route Clusters (K=4)")
plt.savefig(VIS_DIR / "kmeans_cluster_visualization.png", dpi=300)
plt.close()

print("K-Means implementation completed.")
print(results_df)
print("\nCluster distribution:")
print(output["Cluster"].value_counts().sort_index())
