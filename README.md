# RouteRanker – AI-Powered Public Transit Route Optimization

Branch `Satyam` – **Module 1: Data Collection and Dataset Understanding** (no cleaning, no models yet).

## Status and honest limitations
* The dataset named in the project document (Lepton Software on Datarade) is a **paid listing**: no download link, pricing only on request, masked sample. It could **not** be obtained.
* Open GTFS bus feeds for **7 cities** were collected instead: Ahmedabad, Bengaluru, Chennai, Delhi, Hyderabad, Kochi, Pune. Mumbai, Rajkot and Hubli-Dharwad: no open feed found.
* GTFS contains **no passenger counts or occupancy**. None are created or assumed in this module.
* Raw files are **not committed** (large, third-party licences). Re-create them with `download_data.py`.

## How to run
```bash
pip install -r requirements.txt
python download_data.py                 # 1. raw feeds -> data/raw/<city>/<city>_gtfs.zip (originals stay untouched)
python run_module1.py                   # 2. extract .txt, inspect every city read-only, write reports/
# 3. open notebooks/module1_data_collection.ipynb (set CITY in the second cell) and Run All
```
`download_data.py <city>` downloads a single city. If a URL fails, download the ZIP manually from the link in `reports/module1_data_sources.md` into `data/raw/<city>/`.

## Deliverables
| Deliverable | File |
|---|---|
| Dataset source documentation (incl. Lepton access finding) | `reports/module1_data_sources.md` |
| Dataset inventory + data-quality observations | `reports/module1_dataset_inventory.md`, `reports/module1_file_inventory.csv`, `reports/module1_quality_issues.csv` |
| Relationship documentation | `reports/module1_relationships.md` |
| Notebook (load + inspect with pandas) | `notebooks/module1_data_collection.ipynb` |
| Code | `src/inspect_gtfs.py` (read-only inspection), `run_module1.py`, `download_data.py` |

## Folder layout
```
data/raw/<city>/      original ZIP + extracted GTFS .txt files (git-ignored)
data/processed/       reserved for Module 2
notebooks/            module1_data_collection.ipynb
reports/              module1_*.md / *.csv
src/                  inspect_gtfs.py
```

## Key observations (details in `reports/module1_dataset_inventory.md`)
* Weekday and weekend service cannot be separated in 6 of the 7 feeds (every service runs all 7 days).
* Delhi and Kochi schedules are expired (2022–24); most other feeds are community-compiled, not operator-published.
* Some feeds contain many times beyond 24:00:00 (valid GTFS; must be handled later) and a few duplicate trip IDs.
