"""End-to-end Module 6 inference, route review, and simulation workflow."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .module6_inference import run_inference
from .module6_optimization import _key, analyze_network, load_raw_network


def discover_project_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / "models" / "model_index.json").is_file() and (
            candidate / "data" / "processed" / "module4_preprocessing_manifest.json"
        ).is_file():
            return candidate
    raise FileNotFoundError("Could not find a RouteRanker Module 6 project root with models/ and data/processed/.")


def _prepare_default_unseen_data(root: Path) -> tuple[Path, Path, pd.DataFrame]:
    processed_path = root / "data" / "processed" / "routes_ml_ready.csv"
    if not processed_path.is_file():
        raise FileNotFoundError(f"Prepared Module 4 dataset is missing: {processed_path}")
    processed = pd.read_csv(processed_path, dtype={"city": "string", "route_id": "string"})
    if "split" not in processed:
        raise ValueError("Prepared Module 4 dataset must include the original train/validation split column.")
    processed["city"] = processed["city"].astype("string").str.strip().str.casefold()
    processed["route_id"] = processed["route_id"].astype("string").str.strip().str.replace(r"\.0$", "", regex=True)
    raw_network = load_raw_network(root)
    raw_network["_route_key"] = _key(raw_network)
    processed["_route_key"] = _key(processed)
    split_lookup = processed[["_route_key", "split"]].drop_duplicates("_route_key")
    network = raw_network.merge(split_lookup, on="_route_key", how="left", validate="one_to_one").drop(columns=["_route_key"])
    if network["split"].isna().any():
        raise ValueError(f"{int(network['split'].isna().sum())} raw routes do not match the prepared Module 4 route keys.")

    inference_dir = root / "data" / "inference"
    inference_dir.mkdir(parents=True, exist_ok=True)
    unseen_path = inference_dir / "unseen_routes.csv"
    prepared_unseen_path = inference_dir / "unseen_routes_prepared.csv"
    all_network_path = inference_dir / "network_routes_with_split.csv"
    if not unseen_path.is_file():
        network.loc[network["split"].astype(str).str.casefold().eq("validation")].to_csv(unseen_path, index=False)
    if not prepared_unseen_path.is_file():
        processed.loc[processed["split"].astype(str).str.casefold().eq("validation")].drop(columns=["_route_key"]).to_csv(prepared_unseen_path, index=False)
    network.to_csv(all_network_path, index=False)
    return unseen_path, all_network_path, network


def _write_report(root: Path, summary: dict[str, Any]) -> None:
    unseen = summary["unseen_inference"]
    analysis = summary["network_analysis"]
    metrics_path = root / "results" / "current_vs_simulated_network_metrics.csv"
    metrics = pd.read_csv(metrics_path)
    metric_lines = ["| Metric | Current | Simulated | Change | Unit |", "|---|---:|---:|---:|---|"]
    for _, row in metrics.iterrows():
        metric_lines.append(
            f"| {row['metric']} | {row['current_value']:.3f} | {row['simulated_value']:.3f} | "
            f"{row['delta']:+.3f} | {row['unit']} |"
        )
    classifier_lines = "\n".join(f"- {name}: {status}" for name, status in unseen["classification_status"].items())
    text = f"""# RouteRanker Module 6: Inference and Route Optimization

## Scope and source data

This run reuses the saved Module 5 K-Means and DBSCAN models and the Module 4 preprocessing manifest. It does not retrain the clustering models or fit a new scaler. The held-out validation routes are used as unseen inference records; the prepared Module 4 source dataset remains unchanged.

- Unseen inference records: {unseen['input_rows']:,}
- Feature count: {unseen['feature_count']}
- Preprocessing used: {unseen['preprocessing_mode']}
- Selected K-Means K: {unseen['selected_kmeans_k']}
- DBSCAN eps / min_samples: {unseen['dbscan_eps']:.6f} / {unseen['dbscan_min_samples']}
- DBSCAN assignment: nearest saved core sample within eps. This is an approximation because DBSCAN has no native predict method.

## Inference results

K-Means assigns each inference route to its nearest saved centroid. Cluster counts on the held-out routes: `{json.dumps(unseen['kmeans_cluster_counts'], sort_keys=True)}`.

DBSCAN assigns a route to the nearest saved core sample if the distance is within eps; otherwise it marks it as noise. Cluster counts including noise: `{json.dumps(unseen['dbscan_cluster_counts_including_noise'], sort_keys=True)}`. Noise share: {unseen['dbscan_noise_share']:.2%}. Noise is a density result, not proof of a bad route.

### Optional classification models

{classifier_lines}

The supplied schedule dataset contains no ground-truth route-category or passenger-demand labels, so Random Forest and XGBoost were not trained. No classification labels or scores were invented.

## Routes for planner review

The output `results/potential_route_review.csv` combines independent evidence such as DBSCAN noise, a city-relative K-Means distance tail, high headway with low scheduled trip count, long length with long trip duration, and high route-overlap indicators. A single signal is not called inefficiency. The table is a screening list for human review and includes reasons per route.

The merge review list uses the source `overlap_partner`, `max_stop_overlap`, and `overlap_share_of_route` fields to identify pairs. These are pair-review candidates only. The available aggregate fields do not establish that a merge would preserve passenger coverage or capacity.

Split review candidates have both long route length and long trip duration relative to their city. Stop sequences, transfer connectivity, and passenger journeys are not included, so no split geometry is fabricated.

Trip-frequency review candidates have high median scheduled headway and low scheduled trip count relative to same-city quartiles. These remain schedule-only signals, not demand estimates.

## Simulated network comparison

The simulation adds one scheduled trip to each frequency-review route. It is a transparent sensitivity scenario, not an operational recommendation. It does not modify the source dataset. No merge or split is applied because connectivity and passenger coverage cannot be estimated from the available data.

{chr(10).join(metric_lines)}

The scenario changes scheduled-trip metrics only. Route count and sum of route lengths stay constant by design; passenger demand, occupancy, operating cost, fleet requirements, route coverage, and exact headway changes are not estimated.

## Outputs

- `results/inference_assignments.csv`: held-out unseen route predictions.
- `results/network_model_assignments.csv`: model assignments across the full route inventory for screening and comparison.
- `results/potential_route_review.csv`: routes with screening signals and evidence.
- `results/merge_review_candidates.csv` and `results/split_review_candidates.csv`: conditional planner review lists.
- `results/optimization_suggestions.csv`: evidence, proposal, and simulation status for each action.
- `data/simulation/simulated_network_frequency_scenario.csv`: separate simulated copy of the network.
- `results/current_vs_simulated_network_metrics.csv`: comparable current and scenario metrics.
- `visualizations/`: SVG cluster and network comparison charts.

## Limitations and next steps

The source records describe scheduled service, not passenger use. Route-overlap and route-length fields are aggregate; they cannot validate a merge or define split points. Before changing service, add reliable stop sequences, passenger counts by time period, transfer journeys, vehicle capacity, fleet constraints, operating costs, and service obligations. Compare all proposed outcomes with coverage and accessibility requirements.
"""
    (root / "reports" / "module6_report.md").write_text(text, encoding="utf-8")


def run_module6(project_root: Path, unseen_input: Path | None = None) -> dict[str, Any]:
    root = project_root.resolve()
    for folder in ("data/inference", "data/simulation", "results", "reports", "visualizations"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    default_unseen, network_path, raw_network = _prepare_default_unseen_data(root)
    unseen_path = unseen_input.expanduser().resolve() if unseen_input is not None else default_unseen
    unseen_assignments, unseen_summary = run_inference(root, unseen_path, root / "results" / "inference_assignments.csv")
    network_assignments, network_summary = run_inference(root, network_path, root / "results" / "network_model_assignments.csv")
    analysis_summary = analyze_network(root, raw_network, network_assignments)
    pd.DataFrame([
        {
            "model": name,
            "status": status,
            "note": "No trained labelled classifier was supplied; valid route or passenger-demand labels are required before classification predictions can be produced.",
        }
        for name, status in unseen_summary["classification_status"].items()
    ]).to_csv(root / "results" / "classification_availability.csv", index=False)
    summary = {
        "unseen_inference": unseen_summary,
        "full_network_inference": network_summary,
        "network_analysis": analysis_summary,
    }
    (root / "results" / "module6_run_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (root / "results" / "unseen_inference_summary.json").write_text(json.dumps(unseen_summary, indent=2) + "\n", encoding="utf-8")
    _write_report(root, summary)
    return summary
