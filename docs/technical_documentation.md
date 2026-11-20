# RouteRanker Dashboard – Technical Documentation (Module 7)

## 1. Purpose
A single Streamlit application to explore the dataset, EDA, clustering, model predictions, optimisation suggestions and the
current-vs-simulated comparison. No new dataset is introduced and no value is hard-coded: everything is read from files written by
`run_module2-6.py` or computed with the saved models and `src/` functions.

## 2. Architecture
```
run_module1-6.py -> data/processed, models/, data/inference, data/simulated, reports/tables
        |
modules/data_loader.py       cached readers (st.cache_data / cache_resource); missing_files() guard
modules/data_validation.py   upload reading, schema table, quality report, validate_for_inference
modules/route_analysis.py    filters, peer percentiles, group comparison, hourly profile of a route
modules/clustering.py        PCA projection of the 25 model features; KMeans profile; DBSCAN summary
modules/predictions.py       live evaluation and prediction with the saved Random Forest / XGBoost
modules/optimization.py      what-if candidates and scenario metrics (calls src/optimization.py)
modules/visualizations.py    Plotly figure builders
app.py                       sidebar, global city filter, nine page functions
app_legacy.py                the earlier prototype dashboard (kept for reference, not used)
```

## 3. Data flow
1. `app.py` checks `dl.missing_files()`; if anything is missing it shows the list and stops.
2. The sidebar *Cities in scope* filter restricts every page. Hyderabad is excluded by default (not comparable; trips look like vehicle duties).
3. Pages call cached loaders, so a rerun after a widget change does not reread files.
4. Optimisation thresholds from *Route Optimization* are stored in `st.session_state["opt_params"]` and reused by *Metrics Comparison*.

## 4. Key design decisions
- **Parameterised optimisation:** `src/optimization.py` functions take thresholds with the Module-6 defaults, so the dashboard recalculates
  live with the same code. With default thresholds the output must equal the saved Module 6 files; the Metrics page repeats this check.
- **Honest labelling:** colour-coded badges (ACTUAL / MODEL PREDICTION / ESTIMATE / SIMULATED). Deltas in comparisons are neutral (no green/red).
- **Missing and invalid data:** missing values are reported, never replaced by zero; upload validation reports missing columns, non-numeric
  columns, duplicate (city, route_id) and n_trips <= 0 instead of altering data.
- **Supervised models:** target is the city of a route (the only real label). Not a quality or demand predictor.
- **Optimisation:** merge, split and frequency rules are explicit and shown on the page. Frequency only adds trips to meet an assumed headway
  standard; no reductions are suggested. Stop coverage is preserved by construction.

## 5. Simulation assumptions
- Merge: absorbed route's departures kept; unshared length = length x (1 - shared-stop share) added to the target; absorbed route removed.
- Split: cut at the middle stop; two routes of half length, each keeping all departures; transfer burden ignored.
- Frequency: trips added until the busiest hour reaches the headway standard.
- Combined: precedence merge > split > frequency.

## 6. Testing
`tests/test_dashboard.py` (10 tests): every section renders, home metrics equal the data, city filter changes counts, thresholds change merge
candidates, default metrics equal Module 6 outputs, saved models give valid predictions, upload validation and file reading, all-cities
(incl. Hyderabad) and single-city edge cases. Run with `python tests/test_dashboard.py` or `pytest tests/`.

## 7. Limitations
GTFS is schedule-only (no ridership, occupancy, delays); 7 of 23 planned cities; feeds are not directly comparable; clusters are weakly
separated and are not performance classes; simulated results are not validated forecasts.
