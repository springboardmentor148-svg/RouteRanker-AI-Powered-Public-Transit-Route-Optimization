# RouteRanker — AI-Powered Public Transit Route Optimization

RouteRanker is an AI-driven public transit analysis and route optimization project designed to evaluate, profile, and optimize bus transit networks across major Indian metropolitan areas using General Transit Feed Specification (GTFS) datasets.

---

## 1. Project Overview & Scope

Public transit networks in rapidly growing urban centers require robust, data-backed operational insights to balance service coverage, reduce headway variance, and improve network efficiency. RouteRanker standardizes multi-city GTFS feeds into harmonized route profiles and analytical feature sets.

### Target Cities
The project analyzes scheduled transit operations across six Indian transit systems:
- **Hyderabad** (TGSRTC)
- **Mumbai** (BEST)
- **Pune** (PMPML)
- **Chennai** (MTC / Unified GTFS)
- **Ahmedabad** (AMTS / BRTS)
- **Rajkot** (RRL)

---

## 2. Project Modules & Milestones

### Module 1: Dataset Collection, Inventory, and Validation
- **Feed Acquisition (`download_gtfs.py`):** Automated retrieval and extraction of open-access GTFS feeds into `data/raw/<City>/`.
- **Feed Verification (`verify_gtfs.py`):** Schema verification across mandatory GTFS components (`routes.txt`, `trips.txt`, `stops.txt`, `stop_times.txt`, `calendar.txt` / `calendar_dates.txt`).
- **Data Inventory (`dataset_inventory.py` & `dataset_inventory.csv`):** Record counts and completeness audit across cities.
- **Data Cleaning & Harmonization (`milestone1.py` & `check_missing.py`):** Removal of duplicate identifiers, orphan trip references, and coordinate normalization into city-level cleaned tables (`<City>_routes_cleaned.csv`, `<City>_stops_cleaned.csv`, `<City>_trips_cleaned.csv`, etc.).

### Module 2: Feature Engineering & Data Quality Checks
Executed and documented within [`RouteRanker.ipynb`](file:///RouteRanker.ipynb):
1. **GTFS File Availability Audit:** Cross-city validation of available schedule tables.
2. **Missing Value Analysis:** Quantifying missing attributes prior to and following cleaning.
3. **Time-Based Features:** Departure and arrival time normalization, timepoint alignment, and morning/evening peak classification.
4. **Basic Route Profiles:** Route-level aggregation of trip frequencies, stop counts, and span of service.
5. **Scheduled Departures by Hour:** Hourly departure distributions (hours 0–23) across transit lines.
6. **Route Distance Estimation:** Trip distance approximations using available shape geometries and consecutive stop haversine calculations.
7. **Operating Day Analysis:** Weekly operational frequency metrics derived from GTFS calendar service flags.
8. **Combined Feature Engineering:** Generation of the unified dataset [`module2_feature_engineered_dataset.csv`](file:///data/processed/module2_feature_engineered_dataset.csv).
9. **Feature Dictionary & Quality Verification:** Column specifications documented in [`module2_feature_dictionary.csv`](file:///data/processed/module2_feature_dictionary.csv) and validated via [`module2_final_verification_report.csv`](file:///data/processed/module2_final_verification_report.csv).
10. **Assumptions & Limitations:** Methodological constraints and scope documented in [`module2_assumptions_and_limitations.md`](file:///data/processed/module2_assumptions_and_limitations.md).

### Module 3: Exploratory Data Analysis (EDA) — Planned / In Progress
- Service pattern distributions and peak vs. off-peak comparisons.
- Route-level performance correlation and outlier identification.
- Comparative transit metrics across the six cities.

---

## 3. Repository Structure

```text
RouteRanker/
│
├── README.md                                          # Project overview and documentation
├── .gitignore                                         # Git ignore configuration
├── RouteRanker.ipynb                                  # Module 2 Feature Engineering Notebook
├── AI_RouteRanker – AI-Powered Public Transit...pdf  # Project proposal and background
│
├── Python Scripts (Module 1 Pipeline)
│   ├── download_gtfs.py                               # Downloads raw GTFS zip feeds
│   ├── verify_gtfs.py                                 # Validates table presence and schemas
│   ├── dataset_inventory.py                           # Generates inventory metrics
│   ├── dataset_inventory.csv                          # GTFS table record counts summary
│   ├── milestone1.py                                  # Milestone 1 cleaning & feature pipeline
│   └── check_missing.py                               # Data validation check for nulls
│
└── data/
    ├── raw/                                           # Excluded from Git (downloadable via script)
    └── processed/                                     # Cleaned data and feature deliverables
        ├── module2_assumptions_and_limitations.md     # Engineering assumptions & limitations
        ├── module2_data_quality_report.csv            # Missing value & data quality audit
        ├── module2_feature_dictionary.csv             # Feature definitions and data types
        ├── module2_feature_engineered_dataset.csv     # Final multi-city engineered feature set
        ├── module2_final_data_quality_checks.csv      # Validation check results
        ├── module2_final_verification_report.csv      # Deliverable pass/fail verification report
        ├── module2_hourly_trip_counts_all_cities.csv  # Hourly scheduled departure counts
        ├── module2_missing_values.csv                 # Null count analysis across features
        ├── module2_route_distance_estimates.csv       # Route distance estimates
        ├── module2_route_profiles_basic_all_cities.csv# Basic route metrics
        ├── module2_route_profiles_final_all_cities.csv# Comprehensive multi-city route profiles
        ├── module2_route_service_days_all_cities.csv  # Weekly operating day indicators
        └── [City-specific cleaned routes, stops, trips, hourly activity, and service day CSVs]
```

---

## 4. Large File Handling & Storage Policy

- **Raw GTFS Feeds (`data/raw/`):** Excluded from version control due to large aggregate size (~914 MB). Feeds can be reconstructed using `python download_gtfs.py`.
- **Intermediate Stop-Times Files (`*_stop_times_time_features.csv`):** High-volume intermediate files (e.g., Mumbai ~254 MB, Chennai ~116 MB) exceed GitHub's 100 MB file limit. These files are excluded via `.gitignore` and are generated deterministically by Step 4 of `RouteRanker.ipynb`.
- **Deliverables & Aggregated Features:** All 12 Module 2 deliverables and 36 city-level processed tables are version-controlled (~23 MB total).

---

## 5. Getting Started

### Prerequisites
- Python 3.10+
- Jupyter Notebook / JupyterLab

### Installation
Clone the repository and switch to the `sravanth` branch:
```bash
git clone -b sravanth https://github.com/springboardmentor148-svg/RouteRanker-AI-Powered-Public-Transit-Route-Optimization.git
cd RouteRanker-AI-Powered-Public-Transit-Route-Optimization
```

Install required dependencies:
```bash
pip install pandas numpy requests
```

### Reproducing the Pipeline
1. **Download Raw Feeds:**
   ```bash
   python download_gtfs.py
   ```
2. **Run Verification & Inventory:**
   ```bash
   python verify_gtfs.py
   python dataset_inventory.py
   ```
3. **Execute Milestone 1 Cleaning:**
   ```bash
   python milestone1.py
   ```
4. **Execute Module 2 Feature Engineering:**
   Open and execute all cells in `RouteRanker.ipynb` to regenerate all Module 2 deliverables.
