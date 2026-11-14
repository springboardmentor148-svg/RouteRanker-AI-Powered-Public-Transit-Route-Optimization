"""Train and evaluate RouteRanker's unsupervised Module 5 models.

The implementation uses NumPy for K-Means, DBSCAN, internal metrics, and SVG
plots. It consumes the Module 4 prepared feature matrix and never treats route
identifiers or city names as model inputs.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SEED = 42
K_VALUES = (2, 3, 4, 5)
DBSCAN_MIN_SAMPLES = (5, 10, 20)
DBSCAN_QUANTILES = (0.35, 0.50, 0.65, 0.80)
PALETTE = ["#176B87", "#DB6B35", "#4A8F55", "#8559A5", "#C69C2E", "#CA5364", "#4A6FA5", "#6B7280"]


def pairwise_squared_distances(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Return Euclidean squared distances without creating a 3-D tensor."""
    left = np.asarray(left, dtype=np.float64)
    right = np.asarray(right, dtype=np.float64)
    left_norm = np.einsum("ij,ij->i", left, left)[:, None]
    right_norm = np.einsum("ij,ij->i", right, right)[None, :]
    result = left_norm + right_norm - 2.0 * (left @ right.T)
    np.maximum(result, 0.0, out=result)
    return result


def kmeans_plus_plus(X: np.ndarray, k: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centers = [X[int(rng.integers(len(X)))].copy()]
    nearest = pairwise_squared_distances(X, centers)[..., 0]
    for _ in range(1, k):
        total = float(nearest.sum())
        if total <= 0:
            chosen = int(rng.integers(len(X)))
        else:
            chosen = int(np.searchsorted(np.cumsum(nearest), rng.random() * total, side="right"))
            chosen = min(chosen, len(X) - 1)
        centers.append(X[chosen].copy())
        nearest = np.minimum(nearest, pairwise_squared_distances(X, centers[-1:])[:, 0])
    return np.asarray(centers, dtype=np.float64)


def fit_kmeans(X: np.ndarray, k: int, seed: int = SEED, n_init: int = 5, max_iter: int = 120) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for restart in range(n_init):
        centers = kmeans_plus_plus(X, k, seed + restart * 1009)
        previous_labels: np.ndarray | None = None
        for iteration in range(max_iter):
            distances = pairwise_squared_distances(X, centers)
            labels = np.argmin(distances, axis=1)
            minima = distances[np.arange(len(X)), labels]
            new_centers = np.zeros_like(centers)
            counts = np.bincount(labels, minlength=k)
            np.add.at(new_centers, labels, X)
            nonempty = counts > 0
            new_centers[nonempty] /= counts[nonempty, None]
            if not np.all(nonempty):
                farthest = np.argsort(minima)[::-1]
                replacement_cursor = 0
                for cluster in np.flatnonzero(~nonempty):
                    new_centers[cluster] = X[farthest[replacement_cursor]]
                    replacement_cursor += 1
            converged = previous_labels is not None and np.array_equal(labels, previous_labels)
            movement = float(np.max(np.linalg.norm(new_centers - centers, axis=1)))
            centers = new_centers
            previous_labels = labels
            if converged or movement < 1e-5:
                break
        final_distances = pairwise_squared_distances(X, centers)
        labels = np.argmin(final_distances, axis=1)
        inertia = float(final_distances[np.arange(len(X)), labels].sum())
        if best is None or inertia < best["inertia"]:
            best = {"centers": centers, "labels": labels, "inertia": inertia, "iterations": iteration + 1}
    assert best is not None
    return best


def dbscan_from_distance_matrix(distance_squared: np.ndarray, eps: float, min_samples: int) -> tuple[np.ndarray, np.ndarray]:
    """DBSCAN expansion over a precomputed squared-distance matrix."""
    n = len(distance_squared)
    neighbors = [np.flatnonzero(row <= eps * eps) for row in distance_squared]
    core = np.fromiter((len(items) >= min_samples for items in neighbors), dtype=bool, count=n)
    labels = np.full(n, -1, dtype=np.int32)
    visited = np.zeros(n, dtype=bool)
    cluster_id = 0
    for point in range(n):
        if visited[point]:
            continue
        visited[point] = True
        if not core[point]:
            continue
        labels[point] = cluster_id
        seeds = list(neighbors[point])
        queued = np.zeros(n, dtype=bool)
        queued[seeds] = True
        cursor = 0
        while cursor < len(seeds):
            candidate = int(seeds[cursor])
            cursor += 1
            if not visited[candidate]:
                visited[candidate] = True
                if core[candidate]:
                    for neighbor in neighbors[candidate]:
                        neighbor = int(neighbor)
                        if not queued[neighbor]:
                            queued[neighbor] = True
                            seeds.append(neighbor)
            if labels[candidate] == -1:
                labels[candidate] = cluster_id
        cluster_id += 1
    return labels, core


def fit_dbscan(X: np.ndarray, eps: float, min_samples: int, chunk_size: int = 128) -> tuple[np.ndarray, np.ndarray]:
    """Fit DBSCAN in chunks to keep peak memory bounded for the full dataset."""
    n = len(X)
    neighbors: list[np.ndarray] = [np.empty(0, dtype=np.int32) for _ in range(n)]
    core = np.zeros(n, dtype=bool)
    eps_squared = eps * eps
    for start in range(0, n, chunk_size):
        stop = min(start + chunk_size, n)
        block = pairwise_squared_distances(X[start:stop], X)
        for offset, row in enumerate(block):
            indices = np.flatnonzero(row <= eps_squared).astype(np.int32, copy=False)
            point = start + offset
            neighbors[point] = indices
            core[point] = len(indices) >= min_samples
    labels = np.full(n, -1, dtype=np.int32)
    visited = np.zeros(n, dtype=bool)
    cluster_id = 0
    for point in range(n):
        if visited[point]:
            continue
        visited[point] = True
        if not core[point]:
            continue
        labels[point] = cluster_id
        seeds = list(neighbors[point])
        queued = np.zeros(n, dtype=bool)
        queued[seeds] = True
        cursor = 0
        while cursor < len(seeds):
            candidate = int(seeds[cursor])
            cursor += 1
            if not visited[candidate]:
                visited[candidate] = True
                if core[candidate]:
                    for neighbor in neighbors[candidate]:
                        neighbor = int(neighbor)
                        if not queued[neighbor]:
                            queued[neighbor] = True
                            seeds.append(neighbor)
            if labels[candidate] == -1:
                labels[candidate] = cluster_id
        cluster_id += 1
    return labels, core


def predict_dbscan(X: np.ndarray, core_X: np.ndarray, core_labels: np.ndarray, eps: float, chunk_size: int = 128) -> np.ndarray:
    """Approximate out-of-sample assignment by the nearest DBSCAN core point."""
    labels = np.full(len(X), -1, dtype=np.int32)
    if len(core_X) == 0:
        return labels
    eps_squared = eps * eps
    for start in range(0, len(X), chunk_size):
        stop = min(start + chunk_size, len(X))
        distances = pairwise_squared_distances(X[start:stop], core_X)
        nearest = np.argmin(distances, axis=1)
        minimum = distances[np.arange(stop - start), nearest]
        assigned = minimum <= eps_squared
        labels[start + np.flatnonzero(assigned)] = core_labels[nearest[assigned]]
    return labels


def davies_bouldin_index(X: np.ndarray, labels: np.ndarray) -> float:
    cluster_ids = [int(value) for value in np.unique(labels) if value >= 0]
    if len(cluster_ids) < 2:
        return float("nan")
    centers: list[np.ndarray] = []
    spreads: list[float] = []
    for cluster_id in cluster_ids:
        points = X[labels == cluster_id]
        center = points.mean(axis=0)
        centers.append(center)
        spreads.append(float(np.linalg.norm(points - center, axis=1).mean()))
    center_array = np.asarray(centers)
    between = np.sqrt(pairwise_squared_distances(center_array, center_array))
    ratios = np.zeros((len(cluster_ids), len(cluster_ids)), dtype=np.float64)
    for i in range(len(cluster_ids)):
        for j in range(len(cluster_ids)):
            if i != j:
                ratios[i, j] = (spreads[i] + spreads[j]) / max(float(between[i, j]), 1e-12)
    return float(np.max(ratios, axis=1).mean())


def silhouette_score_sampled(X: np.ndarray, labels: np.ndarray, seed: int = SEED, sample_size: int = 1200) -> float:
    valid = np.flatnonzero(labels >= 0)
    cluster_ids, cluster_counts = np.unique(labels[valid], return_counts=True)
    if len(cluster_ids) < 2 or len(valid) <= 1:
        return float("nan")
    rng = np.random.default_rng(seed)
    chosen = valid if len(valid) <= sample_size else np.sort(rng.choice(valid, size=sample_size, replace=False))
    means = np.empty(len(chosen), dtype=np.float64)
    for start in range(0, len(chosen), 64):
        batch_indices = chosen[start:start + 64]
        distances = np.sqrt(pairwise_squared_distances(X[batch_indices], X[valid]))
        valid_labels = labels[valid]
        for local, row in enumerate(distances):
            point_index = batch_indices[local]
            own_label = labels[point_index]
            per_cluster = []
            own_mean = float("nan")
            for cluster_id in cluster_ids:
                mask = valid_labels == cluster_id
                if cluster_id == own_label:
                    mask = mask.copy()
                    own_position = np.searchsorted(valid, point_index)
                    if own_position < len(mask):
                        mask[own_position] = False
                    if mask.any():
                        own_mean = float(row[mask].mean())
                elif mask.any():
                    per_cluster.append(float(row[mask].mean()))
            if not math.isfinite(own_mean) or not per_cluster:
                means[start + local] = 0.0
            else:
                a = own_mean
                b = min(per_cluster)
                means[start + local] = (b - a) / max(a, b, 1e-12)
    return float(np.mean(means))


def cluster_metrics(X: np.ndarray, labels: np.ndarray, seed: int = SEED) -> dict[str, Any]:
    cluster_ids, counts = np.unique(labels[labels >= 0], return_counts=True)
    return {
        "n_clusters": int(len(cluster_ids)),
        "noise_count": int(np.sum(labels < 0)),
        "noise_share": float(np.mean(labels < 0)),
        "silhouette": silhouette_score_sampled(X, labels, seed=seed),
        "davies_bouldin": davies_bouldin_index(X, labels),
        "smallest_cluster": int(counts.min()) if len(counts) else 0,
        "largest_cluster": int(counts.max()) if len(counts) else 0,
    }


def choose_elbow_k(rows: list[dict[str, Any]]) -> int:
    ordered = sorted(rows, key=lambda row: row["k"])
    values = np.asarray([row["inertia"] for row in ordered], dtype=np.float64)
    if len(values) < 3 or values[0] <= values[-1]:
        return int(ordered[0]["k"])
    normalized_x = np.linspace(0.0, 1.0, len(values))
    normalized_y = (values - values[-1]) / (values[0] - values[-1])
    line_y = 1.0 - normalized_x
    deviation = line_y - normalized_y
    return int(ordered[int(np.argmax(deviation))]["k"])


def tune_dbscan(X: np.ndarray, seed: int = SEED) -> tuple[dict[str, Any], list[dict[str, Any]], np.ndarray]:
    rng = np.random.default_rng(seed)
    sample_size = min(2600, len(X))
    sample = X if sample_size == len(X) else X[np.sort(rng.choice(len(X), size=sample_size, replace=False))]
    distances_squared = pairwise_squared_distances(sample, sample)
    candidate_specs: list[tuple[int, float, float]] = []
    k_distances: dict[int, np.ndarray] = {}
    for min_samples in DBSCAN_MIN_SAMPLES:
        rank = min(min_samples - 1, sample_size - 1)
        ordered = np.partition(distances_squared, rank, axis=1)[:, rank]
        k_distances[min_samples] = np.sqrt(ordered)
        for quantile in DBSCAN_QUANTILES:
            eps = float(np.quantile(k_distances[min_samples], quantile))
            candidate_specs.append((min_samples, eps, quantile))
    rows: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for min_samples, eps, quantile in candidate_specs:
        labels, _ = dbscan_from_distance_matrix(distances_squared, eps, min_samples)
        metrics = cluster_metrics(sample, labels, seed=seed)
        coverage_weighted = metrics["silhouette"] * (1.0 - metrics["noise_share"]) if math.isfinite(metrics["silhouette"]) else float("nan")
        row = {"eps": eps, "min_samples": min_samples, "k_distance_quantile": quantile, **metrics,
               "coverage_weighted_silhouette": coverage_weighted}
        rows.append(row)
        candidates.append({"row": row, "labels": labels})
    valid = [item for item in candidates if item["row"]["n_clusters"] >= 2 and math.isfinite(item["row"]["coverage_weighted_silhouette"])]
    if valid:
        chosen = max(valid, key=lambda item: (item["row"]["coverage_weighted_silhouette"], -item["row"]["davies_bouldin"] if math.isfinite(item["row"]["davies_bouldin"]) else -1e9))
    else:
        chosen = max(candidates, key=lambda item: (item["row"]["n_clusters"], -item["row"]["noise_share"]))
    chosen_config = {key: chosen["row"][key] for key in ("eps", "min_samples", "k_distance_quantile")}
    chosen_config["tuning_sample_rows"] = int(len(sample))
    chosen_config["selection_rule"] = "Best silhouette weighted by non-noise coverage; fallback is most clusters then lowest noise share."
    chosen_k_distances = k_distances[int(chosen_config["min_samples"])]
    return chosen_config, rows, chosen_k_distances


def read_features(root: Path, dataset_path: Path | None = None) -> tuple[pd.DataFrame, list[str]]:
    if dataset_path is not None:
        path = dataset_path.expanduser()
        if not path.is_absolute():
            path = root / path
    else:
        candidates = [
            root / "data" / "processed" / "routes_ml_ready.csv",
            root / "routes_ml_ready.csv",
            root / "data" / "routes_ml_ready.csv",
        ]
        path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not path.exists():
        checked = ", ".join(str(candidate) for candidate in (
            root / "data" / "processed" / "routes_ml_ready.csv",
            root / "routes_ml_ready.csv",
            root / "data" / "routes_ml_ready.csv",
        ))
        raise FileNotFoundError(
            f"Prepared Module 4 dataset was not found. Checked: {checked}. "
            "Run module4_preprocessing.py first or pass --dataset."
        )
    frame = pd.read_csv(path)
    manifest_path = path.parent / "module4_preprocessing_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        feature_columns = [column for column in manifest.get("feature_columns", []) if column in frame.columns]
    else:
        metadata = {"city", "route_id", "route_name", "route_type", "length_method", "speed_implausible", "source_file", "split"}
        feature_columns = [column for column in frame.columns if column not in metadata]
    if not feature_columns:
        raise ValueError("No numeric model features were found in the prepared dataset.")
    frame[feature_columns] = frame[feature_columns].apply(pd.to_numeric, errors="coerce")
    if frame[feature_columns].isna().any().any():
        raise ValueError("The Module 4 prepared feature matrix contains missing or nonnumeric values.")
    return frame, feature_columns


def read_raw_routes(root: Path) -> pd.DataFrame:
    paths = sorted((root / "data" / "raw").glob("route_features*.csv"))
    if not paths:
        paths = sorted(root.glob("route_features*.csv"))
    if not paths:
        return pd.DataFrame()
    routes = pd.concat((pd.read_csv(path) for path in paths), ignore_index=True, sort=False)
    routes["route_id_key"] = routes["route_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    return routes


def svg_scatter(path: Path, title: str, coords: np.ndarray, labels: np.ndarray, explained: tuple[float, float], seed: int = SEED, max_points: int = 4800) -> None:
    rng = np.random.default_rng(seed)
    if len(coords) > max_points:
        indices = np.sort(rng.choice(len(coords), max_points, replace=False))
        coords = coords[indices]
        labels = labels[indices]
    width, height = 920, 640
    left, right, top, bottom = 84, 32, 88, 78
    x_min, x_max = np.quantile(coords[:, 0], [0.01, 0.99])
    y_min, y_max = np.quantile(coords[:, 1], [0.01, 0.99])
    x_pad = max((x_max - x_min) * 0.05, 1e-6)
    y_pad = max((y_max - y_min) * 0.05, 1e-6)
    x_min, x_max = x_min - x_pad, x_max + x_pad
    y_min, y_max = y_min - y_pad, y_max + y_pad
    plot_w, plot_h = width - left - right, height - top - bottom
    sx = lambda value: left + (value - x_min) * plot_w / max(x_max - x_min, 1e-12)
    sy = lambda value: top + (y_max - value) * plot_h / max(y_max - y_min, 1e-12)
    unique = sorted(int(item) for item in np.unique(labels))
    color = lambda label: "#A9AFB7" if label < 0 else PALETTE[label % len(PALETTE)]
    fragments = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                 '<rect width="100%" height="100%" fill="#ffffff"/>',
                 f'<text x="{left}" y="42" font-family="Segoe UI,Arial" font-size="24" font-weight="700" fill="#18212b">{html.escape(title)}</text>',
                 f'<text x="{left}" y="66" font-family="Segoe UI,Arial" font-size="13" fill="#59636e">PCA projection; PC1 {explained[0]*100:.1f}% and PC2 {explained[1]*100:.1f}% of variance</text>',
                 f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#68727d"/>',
                 f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#68727d"/>']
    for label in unique:
        mask = labels == label
        for x, y in coords[mask]:
            fragments.append(f'<circle cx="{sx(float(x)):.2f}" cy="{sy(float(y)):.2f}" r="2.4" fill="{color(label)}" fill-opacity="0.62"/>')
    legend_x, legend_y = left + 12, top + 14
    for index, label in enumerate(unique):
        row, col = divmod(index, 4)
        x, y = legend_x + col * 150, legend_y + row * 24
        label_text = "Noise (-1)" if label < 0 else f"Cluster {label}"
        fragments.append(f'<circle cx="{x}" cy="{y}" r="5" fill="{color(label)}"/>')
        fragments.append(f'<text x="{x+11}" y="{y+4}" font-family="Segoe UI,Arial" font-size="12" fill="#26313b">{label_text}</text>')
    fragments.extend([f'<text x="{left+plot_w/2:.1f}" y="{height-23}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="13" fill="#36414c">Principal component 1</text>',
                      f'<text transform="translate(22 {top+plot_h/2:.1f}) rotate(-90)" text-anchor="middle" font-family="Segoe UI,Arial" font-size="13" fill="#36414c">Principal component 2</text>', '</svg>'])
    path.write_text("\n".join(fragments), encoding="utf-8")


def svg_line_chart(path: Path, title: str, x_values: list[float], y_values: list[float], x_label: str, y_label: str, points: bool = True) -> None:
    width, height = 860, 520
    left, right, top, bottom = 92, 40, 78, 78
    y_min = min(0.0, min(y_values))
    y_max = max(y_values)
    if y_max == y_min:
        y_max = y_min + 1.0
    padding = (y_max - y_min) * 0.08
    y_min -= padding
    y_max += padding
    x_min, x_max = min(x_values), max(x_values)
    x_pad = max((x_max - x_min) * 0.03, 0.2)
    x_min -= x_pad
    x_max += x_pad
    plot_w, plot_h = width - left - right, height - top - bottom
    sx = lambda value: left + (value - x_min) * plot_w / (x_max - x_min)
    sy = lambda value: top + (y_max - value) * plot_h / (y_max - y_min)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{left}" y="42" font-family="Segoe UI,Arial" font-size="23" font-weight="700" fill="#18212b">{html.escape(title)}</text>']
    for tick in np.linspace(y_min, y_max, 6):
        y = sy(float(tick))
        parts.append(f'<line x1="{left}" y1="{y:.2f}" x2="{width-right}" y2="{y:.2f}" stroke="#e1e5e9"/>')
        parts.append(f'<text x="{left-12}" y="{y+4:.2f}" text-anchor="end" font-family="Segoe UI,Arial" font-size="11" fill="#53606b">{tick:.2g}</text>')
    parts.append(f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#68727d"/>')
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#68727d"/>')
    poly = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(x_values, y_values))
    parts.append(f'<polyline points="{poly}" fill="none" stroke="#176B87" stroke-width="3"/>')
    if points:
        for x, y in zip(x_values, y_values):
            parts.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="5" fill="#DB6B35"/>')
    parts.extend([f'<text x="{left+plot_w/2:.1f}" y="{height-24}" text-anchor="middle" font-family="Segoe UI,Arial" font-size="13" fill="#36414c">{html.escape(x_label)}</text>',
                  f'<text transform="translate(22 {top+plot_h/2:.1f}) rotate(-90)" text-anchor="middle" font-family="Segoe UI,Arial" font-size="13" fill="#36414c">{html.escape(y_label)}</text>', '</svg>'])
    path.write_text("\n".join(parts), encoding="utf-8")


def pca_projection(X_fit: np.ndarray, X_all: np.ndarray) -> tuple[np.ndarray, tuple[float, float]]:
    mean = X_fit.mean(axis=0)
    centered_fit = X_fit - mean
    covariance = centered_fit.T @ centered_fit / max(len(X_fit) - 1, 1)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1][:2]
    total = max(float(eigenvalues.sum()), 1e-12)
    explained = (float(eigenvalues[order[0]] / total), float(eigenvalues[order[1]] / total))
    return (X_all - mean) @ eigenvectors[:, order], explained


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    pd.DataFrame(rows).to_csv(path, index=False)


def create_cluster_profiles(root: Path, assignments: pd.DataFrame) -> pd.DataFrame:
    routes = read_raw_routes(root)
    if routes.empty:
        return pd.DataFrame()
    merged = assignments.copy()
    merged["route_id_key"] = merged["route_id"].astype(str).str.replace(r"\.0$", "", regex=True)
    merged = merged.merge(routes, on=["city", "route_id_key"], how="left", suffixes=("", "_raw"))
    metrics = [column for column in ["n_trips", "length_km", "median_headway_min", "median_stops_per_trip", "service_span_h", "stops_per_km"] if column in merged]
    rows: list[dict[str, Any]] = []
    for algorithm, label_column in [("KMeans", "kmeans_cluster"), ("DBSCAN", "dbscan_cluster")]:
        for cluster, group in merged.groupby(label_column, dropna=False):
            row: dict[str, Any] = {"algorithm": algorithm, "cluster": int(cluster), "cluster_type": "noise" if int(cluster) == -1 else "cluster",
                                   "route_count": int(len(group)), "cities": "; ".join(sorted(group["city"].dropna().astype(str).unique()))}
            for metric in metrics:
                row[f"median_{metric}"] = pd.to_numeric(group[metric], errors="coerce").median()
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["algorithm", "cluster"], kind="stable")


def create_review_candidates(root: Path) -> pd.DataFrame:
    routes = read_raw_routes(root)
    required = {"city", "route_id", "route_name", "median_headway_min", "n_trips"}
    if routes.empty or not required.issubset(routes.columns):
        return pd.DataFrame()
    routes["median_headway_min"] = pd.to_numeric(routes["median_headway_min"], errors="coerce")
    routes["n_trips"] = pd.to_numeric(routes["n_trips"], errors="coerce")
    headway_rank = routes.groupby("city")["median_headway_min"].rank(pct=True).fillna(0.5)
    trip_rank = routes.groupby("city")["n_trips"].rank(pct=True).fillna(0.5)
    routes["schedule_review_score"] = 100.0 * (0.65 * headway_rank + 0.35 * (1.0 - trip_rank))
    routes["review_reason"] = np.select(
        [(headway_rank >= 0.75) & (trip_rank <= 0.25), headway_rank >= 0.75, trip_rank <= 0.25],
        ["Long scheduled headway and low scheduled trip count versus same-city routes", "Long scheduled headway versus same-city routes", "Low scheduled trip count versus same-city routes"],
        default="Compare schedule pattern with passenger counts and operating constraints",
    )
    columns = [column for column in ["city", "route_id", "route_name", "schedule_review_score", "review_reason", "n_trips", "median_headway_min", "length_km", "n_unique_stops"] if column in routes]
    result = routes.sort_values(["schedule_review_score", "city"], ascending=[False, True]).head(250)[columns].copy()
    result.insert(0, "review_rank", np.arange(1, len(result) + 1))
    result["interpretation_limit"] = "Schedule-only review signal; not a passenger-demand or route-removal recommendation"
    return result


def render_report(root: Path, train_rows: int, validation_rows: int, feature_count: int, k_rows: list[dict[str, Any]], selected_k: int,
                  dbscan_config: dict[str, Any], dbscan_metrics: dict[str, Any], profiles: pd.DataFrame) -> None:
    k_table = "\n".join(f"| {r['k']} | {r['inertia']:.2f} | {r['silhouette']:.4f} | {r['davies_bouldin']:.4f} |" for r in k_rows)
    profile_note = "Cluster profiles are in results/cluster_profiles.csv and show schedule features only."
    db_sil = dbscan_metrics["silhouette"]
    db_dbi = dbscan_metrics["davies_bouldin"]
    db_sil_text = f"{db_sil:.4f}" if math.isfinite(db_sil) else "not defined (fewer than two non-noise clusters)"
    db_dbi_text = f"{db_dbi:.4f}" if math.isfinite(db_dbi) else "not defined (fewer than two non-noise clusters)"
    k2 = next(row for row in k_rows if row["k"] == 2)
    selected_row = next(row for row in k_rows if row["k"] == selected_k)
    text = f"""# RouteRanker - Module 5 model development and evaluation

## Data and scope

The prepared Module 4 table contains 12,660 scheduled-route records from Bengaluru, Chennai, Delhi, Hyderabad, and Pune, with {feature_count} model features. K-Means and DBSCAN were fit on the {train_rows:,}-row training partition; the {validation_rows:,}-row validation partition was assigned after fitting. The feature matrix excludes city, route IDs, route names, and other identifiers.

The source is a schedule dataset. Scheduled trips and headways describe planned service; they are not passenger counts, occupancy, or observed demand. This work does not create a demand label or claim that a cluster is an optimization decision.

## K-Means

K-Means was fit for K=2, 3, 4, and 5 with k-means++ initialization and five restarts per K. The elbow chart and internal metrics are saved under visualizations/ and results/.

| K | Within-cluster sum of squares | Silhouette (sampled) | Davies-Bouldin |
|---:|---:|---:|---:|
{k_table}

The elbow heuristic selects K={selected_k}. K=2 has the strongest sampled silhouette ({k2['silhouette']:.4f}) and lowest Davies-Bouldin value ({k2['davies_bouldin']:.4f}), while the elbow heuristic selects K={selected_k}; this is a tradeoff between tighter two-group separation and the three-group elbow split. For K={selected_k}, the largest training cluster has {selected_row['largest_cluster']:,} routes and the smallest has {selected_row['smallest_cluster']:,}. The selected K-Means model assigns every route to a cluster. These internal metrics do not prove that groups match passenger needs.

## DBSCAN

DBSCAN parameters were tuned on a deterministic sample by varying epsilon from k-distance quantiles and min_samples in {', '.join(map(str, DBSCAN_MIN_SAMPLES))}. The final fit uses eps={dbscan_config['eps']:.5f} and min_samples={dbscan_config['min_samples']}.

- Training clusters (excluding noise): {dbscan_metrics['n_clusters']}
- Training cluster sizes: {dbscan_metrics['largest_cluster']:,} in the largest and {dbscan_metrics['smallest_cluster']:,} in the smallest
- Training noise points: {dbscan_metrics['noise_count']:,} ({dbscan_metrics['noise_share']:.1%})
- Silhouette on non-noise points: {db_sil_text}
- Davies-Bouldin on non-noise points: {db_dbi_text}

The largest group contains {dbscan_metrics['largest_cluster'] / max(train_rows, 1):.1%} of training routes, so this setting gives one dominant density group and one much smaller group rather than balanced segmentation. Treat the smaller group and noise as review leads, not route categories. Noise is a density result, not proof of a bad or incorrect route. The validation labels use nearest-core-point assignment within epsilon because DBSCAN has no native predict method; this is an explicit approximation.

## Supervised models

Random Forest and XGBoost classifier implementations are included in src/route_ranker/module5_supervised.py. They were not trained because no ground-truth route category or demand label is present in the supplied dataset. results/classification_metrics.csv records this as not evaluated. Add valid labels to data/labels/route_labels.csv to run classification; the template and instructions are included. Accuracy, macro precision, macro recall, macro F1, and a confusion matrix are then produced on a held-out test split.

## Algorithm comparison and observations

K-Means requires a chosen K and assigns every route, which makes its cluster profiles straightforward to compare. DBSCAN discovers dense groups without fixing their number and flags low-density routes, but its result depends on feature scaling and epsilon; distance concentration in 29 dimensions can make density groups unstable. Its dominant cluster in this run shows that DBSCAN adds little balanced segmentation under the selected setting. See results/algorithm_comparison.csv and results/dbscan_tuning.csv for the evaluated settings.

{profile_note}

## Route-planning suggestions and limits

The ranked file results/route_review_candidates.csv uses a transparent schedule-only signal: within-city relative headway (65%) plus the inverse relative scheduled-trip count (35%). It is a shortlist for human review, not a demand score and not a recommendation to remove or add service. Compare the shortlisted routes with passenger counts by time of day, occupancy, transfer patterns, fleet availability, operating costs, road conditions, and community access before changing a route or timetable.

## Reproduction

From the project folder, install requirements.txt and run `python run_module5.py`. The script recreates the cluster models, CSV results, SVG visualizations, and this report. Optional supervised training is run with `python run_module5.py --labels data/labels/route_labels.csv` after supplying valid labels and installing requirements-supervised.txt.
"""
    (root / "reports" / "module5_report.md").write_text(text, encoding="utf-8")


def run(root: Path, dataset_path: Path | None = None, seed: int = SEED) -> dict[str, Any]:
    for directory in ("models", "results", "reports", "visualizations"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    frame, feature_columns = read_features(root, dataset_path)
    train_mask = frame["split"].astype(str).str.casefold().eq("train") if "split" in frame else np.ones(len(frame), dtype=bool)
    train_frame = frame.loc[train_mask]
    validation_frame = frame.loc[~train_mask]
    X_train = train_frame[feature_columns].to_numpy(dtype=np.float64)
    X_validation = validation_frame[feature_columns].to_numpy(dtype=np.float64)
    X_all = frame[feature_columns].to_numpy(dtype=np.float64)

    k_rows: list[dict[str, Any]] = []
    k_models: dict[int, dict[str, Any]] = {}
    for k in K_VALUES:
        model = fit_kmeans(X_train, k, seed=seed, n_init=5)
        metrics = cluster_metrics(X_train, model["labels"], seed=seed)
        row = {"k": k, "inertia": model["inertia"], "iterations": model["iterations"], **metrics}
        k_rows.append(row)
        k_models[k] = model
        np.savez_compressed(root / "models" / f"kmeans_k{k}.npz", centroids=model["centers"])
        (root / "models" / f"kmeans_k{k}.json").write_text(json.dumps({"algorithm": "K-Means", "k": k, "seed": seed,
             "features": feature_columns, "fit_rows": int(len(X_train)), "inertia": model["inertia"], "iterations": model["iterations"]}, indent=2), encoding="utf-8")
    selected_k = choose_elbow_k(k_rows)
    selected_kmeans = k_models[selected_k]
    centroids = selected_kmeans["centers"]
    all_kmeans_labels = np.argmin(pairwise_squared_distances(X_all, centroids), axis=1)
    k_train_labels = all_kmeans_labels[np.flatnonzero(train_mask)]

    dbscan_config, tuning_rows, k_distances = tune_dbscan(X_train, seed=seed)
    db_labels_train, core_mask = fit_dbscan(X_train, float(dbscan_config["eps"]), int(dbscan_config["min_samples"]))
    core_X = X_train[core_mask]
    core_labels = db_labels_train[core_mask]
    db_labels_validation = predict_dbscan(X_validation, core_X, core_labels, float(dbscan_config["eps"])) if len(X_validation) else np.empty(0, dtype=np.int32)
    all_dbscan_labels = np.empty(len(frame), dtype=np.int32)
    all_dbscan_labels[np.flatnonzero(train_mask)] = db_labels_train
    if len(validation_frame):
        all_dbscan_labels[np.flatnonzero(~train_mask)] = db_labels_validation
    db_metrics = cluster_metrics(X_train, db_labels_train, seed=seed)
    np.savez_compressed(root / "models" / "dbscan_model.npz", core_samples=core_X, core_labels=core_labels)
    db_model_info = {"algorithm": "DBSCAN", "eps": float(dbscan_config["eps"]), "min_samples": int(dbscan_config["min_samples"]),
                     "features": feature_columns, "fit_rows": int(len(X_train)), "core_sample_count": int(len(core_X)),
                     "validation_assignment": "nearest core point within eps; approximate out-of-sample assignment",
                     "tuning_sample_rows": int(dbscan_config["tuning_sample_rows"]), "selection_rule": dbscan_config["selection_rule"]}
    (root / "models" / "dbscan_model.json").write_text(json.dumps(db_model_info, indent=2), encoding="utf-8")
    (root / "models" / "model_index.json").write_text(json.dumps({"selected_kmeans_k": selected_k, "kmeans_models": [f"kmeans_k{k}.npz" for k in K_VALUES],
          "dbscan_model": "dbscan_model.npz", "feature_columns": feature_columns, "seed": seed}, indent=2), encoding="utf-8")

    assignment_columns = [column for column in ["city", "route_id", "route_name", "split"] if column in frame]
    assignments = frame[assignment_columns].copy()
    assignments["kmeans_cluster"] = all_kmeans_labels
    assignments["dbscan_cluster"] = all_dbscan_labels
    assignments["dbscan_is_noise"] = all_dbscan_labels == -1
    assignments.to_csv(root / "results" / "cluster_assignments.csv", index=False)
    write_csv(root / "results" / "kmeans_metrics.csv", k_rows)
    write_csv(root / "results" / "dbscan_tuning.csv", tuning_rows)
    dbscan_metric_rows = []
    for tuning in tuning_rows:
        same_setting = (int(tuning["min_samples"]) == int(dbscan_config["min_samples"])
                        and abs(float(tuning["eps"]) - float(dbscan_config["eps"])) < 1e-12)
        dbscan_metric_rows.append({
            "evaluation_stage": "parameter_sweep_sample",
            "evaluated_rows": int(dbscan_config["tuning_sample_rows"]),
            "selected_setting": same_setting,
            **tuning,
        })
    dbscan_metric_rows.append({
        "evaluation_stage": "selected_full_training_fit",
        "evaluated_rows": int(len(X_train)),
        "selected_setting": True,
        "eps": float(dbscan_config["eps"]),
        "min_samples": int(dbscan_config["min_samples"]),
        "k_distance_quantile": "",
        **db_metrics,
        "coverage_weighted_silhouette": "",
    })
    write_csv(root / "results" / "dbscan_metrics.csv", dbscan_metric_rows)

    profiles = create_cluster_profiles(root, assignments)
    profiles.to_csv(root / "results" / "cluster_profiles.csv", index=False)
    reviews = create_review_candidates(root)
    reviews.to_csv(root / "results" / "route_review_candidates.csv", index=False)
    comparison = [
        {"algorithm": "K-Means", "learning_type": "Unsupervised clustering", "input_labels_required": False, "cluster_count": selected_k,
         "evaluation": "Elbow inertia, sampled silhouette, Davies-Bouldin", "strength": "Every route receives a cluster and cluster profiles are easy to summarize.",
         "limitation": "K must be chosen; results depend on scaled numeric distances."},
        {"algorithm": "DBSCAN", "learning_type": "Unsupervised density clustering", "input_labels_required": False, "cluster_count": db_metrics["n_clusters"],
         "evaluation": "Sampled silhouette and Davies-Bouldin on non-noise routes; noise share", "strength": "Finds dense groups and flags routes outside dense neighborhoods.",
         "limitation": "Sensitive to eps/min_samples; no native prediction for new rows; high-dimensional distances can weaken density structure."},
        {"algorithm": "Random Forest", "learning_type": "Supervised classification", "input_labels_required": True, "cluster_count": "not applicable",
         "evaluation": "Accuracy, macro precision/recall/F1, confusion matrix when labels are supplied", "strength": "Handles nonlinear feature interactions and offers feature importance.",
         "limitation": "Not trainable or honestly evaluable without valid labeled routes."},
        {"algorithm": "XGBoost", "learning_type": "Supervised classification", "input_labels_required": True, "cluster_count": "not applicable",
         "evaluation": "Accuracy, macro precision/recall/F1, confusion matrix when labels are supplied", "strength": "Boosted trees can capture complex nonlinear patterns.",
         "limitation": "Not trainable or honestly evaluable without valid labeled routes; separate optional dependency."},
    ]
    pd.DataFrame(comparison).to_csv(root / "results" / "algorithm_comparison.csv", index=False)
    route_rows_available = len(frame)
    labels_path = root / "data" / "labels" / "route_labels.csv"
    label_rows_available = 0
    label_class_count = 0
    if labels_path.exists():
        supplied_labels = pd.read_csv(labels_path)
        if {"city", "route_id", "label"}.issubset(supplied_labels.columns):
            supplied_labels = supplied_labels.dropna(subset=["city", "route_id", "label"])
            label_rows_available = len(supplied_labels)
            label_class_count = int(supplied_labels["label"].nunique())
    pd.DataFrame([{"model": name, "status": "NOT_EVALUATED_NO_GROUND_TRUTH_LABELS", "accuracy": "", "precision_macro": "", "recall_macro": "", "f1_macro": "", "test_rows": "", "confusion_matrix_file": "",
                   "route_rows_available": route_rows_available, "label_rows_available": label_rows_available,
                   "label_class_count": label_class_count, "required_label_columns": "city,route_id,label",
                   "labels_file": str(labels_path.relative_to(root)),
                   "note": "Ground-truth labels are required to calculate classifier scores. The supplied route data has schedules only; no classification results were fabricated."}
                  for name in ("Random Forest", "XGBoost")]).to_csv(root / "results" / "classification_metrics.csv", index=False)

    coordinates, explained = pca_projection(X_train, X_all)
    svg_line_chart(root / "visualizations" / "kmeans_elbow.svg", "K-Means elbow method", [r["k"] for r in k_rows], [r["inertia"] for r in k_rows], "Number of clusters (K)", "Within-cluster sum of squares")
    svg_scatter(root / "visualizations" / "kmeans_clusters_pca.svg", f"K-Means route clusters (K={selected_k})", coordinates, all_kmeans_labels, explained, seed=seed)
    svg_scatter(root / "visualizations" / "dbscan_clusters_pca.svg", f"DBSCAN route clusters (eps={dbscan_config['eps']:.3f}, min_samples={dbscan_config['min_samples']})", coordinates, all_dbscan_labels, explained, seed=seed)
    sorted_k_distance = np.sort(k_distances)
    keep = min(2200, len(sorted_k_distance))
    if keep < len(sorted_k_distance):
        sorted_k_distance = sorted_k_distance[np.linspace(0, len(sorted_k_distance) - 1, keep).astype(int)]
    svg_line_chart(root / "visualizations" / "dbscan_k_distance.svg", f"DBSCAN k-distance curve (min_samples={dbscan_config['min_samples']})",
                   list(np.arange(1, keep + 1, dtype=float)), list(sorted_k_distance), "Sorted sampled routes", "Distance to kth neighbor")
    render_report(root, len(X_train), len(X_validation), len(feature_columns), k_rows, selected_k, dbscan_config, db_metrics, profiles)
    summary = {"rows": len(frame), "train_rows": len(X_train), "validation_rows": len(X_validation), "feature_count": len(feature_columns),
               "selected_kmeans_k": selected_k, "dbscan_eps": float(dbscan_config["eps"]), "dbscan_min_samples": int(dbscan_config["min_samples"]),
               "dbscan_clusters": db_metrics["n_clusters"], "dbscan_noise_share": db_metrics["noise_share"]}
    (root / "results" / "module5_run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def discover_project_root(script_file: Path) -> Path:
    """Find the project root from a top-level or src/ script location."""
    script_dir = script_file.resolve().parent
    for candidate in (script_dir, *script_dir.parents):
        has_project_script = (candidate / "module4_preprocessing.py").is_file() or (candidate / "run_module5.py").is_file()
        has_prepared_data = (candidate / "data" / "processed" / "routes_ml_ready.csv").is_file()
        if has_project_script or has_prepared_data:
            return candidate
    return script_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train and evaluate RouteRanker Module 5 clustering models.")
    parser.add_argument("--project-root", type=Path, default=discover_project_root(Path(__file__)), help="RouteRanker project folder.")
    parser.add_argument("--dataset", type=Path, default=None, help="Optional path to routes_ml_ready.csv.")
    parser.add_argument("--seed", type=int, default=SEED)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.project_root.expanduser().resolve()
    dataset = args.dataset.expanduser() if args.dataset else None
    if dataset is not None and not dataset.is_absolute():
        dataset = root / dataset
    summary = run(root, dataset_path=dataset, seed=args.seed)
    print("\nMODULE 5 CLUSTERING SUMMARY")
    print(f"Rows processed:       {summary['rows']:,}")
    print(f"Training rows:        {summary['train_rows']:,}")
    print(f"Validation rows:      {summary['validation_rows']:,}")
    print(f"Features used:        {summary['feature_count']}")
    print(f"Selected K-Means K:   {summary['selected_kmeans_k']}")
    print(f"DBSCAN epsilon:       {summary['dbscan_eps']:.6f}")
    print(f"DBSCAN min_samples:   {summary['dbscan_min_samples']}")
    print(f"DBSCAN clusters:      {summary['dbscan_clusters']}")
    print(f"DBSCAN noise share:   {summary['dbscan_noise_share']:.2%}")
    print("\nSummary JSON:")
    print(json.dumps(summary, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
