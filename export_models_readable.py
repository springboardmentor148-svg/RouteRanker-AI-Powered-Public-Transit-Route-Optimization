"""Export every NumPy model archive into CSV arrays and JSON metadata.

Run from the project root with:
    python export_models_readable.py

The original .npz model files are kept for use by the Python training code.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = MODELS_DIR / "readable"


def write_csv(path: Path, headers: list[str], rows: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows.tolist())


def export_model(archive_path: Path) -> None:
    metadata_path = archive_path.with_suffix(".json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
    features = metadata.get("features", [])
    destination = OUTPUT_DIR / archive_path.stem
    destination.mkdir(parents=True, exist_ok=True)
    exported_arrays: list[dict[str, object]] = []

    with np.load(archive_path, allow_pickle=False) as archive:
        for array_name in archive.files:
            array = np.asarray(archive[array_name])
            csv_path = destination / f"{array_name}.csv"

            if array.ndim == 2:
                if array.shape[1] == len(features):
                    feature_headers = list(features)
                else:
                    feature_headers = [f"value_{index}" for index in range(array.shape[1])]

                if array_name == "centroids":
                    headers = ["cluster_id", *feature_headers]
                    rows = np.column_stack((np.arange(array.shape[0]), array))
                elif array_name == "core_samples":
                    headers = ["core_sample_index", *feature_headers]
                    rows = np.column_stack((np.arange(array.shape[0]), array))
                else:
                    headers = feature_headers
                    rows = array
            elif array.ndim == 1 and array_name == "core_labels":
                headers = ["core_sample_index", "cluster_label"]
                rows = np.column_stack((np.arange(array.shape[0]), array))
            elif array.ndim == 1:
                headers = [array_name]
                rows = array.reshape(-1, 1)
            else:
                raise ValueError(f"Unsupported array dimensions in {archive_path.name}: {array_name} {array.shape}")

            write_csv(csv_path, headers, rows)
            exported_arrays.append(
                {
                    "name": array_name,
                    "shape": list(array.shape),
                    "dtype": str(array.dtype),
                    "csv": csv_path.name,
                }
            )

    readable_metadata = {
        **metadata,
        "source_archive": archive_path.name,
        "array_values": "Model input space values from the processed dataset (robust-scaled where applicable).",
        "exports": exported_arrays,
    }
    (destination / "metadata.json").write_text(
        json.dumps(readable_metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    archives = sorted(MODELS_DIR.glob("*.npz"))
    if not archives:
        raise FileNotFoundError(f"No .npz files found in {MODELS_DIR}")
    for archive_path in archives:
        export_model(archive_path)
        print(f"Exported {archive_path.name} to models/readable/{archive_path.stem}/")
    print(f"Converted {len(archives)} model archives.")


if __name__ == "__main__":
    main()
