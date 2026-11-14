# RouteRanker - Module 6 Inference and Route Optimization

This is a VS Code-ready Module 6 project. It reuses the trained Module 5 K-Means and DBSCAN model files and the saved Module 4 preprocessing manifest. It does not retrain the clustering models or refit preprocessing.

## Open and run in VS Code

1. Extract `RouteRanker_Module6_Submission.zip` and open the extracted folder in VS Code.
2. In a terminal at the project root, create and activate a virtual environment if desired.
3. Install the core dependencies and run:

```powershell
python -m pip install -r requirements.txt
python run_module6.py
```

The script runs model inference on `data/inference/unseen_routes.csv`, creates assignments and route-review outputs, applies the separate frequency sensitivity scenario, and prints a summary in the terminal.

To use a different raw route-feature CSV or a Module 4 prepared CSV:

```powershell
python run_module6.py --unseen-data path\to\new_routes.csv
```

Raw input must contain the route-level fields documented in `data/processed/module4_preprocessing_manifest.json`. The code applies the saved Module 4 medians, log transforms, robust scaler values, cyclic time features, and one-hot categories. A Module 4 prepared input is validated and used directly without scaling it a second time.

## Notebook

Open `notebooks/module6_inference_optimization.ipynb` in VS Code, select a Python kernel, and run its cells from top to bottom. If the notebook kernel needs dependencies, run:

```powershell
python -m pip install -r requirements-notebook.txt
```

## Project map

- `models/` - Module 5 K-Means and DBSCAN NPZ model files, model JSON metadata, and Module 4 preprocessing manifest.
- `models/readable/` - CSV exports of model arrays for opening directly in VS Code or spreadsheet software; the NPZ files remain the runtime model files.
- `data/processed/` - original prepared Module 4 data, train/validation split, and preprocessing manifest. Keep these source files unchanged.
- `data/raw/` - original route-feature CSVs used for route-level review and network metrics.
- `data/inference/unseen_routes.csv` - raw held-out validation routes used as the Module 6 unseen inference example.
- `data/inference/unseen_routes_prepared.csv` - corresponding Module 4 transformed validation feature rows.
- `data/simulation/simulated_network_frequency_scenario.csv` - separate simulated network copy; source route data is unchanged.
- `src/route_ranker/module6_inference.py` - loads saved models, applies saved preprocessing, and assigns clusters.
- `src/route_ranker/module6_optimization.py` - review signals, merge/split screening, trip-frequency sensitivity scenario, metrics, and SVG charts.
- `src/route_ranker/module6_workflow.py` - end-to-end workflow.
- `previous_modules/` - copies of the Module 4/5 implementation scripts used to produce the supplied prepared data and models.
- `results/inference_assignments.csv` - predictions for held-out unseen routes.
- `results/network_model_assignments.csv` - model assignments across the full route inventory for screening.
- `results/potential_route_review.csv` - routes with explicit screening signals and reasons.
- `results/merge_review_candidates.csv`, `results/split_review_candidates.csv`, and `results/optimization_suggestions.csv` - conditional planner review suggestions.
- `results/current_vs_simulated_network_metrics.csv` - current versus simulated schedule-level metrics.
- `results/classification_availability.csv` - supervised model availability and why no classifier scores are supplied.
- `reports/module6_report.md` - observations, scenario results, limitations, and next steps.
- `visualizations/` - SVG visuals for held-out clusters and scenario metrics.

## Interpretation and limitations

All cluster assignments are model-generated groups, not route-quality labels. DBSCAN inference uses nearest saved core samples within `eps`, an explicit approximation because DBSCAN has no native prediction method. Classifier files are loaded only if trained Module 5 Random Forest or XGBoost models are present. The supplied data has no ground-truth route or demand labels, so no supervised scores or passenger-demand predictions are invented.

The optimization analysis treats long headways, scheduled trips, route overlap, route length, and model outliers as screening evidence only. It does not label routes inefficient. The simulated scenario adds one scheduled trip to routes with both high same-city headway and low same-city trip count; this is a sensitivity example, not an operational recommendation. Merges and splits are provided as manual review candidates and are not simulated because stop sequences, transfer connectivity, passenger demand, capacity, and route-coverage constraints are not available.

The comparison uses identical schedule-level definitions for current and simulated data. Route count and total route length remain unchanged in a frequency-only scenario by design. Add reliable passenger counts, stop-level shapes, transfers, fleet/cost constraints, and accessibility measures before making actual service changes.

## GitHub

This folder is organized for a repository. Review generated outputs, then commit and push it on your team's feature branch using the team's normal GitHub workflow.
