
from pathlib import Path
import joblib
import sklearn
import pandas
import numpy
import xgboost

PROJECT_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = PROJECT_DIR / "models"
DATA_DIR = PROJECT_DIR / "data" / "processed"

artifacts = {
    "K-Means": MODEL_DIR / "kmeans_final_model.pkl",
    "DBSCAN": MODEL_DIR / "dbscan_final_model.pkl",
    "Random Forest": MODEL_DIR / "random_forest_classifier_module4.pkl",
    "XGBoost": MODEL_DIR / "xgboost_classifier_module4.pkl",
    "Module 4 preprocessing": DATA_DIR / "module4_preprocessing_pipeline.pkl",
    "Preprocessing objects": DATA_DIR / "preprocessing_objects.pkl",
    "Route preprocessing": DATA_DIR / "route_preprocessing_pipeline.pkl",
}

print("=" * 60)
print("ROUTERANKER MODULE 6 - MODEL LOADING VERIFICATION")
print("=" * 60)

print("\nLibrary versions:")
print("NumPy:", numpy.__version__)
print("Pandas:", pandas.__version__)
print("Scikit-learn:", sklearn.__version__)
print("XGBoost:", xgboost.__version__)

for name, path in artifacts.items():
    print("\n" + "-" * 60)
    print(name)
    print("File:", path.name)

    if not path.exists():
        print("STATUS: FILE NOT FOUND")
        continue

    try:
        model = joblib.load(path)

        print("STATUS: LOADED SUCCESSFULLY")
        print("Object type:", type(model).__name__)

        if hasattr(model, "n_features_in_"):
            print("Number of input features:", model.n_features_in_)

        if hasattr(model, "feature_names_in_"):
            print("Feature names:", list(model.feature_names_in_))

        if hasattr(model, "n_clusters"):
            print("Number of clusters:", model.n_clusters)

        if hasattr(model, "cluster_centers_"):
            print("Cluster centers shape:", model.cluster_centers_.shape)

        if hasattr(model, "eps"):
            print("DBSCAN eps:", model.eps)

        if hasattr(model, "min_samples"):
            print("DBSCAN min_samples:", model.min_samples)

        if hasattr(model, "core_sample_indices_"):
            print("DBSCAN core samples:", len(model.core_sample_indices_))

        if hasattr(model, "classes_"):
            print("Classification classes:", model.classes_)

    except Exception as error:
        print("STATUS: LOADING FAILED")
        print("Error:", repr(error))

print("\n" + "=" * 60)
print("MODEL VERIFICATION FINISHED")
print("=" * 60)
