# Module 1 — Dataset Inventory Report
**Project:** RouteRanker – AI-Powered Public Transit Route Optimization  
**Branch:** `Ayush-singh`  
**Prepared by:** Ayush Singh  
**Report date:** 19 October 2026  

---

## 1. Overview

GTFS (General Transit Feed Specification) data was collected for **8 Indian cities/transit systems**. Each city's data was downloaded from open/community sources, placed in its own folder inside `RAW DATASET/`, and loaded into Pandas DataFrames using `module1_data_collection.ipynb`.

---

## 2. City-wise Record Counts

> Row counts are taken directly from the executed notebook cell outputs.

| City / System | routes | calendar | stops | trips | stop_times | Total rows |
|---|---:|---:|---:|---:|---:|---:|
| Ahmedabad | 978 | 1 | 3,235 | 14,323 | 646,854 | **665,391** |
| Bengaluru | 4,434 | 1 | 9,960 | 57,836 | 1,540,686 | **1,612,917** |
| Davangere | 93 | 1 | 146 | 586 | 17,783 | **18,609** |
| Delhi | 1,270 | 1 | 4,192 | 50,355 | 2,250,290 | **2,306,108** |
| HDBRT (Hubli-Dharwad) | 632 | 2 | 2,332 | 8,669 | 194,059 | **205,694** |
| Mumbai | 1,609 | 1 | 10,279 | 99,080 | 2,655,026 | **2,765,995** |
| Pune | 628 | 1 | 6,745 | 10,128 | 429,302 | **446,804** |
| Rajkot | 271 | 1 | 760 | 3,192 | 94,809 | **99,033** |
| **TOTAL** | **9,915** | **9** | **37,649** | **244,169** | **7,828,809** | **8,120,551** |

---

## 3. Column Counts per File per City

> Column counts observed from DataFrame shapes `(rows, cols)`.

| City | routes cols | calendar cols | stops cols | trips cols | stop_times cols |
|---|:---:|:---:|:---:|:---:|:---:|
| Ahmedabad | 5 | 10 | 4 | 6 | 6 |
| Bengaluru | 5 | 10 | **9** | 6 | 6 |
| Davangere | 5 | 10 | 4 | **3** | **5** |
| Delhi | 5 | 10 | **6** | **4** | **5** |
| HDBRT | 5 | 10 | 4 | 5 | 6 |
| Mumbai | 5 | 10 | 4 | 5 | 6 |
| Pune | 5 | 10 | 4 | 6 | 6 |
| Rajkot | 5 | 10 | 4 | 5 | 6 |

> [!NOTE]
> Bengaluru `stops` has 9 columns (richest stop metadata). Davangere `trips` has only 3 columns. Delhi and Davangere `stop_times` have only 5 columns. These differences must be handled carefully when merging data across cities in later modules.

---

## 4. File Inventory per City Folder

### 4.1 GTFS AHEMDABAD
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 58,739 | Core | ✅ |
| `trips.txt` | 800,330 | Core | ✅ |
| `stop_times.txt` | 28,172,101 | Core | ✅ |
| `stops.txt` | 143,278 | Core | ✅ |
| `calendar.txt` | 136 | Core | ✅ |
| `agency.txt` | 404 | Optional | ➕ |
| `areas.txt` | 5,640 | Optional | ➕ |
| `stop_areas.txt` | 4,059 | Optional | ➕ |
| `fare_leg_rules.txt` | 4,489,530 | Optional | ➕ |
| `fare_products.txt` | 1,187 | Optional | ➕ |
| `feed_info.txt` | 174 | Optional | ➕ |
| `rider_categories.txt` | 101 | Optional | ➕ |
| **Total files** | **12** | | |

### 4.2 GTFS BENGALURU
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 281,498 | Core | ✅ |
| `trips.txt` | 2,719,889 | Core | ✅ |
| `stop_times.txt` | 81,380,169 | Core | ✅ |
| `stops.txt` | 920,413 | Core | ✅ |
| `calendar.txt` | 122 | Core | ✅ |
| `agency.txt` | 124 | Optional | ➕ |
| `attributions.txt` | 239 | Optional | ➕ |
| `fare_attributes.txt` | 2,653 | Optional | ➕ |
| `fare_rules.txt` | 3,389,134 | Optional | ➕ |
| `feed_info.txt` | 250 | Optional | ➕ |
| `shapes.txt` | 114,299,176 | Optional | ➕ |
| `translations.txt` | 1,350,738 | Optional | ➕ |
| **Total files** | **12** | | |

### 4.3 GTFS DAVANGARE
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 5,618 | Core | ✅ |
| `trips.txt` | 12,334 | Core | ✅ |
| `stop_times.txt` | 572,547 | Core | ✅ |
| `stops.txt` | 5,995 | Core | ✅ |
| `calendar.txt` | 128 | Core | ✅ |
| `agency.txt` | 160 | Optional | ➕ |
| `feed_info.txt` | 174 | Optional | ➕ |
| **Total files** | **7** | | |

### 4.4 GTFS DELHI ⚠️ uses `.csv` extension
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.csv` | 28,089 | Core | ✅ |
| `trips.csv` | 868,004 | Core | ✅ |
| `stop_times.csv` | 79,686,194 | Core | ✅ |
| `stops.csv` | 247,800 | Core | ✅ |
| `calendar.csv` | 122 | Core | ✅ |
| **Total files** | **5** | | |

> [!WARNING]
> Delhi is the **only city** using `.csv` extensions instead of `.txt`. It also has **no optional files** (no `agency`, `shapes`, `feed_info`, etc.). The notebook already accounts for this with separate `pd.read_csv(DELHI_GTFS_DIR / "routes.csv")` calls.

### 4.5 GTFS HDBRT (Hubli-Dharwad BRT)
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 34,776 | Core | ✅ |
| `trips.txt` | 621,453 | Core | ✅ |
| `stop_times.txt` | 9,866,257 | Core | ✅ |
| `stops.txt` | 102,808 | Core | ✅ |
| `calendar.txt` | 184 | Core | ✅ |
| `agency.txt` | 201 | Optional | ➕ |
| `feed_info.txt` | 174 | Optional | ➕ |
| **Total files** | **7** | | |

> [!NOTE]
> HDBRT is the only city with **2 calendar service records**, meaning it has two distinct service schedules (e.g., weekday and weekend).

### 4.6 GTFS MUMBAI
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 116,978 | Core | ✅ |
| `trips.txt` | 6,968,081 | Core | ✅ |
| `stop_times.txt` | 140,806,534 | Core | ✅ |
| `stops.txt` | 522,826 | Core | ✅ |
| `calendar.txt` | 136 | Core | ✅ |
| `agency.txt` | 496 | Optional | ➕ |
| `feed_info.txt` | 174 | Optional | ➕ |
| **Total files** | **7** | | |

### 4.7 GTFS PUNE
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 38,950 | Core | ✅ |
| `trips.txt` | 551,188 | Core | ✅ |
| `stop_times.txt` | 16,685,721 | Core | ✅ |
| `stops.txt` | 321,593 | Core | ✅ |
| `calendar.txt` | 128 | Core | ✅ |
| `agency.txt` | 197 | Optional | ➕ |
| `feed_info.txt` | 174 | Optional | ➕ |
| `shapes.txt` | 8,093,984 | Optional | ➕ |
| **Total files** | **8** | | |

### 4.8 GTFS RAJKOT
| File | Size (bytes) | Type | Required? |
|---|---:|---|---|
| `routes.txt` | 15,995 | Core | ✅ |
| `trips.txt` | 135,561 | Core | ✅ |
| `stop_times.txt` | 3,503,938 | Core | ✅ |
| `stops.txt` | 31,593 | Core | ✅ |
| `calendar.txt` | 128 | Core | ✅ |
| `agency.txt` | 170 | Optional | ➕ |
| `feed_info.txt` | 174 | Optional | ➕ |
| **Total files** | **7** | | |

---

## 5. Optional Files Availability Matrix

| Optional File | Ahmedabad | Bengaluru | Davangere | Delhi | HDBRT | Mumbai | Pune | Rajkot |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `agency.txt` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `feed_info.txt` | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| `shapes.txt` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| `fare_attributes.txt` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `fare_rules.txt` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `fare_leg_rules.txt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `fare_products.txt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `areas.txt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `stop_areas.txt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `translations.txt` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `attributions.txt` | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `rider_categories.txt` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## 6. File Size Summary (Core Files Only)

| City | stop_times size | trips size | stops size | routes size | Total core size (approx.) |
|---|---:|---:|---:|---:|---:|
| Ahmedabad | 28.2 MB | 800 KB | 143 KB | 59 KB | ~29.2 MB |
| Bengaluru | 81.4 MB | 2.7 MB | 920 KB | 281 KB | ~85.3 MB |
| Davangere | 573 KB | 12 KB | 6 KB | 6 KB | ~597 KB |
| Delhi | 79.7 MB | 868 KB | 248 KB | 28 KB | ~80.8 MB |
| HDBRT | 9.9 MB | 621 KB | 103 KB | 35 KB | ~10.7 MB |
| Mumbai | **140.8 MB** | **7.0 MB** | 523 KB | 117 KB | **~148.4 MB** |
| Pune | 16.7 MB | 551 KB | 322 KB | 39 KB | ~17.6 MB |
| Rajkot | 3.5 MB | 136 KB | 32 KB | 16 KB | ~3.7 MB |

> [!TIP]
> `stop_times` is by far the largest file in every city. Mumbai's `stop_times.txt` alone is **140.8 MB** — memory management (chunked reading or dtype optimization) should be considered for this city in later modules.

---

## 7. Data Sources

| City Folder | Source | Download Date |
|---|---|---|
| GTFS AHEMDABAD | FOSS United / CROLA project | 16 Oct 2026 |
| GTFS BENGALURU | BMTC unofficial GTFS (Vonter, GitHub) | 16 Oct 2026 |
| GTFS DAVANGARE | FOSS United / CROLA project | 16 Oct 2026 |
| GTFS DELHI | Delhi Open Transit Data portal | 16 Oct 2026 |
| GTFS HDBRT | FOSS United / CROLA project | 16 Oct 2026 |
| GTFS MUMBAI | FOSS United / CROLA project | 16 Oct 2026 |
| GTFS PUNE | FOSS United / CROLA project | 16 Oct 2026 |
| GTFS RAJKOT | FOSS United / CROLA project | 16 Oct 2026 |

---

## 8. Key Observations & Flags for Future Modules

| # | Observation | Impact |
|---|---|---|
| 1 | **Mumbai** has the largest `stop_times` (2.65M rows, 140 MB) | May need chunked reading in Modules 2+ |
| 2 | **Delhi** uses `.csv` extension instead of `.txt` | Notebook already handles this; any new scripts must too |
| 3 | **Bengaluru** stops has 9 columns vs. 4 for most cities | Extra stop metadata available; column alignment needed when merging |
| 4 | **Davangere** trips has only 3 columns | Missing fields (e.g. `shape_id`, `direction_id`) — impute or ignore in joins |
| 5 | **HDBRT** has 2 calendar service records | Two service schedules — filter or union logic needed |
| 6 | **Shapes data** only available for Bengaluru and Pune | Route geometry analysis limited to these two cities |
| 7 | **Fare data** available only for Ahmedabad and Bengaluru | Cross-city fare comparison not possible with current data |
| 8 | **Delhi** has no optional files at all | No agency, shapes, or feed_info metadata available |
| 9 | All 5 core GTFS files loaded successfully for all 8 cities | ✅ Module 1 goal achieved |
| 10 | Total dataset: ~8.12M rows across all cities combined | Significant data volume — production pipeline needs batching |

---

## 9. Module 1 Completion Checklist

- [x] Collect GTFS data for all available cities (8 of 23 targeted)
- [x] Organise files into one folder per city under `RAW DATASET/`
- [x] Load all 5 core GTFS files with Pandas for all 8 cities
- [x] Verify record counts (rows × columns) for each file
- [x] Identify optional files present per city
- [x] Document data sources and download dates
- [x] Dataset inventory report produced (`module1_dataset_inventory.md`)

---

*Report generated from notebook outputs and file system inspection on 19 October 2026.*
