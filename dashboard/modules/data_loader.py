from pathlib import Path
import pandas as pd

# Identify the main RouteRanker project directory
PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "processed"

# Existing datasets used by the dashboard
DATA_FILES = {
    "main": "module4_processed_dataset.csv",
    "clustering_features": "module5_clustering_features.csv",
    "kmeans": "kmeans_route_clusters.csv",
    "dbscan": "dbscan_cluster_labels.csv",
    "kmeans_inference": "module6_kmeans_inference.csv",
    "classification": "module6_classification_inference.csv",
    "route_analysis": "module6_route_analysis.csv",
    "simulation": "module6_hypothetical_schedule_scenario.csv",
    "comparison": "module6_simulation_comparison.csv",
}


def load_csv(dataset_name):
    """Load one existing processed dataset by its registered name."""

    if dataset_name not in DATA_FILES:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. "
            f"Available datasets: {list(DATA_FILES.keys())}"
        )

    file_path = DATA_DIR / DATA_FILES[dataset_name]

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    return pd.read_csv(file_path)


def load_all_data():
    """Load all registered datasets for the dashboard."""

    datasets = {}

    for dataset_name in DATA_FILES:
        datasets[dataset_name] = load_csv(dataset_name)

    return datasets


def get_dataset_summary(datasets):
    """Return basic information about the loaded datasets."""

    summary = []

    for name, dataframe in datasets.items():
        summary.append({
            "Dataset": name,
            "Rows": len(dataframe),
            "Columns": len(dataframe.columns),
            "Missing Values": int(dataframe.isna().sum().sum())
        })

    return pd.DataFrame(summary)
