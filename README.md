# RouteRanker – AI-Powered Public Transit Route Optimization

## Module 1: Data Collection and Dataset Understanding

RouteRanker is a project that analyses public transit data from Indian cities to find inefficient bus routes (for example overlapping routes, uneven service frequency and possible underutilisation) and, in later modules, to recommend improvements through a Streamlit dashboard.

This branch contains **Module 1** only. Its goal is to collect the GTFS (General Transit Feed Specification) data, load it with Python/Pandas, and understand its structure. No cleaning, feature engineering or machine learning is done at this stage.

---

## 1. What has been collected

GTFS data was collected for **8 cities/systems**, not the 23 listed in the original project document. The Lepton Software dataset named in the project document is a commercial listing, so the free sources below were used instead.

Record counts below come from the notebook output (rows in each file):

| City / system | routes | calendar | stops | trips | stop_times |
|---|---:|---:|---:|---:|---:|
| Ahmedabad | 978 | 1 | 3,235 | 14,323 | 646,854 |
| Bengaluru | 4,434 | 1 | 9,960 | 57,836 | 1,540,686 |
| Davangere | 93 | 1 | 146 | 586 | 17,783 |
| Delhi | 1,270 | 1 | 4,192 | 50,355 | 2,250,290 |
| HDBRT | 632 | 2 | 2,332 | 8,669 | 194,059 |
| Mumbai | 1,609 | 1 | 10,279 | 99,080 | 2,655,026 |
| Pune | 628 | 1 | 6,745 | 10,128 | 429,302 |
| Rajkot | 271 | 1 | 760 | 3,192 | 94,809 |

All five required files (`routes`, `trips`, `stop_times`, `stops`, `calendar`) loaded successfully for every city.

Notes on the files:
- The Delhi data is in `.csv` files (`routes.csv`, `trips.csv`, and so on). All other cities use `.txt` files. Both are comma-separated, so `pd.read_csv()` reads either.
- Some cities include extra GTFS files (for example `agency.txt`, `feed_info.txt`, `areas.txt`, `fare_products.txt`). The Ahmedabad folder has several of these. Which optional files exist for each city is documented in the dataset inventory report.
- The number of columns differs between cities (for example Davangere's `trips.txt` has 3 columns and Bengaluru's has 6), so a column that exists for one city may not exist for another.

---

## 2. Data sources and how the data was collected

The data was gathered from public websites, GitHub repositories and open-data platforms. Raw files are **not** committed to this repository because they are large (several `stop_times` files have over a million rows). Use the links below to obtain them again.

### Primary source for several cities

**FOSS United – CROLA GTFS project**
https://fossunited.org/grants/directory/crola

This grant project page describes open GTFS feeds for Indian cities, including Mumbai, Pune, Ahmedabad, Rajkot, Hubli-Dharwad and Davangere. Follow the data/repository links on that page to download the feeds.

### Other sources consulted

| Source | Link | Used for |
|---|---|---|
| Delhi Open Transit Data portal (static GTFS, buses) | https://otd.delhi.gov.in/data/static/ | Delhi bus data |
| Delhi GTFS static (NIUA DataSpace mirror, separate files) | https://ndp.ckan.civicdatalab.in/dataset/delhi-gtfs-static | Delhi, alternative download |
| BMTC GTFS (unofficial, Vonter) | https://github.com/Vonter/bmtc-gtfs/raw/refs/heads/main/gtfs/bmtc.zip | Bengaluru buses |
| BMRCL Namma Metro GTFS (unofficial) | https://raw.githubusercontent.com/Vonter/bmrcl-gtfs/main/gtfs/bmrcl.zip | Bengaluru metro (reference) |
| Karnataka official transport data portal | https://tdh.dult-karnataka.com | Bengaluru official data |
| Chartr open GTFS datasets | https://chartr.in/products/gtfs/ | Delhi, Pune, Rajkot |
| MobilityDatabase | https://mobilitydatabase.org | Feed lookup |
| TUMI DataHub (Hyderabad) | https://hub.tumidata.org/dataset/gtfs-hyderabad/resource/03ed6e43-2e33-4a02-bb13-6c2bab626651 | Hyderabad (reference, not in this dataset) |
| Lepton Software India transit data (project document source) | https://datarade.ai/data-products/india-transit-data-railways-metro-and-public-buses-routes-lepton-software | Investigated; commercial, not used |

### Which source each city came from

> **TODO (team member to confirm before submitting):** fill in the exact source and download date for each city. This table should reflect what was actually downloaded.

| City folder | Source used | Download date |
|---|---|---|
| GTFS AHEMDABAD | _confirm_ | _fill in_ |
| GTFS BENGALURU | _confirm (for example the BMTC GTFS above)_ | _fill in_ |
| GTFS DAVANGARE | _confirm_ | _fill in_ |
| GTFS DELHI | _confirm (for example Delhi OTD portal)_ | _fill in_ |
| GTFS HDBRT | _confirm_ | _fill in_ |
| GTFS MUMBAI | _confirm_ | _fill in_ |
| GTFS PUNE | _confirm_ | _fill in_ |
| GTFS RAJKOT | _confirm_ | _fill in_ |

Process: for each city, the GTFS feed was located on one of the sources above, downloaded (as a zip or as individual files), unzipped into its own `GTFS <CITY>` folder, and left unmodified.

---

## 3. Folder structure

The notebook expects the city folders to sit in the same folder as the notebook:

```
RAW DATASET/
│
├── module1_data_collection.ipynb
│
├── GTFS AHEMDABAD/
│   ├── routes.txt
│   ├── trips.txt
│   ├── stop_times.txt
│   ├── stops.txt
│   ├── calendar.txt
│   └── (other optional GTFS files)
├── GTFS BENGALURU/
├── GTFS DAVANGARE/
├── GTFS DELHI/          <- note: .csv files instead of .txt
├── GTFS HDBRT/
├── GTFS MUMBAI/
├── GTFS PUNE/
└── GTFS RAJKOT/
```

The original downloaded files in these folders are never edited.

---

## 4. How to set up and run

### Requirements
- Python 3.10 or newer (the notebook was run on Python 3.14.3 in a virtual environment)
- `pandas`
- `numpy`
- Jupyter (VS Code with the Jupyter extension, Jupyter Notebook, or JupyterLab)

### Steps

1. **Clone the repository** and switch to this branch:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   git checkout <branch-name>
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install pandas numpy jupyter ipykernel
   ```

4. **Download the raw data** from the sources in Section 2 and place each city's files in its own `GTFS <CITY>` folder, as shown in Section 3.

5. **Open the notebook** `module1_data_collection.ipynb` in VS Code (select your `.venv` as the kernel) or run `jupyter notebook`.

6. **Run all cells** (Run All). Each cell loads one city and prints the shape (rows, columns) of its five files.

### How the loading works

The notebook uses Pandas to read each file into a DataFrame:

```python
from pathlib import Path
import pandas as pd

GTFS_DIR = Path("GTFS AHEMDABAD")

datasets = {
    "routes":     pd.read_csv(GTFS_DIR / "routes.txt"),
    "calendar":   pd.read_csv(GTFS_DIR / "calendar.txt"),
    "stops":      pd.read_csv(GTFS_DIR / "stops.txt"),
    "trips":      pd.read_csv(GTFS_DIR / "trips.txt"),
    "stop_times": pd.read_csv(GTFS_DIR / "stop_times.txt"),
}

{name: frame.shape for name, frame in datasets.items()}
```

The same pattern is repeated for each city. For Delhi the file extension is `.csv`, so the notebook reads `routes.csv`, `trips.csv` and so on.

If a path error appears, check that the notebook is in the same folder as the `GTFS ...` folders, or change the folder path at the top of the cell.

---

## 5. Understanding the five GTFS files

| File | What it contains |
|---|---|
| `routes.txt` | The list of transit routes, each with a `route_id` |
| `trips.txt` | Individual scheduled trips; each trip belongs to a route (`route_id`) and a service schedule (`service_id`) |
| `stop_times.txt` | Arrival and departure time at each stop for every trip, with stop sequence |
| `stops.txt` | Stop locations (name and latitude/longitude) |
| `calendar.txt` | The days of the week each service runs and its start and end dates |

How the files connect:

```
routes.route_id  ──►  trips.route_id
trips.trip_id    ──►  stop_times.trip_id
stop_times.stop_id ─►  stops.stop_id
trips.service_id ──►  calendar.service_id
```

---

## 6. Limitations

- **Only 8 cities** were collected, not the 23 mentioned in the project document.
- **GTFS has no passenger data.** It describes scheduled routes, stops, trips and timings. It does not contain passenger counts, bus occupancy or live traffic. No ridership values have been created or assumed in this module. If later modules need ridership, an additional data source will be required, to be decided with the mentor.
- **Scheduled data only.** The data shows planned service, not actual operations. A route with fewer scheduled trips should not be assumed to be inefficient.
- **Some feeds are unofficial or community-built** (see Section 2), and their quality and update dates vary by city.
- **Different column sets per city.** Some cities have fewer columns than others, which will matter when the data is merged in later modules.

---

## 7. Module 1 status

- [x] Collect GTFS data for the available cities
- [x] Organise files into one folder per city
- [x] Load the five required files with Pandas for all 8 cities
- [ ] Inspect structure in detail (columns, data types, sample values)
- [ ] Data-quality inspection (missing values, duplicates, invalid IDs, unusual times and dates), documented only, with no data deleted or altered
- [ ] Relationship checks between files
- [ ] Dataset inventory report (`reports/module1_dataset_inventory.md`)

---

## 8. Next steps (later modules)

After Module 1 is reviewed: feature engineering, EDA, preprocessing, clustering and classification, route suggestions and a Streamlit dashboard, as described in the project document.

---

## Team

_Add team member names and mentor here._
