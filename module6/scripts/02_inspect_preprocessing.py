
from pathlib import Path
import joblib

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data" / "processed"

print("=" * 60)
print("MODULE 6 - PREPROCESSING INSPECTION")
print("=" * 60)

# Inspect preprocessing dictionary
objects_path = DATA_DIR / "preprocessing_objects.pkl"
objects = joblib.load(objects_path)

print("\nPREPROCESSING OBJECTS")
print("Object type:", type(objects).__name__)

if isinstance(objects, dict):
    for name, obj in objects.items():
        print("\nKey:", name)
        print("Type:", type(obj).__name__)

        if hasattr(obj, "classes_"):
            print("Classes:", obj.classes_)

        if hasattr(obj, "get_feature_names_out"):
            try:
                print("Output features:", obj.get_feature_names_out())
            except Exception as error:
                print("Feature inspection:", error)

# Inspect Module 4 pipeline
pipeline_path = DATA_DIR / "module4_preprocessing_pipeline.pkl"
pipeline = joblib.load(pipeline_path)

print("\n" + "=" * 60)
print("MODULE 4 PREPROCESSING PIPELINE")
print("=" * 60)

print("Pipeline type:", type(pipeline).__name__)
print("Input features:", list(pipeline.feature_names_in_))

try:
    print("Output features:")
    print(list(pipeline.get_feature_names_out()))
except Exception as error:
    print("Could not retrieve output features:", error)

print("\n" + "=" * 60)
print("INSPECTION COMPLETED")
print("=" * 60)
