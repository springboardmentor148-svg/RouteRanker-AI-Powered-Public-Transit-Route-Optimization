# RouteRanker – AI-Powered Public Transit Route Optimization

Branch `Satyam` – **Modules 1–4: data collection, feature engineering, EDA, data preprocessing** (no models yet).

## Status and honest limitations
* The dataset named in the project document (Lepton Software on Datarade) is a **paid listing** (no download link, price on request, masked sample) and could **not** be obtained.
* Open GTFS bus feeds for **7 cities** were used instead: Ahmedabad, Bengaluru, Chennai, Delhi, Hyderabad, Kochi, Pune. No open feed was found for Mumbai, Rajkot or Hubli-Dharwad.
* GTFS describes **planned** service. It has **no passenger counts or occupancy**. Every feature is a *scheduled* quantity (trips, stops, headway); nothing is estimated as demand, and no route is called overcrowded or underutilised.
* Raw GTFS files are **not committed** (large, third-party licences): recreate them with `download_data.py`.

## How to run
```bash
pip install -r requirements.txt
python download_data.py          # raw feeds -> data/raw/<city>/<city>_gtfs.zip (originals stay untouched)
python run_module1.py            # Module 1: extract + inspect + reports/module1_*
python run_module2.py            # Module 2: clean + features -> data/processed/<city>/ + reports/module2_*
python run_module3.py            # Module 3: EDA -> reports/figures, maps, tables, module3_*
python run_module4.py            # Module 4: preprocessing -> data/processed/module4/, reports/module4_*  (--include-all keeps every feed)
```
Notebooks (one per module, executed with outputs): `notebooks/module1_data_collection.ipynb`, `module2_feature_engineering.ipynb`, `module3_eda.ipynb`, `module4_data_preprocessing.ipynb` – set `CITY` in the second cell.

## Deliverables
| Module | Deliverable | File |
|---|---|---|
| 1 | Sources (incl. Lepton access finding), inventory, quality observations, relationships | `reports/module1_*.md/csv` |
| 2 | Feature-engineered dataset (route profiles) | `data/processed/<city>/route_features.csv`, `all_cities_route_features.csv`; route×hour: `route_hour_features.csv`; stops: `stop_usage.csv` |
| 2 | Feature dictionary / data-quality report / assumptions and limitations / route profile summary | `reports/module2_feature_dictionary.md`, `module2_data_quality_report.md`, `module2_assumptions_limitations.md`, `module2_route_profile_summary.md`, `module2_cleaning_log.csv` |
| 3 | Exploratory analysis report, route comparison summary, data quality summary, findings & limitations | `reports/module3_exploratory_analysis_report.md`, `module3_route_comparison_summary.md`, `module3_data_quality_summary.md`, `module3_findings_and_limitations.md`, `module3_cross_city_summary.csv` |
| 3 | Visualisations, maps, tables | `reports/figures/<city>/`, `reports/maps/*.html`, `reports/tables/` |
| 4 | Processed (model-ready) dataset: train / validation CSV, fitted preprocessor, feature list, excluded routes | `data/processed/module4/` |
| 4 | Missing values, encoding & scaling, split & evaluation strategy, features & decisions, assumptions & limitations | `reports/module4_missing_values_summary.md`, `module4_encoding_and_scaling.md`, `module4_split_and_evaluation_strategy.md`, `module4_feature_selection_and_decisions.md`, `module4_assumptions_limitations.md` |

## Code layout
```
src/inspect_gtfs.py       Module 1  read-only inspection
src/cleaning.py           Module 2  documented cleaning (every action logged with a reason)
src/module2_features.py   Module 2  time, aggregation, headway, route length (shapes.txt first), overlap
src/feature_dictionary.py Module 2  single source of the feature dictionary
src/gtfs_utils.py         shared GTFS helpers (time parsing, frequency expansion, distances, overlap)
src/eda.py                Module 3  tables, charts, maps, data-driven observations
src/preprocessing.py      Module 4  imputation, encoding, scaling, grouped train/validation split (fit on training only)
data/raw/<city>/          original ZIP + extracted .txt  (git-ignored)
data/processed/<city>/    engineered CSVs
```

## Key observations (details in the reports)
* Weekday and weekend schedules are identical in most feeds (every service runs every day).
* Delhi and Kochi calendars are expired (2022-24). Delhi, Kochi and Pune show near-constant scheduled speeds (possibly generated timetables); Hyderabad's "trips" look like whole vehicle duties; Chennai's `shapes.txt` only covers the metro. These feeds are **not directly comparable** with each other.
* Scheduled service per route is very uneven (e.g. Bengaluru: median 3 trips, maximum 398). Route pairs that share stops or corridors are listed as *candidates for investigation*, not as confirmed redundancy.

## Module 4 in one paragraph
The Module-2 route features are prepared for the planned **unsupervised** models (KMeans, DBSCAN): missing headways (routes with a single trip, undefined in GTFS) are median-imputed with an indicator column, impossible speeds are treated as invalid, skewed counts get `log1p`, features are standardised, categories one-hot encoded, and the data is split 80:20 grouped by bus line (fit on training only). **No supervised target or demand value was created** because GTFS has no passenger data. Hyderabad (trips look like whole vehicle duties) is excluded from the pooled set but not deleted - to be confirmed with the mentor.
