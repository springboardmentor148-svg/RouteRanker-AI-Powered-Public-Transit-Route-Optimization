[README.md](https://github.com/user-attachments/files/33596408/README.md)
# Indian City Transit Data (GTFS) - Milestone 1: Data Collection and Feature Engineering

## Overview

This repository holds the Module 1 work of Milestone 1: collecting GTFS transit data for major Indian cities, organizing it into a clear folder structure, loading it with Python and Pandas, and inspecting its structure and quality. The goal of this stage is to understand what the data represents before any feature engineering or machine-learning work begins. No models have been built.

The milestone brief asks for GTFS datasets from Lepton Software for 23 major Indian cities. That commercial bundle was **not** obtained. Instead, public GTFS feeds were collected for **7 of the 23 cities** (Pune, Bengaluru, Mumbai, Hyderabad, Chennai, Kolkata and Delhi), giving 17,921 route records and 283,807 GTFS trips. For the other 16 cities no downloadable feed could be found, so there is no data for them and none was invented.

## Milestone Plan

Week 1 covers collecting the GTFS datasets, extracting and loading the essential files (routes.txt, trips.txt, stop\_times.txt, stops.txt and calendar.txt), and performing an initial inspection of the dataset structure. Week 2 covers cleaning the data (missing values and erroneous entries), engineering time-based features such as hour of day and weekday versus weekend, aggregating stop usage to passengers per route per hour, and building basic route profiles with route length and trip frequency.

Status: the Week 1 work is done for the 7 cities that have data. The Week 2 work has not been started (see Next Steps).

## Module 1 Tasks

**Task 1 - Explore and collect the dataset.** The dataset sources were identified, the files that exist were downloaded, and the cities, file formats and access limitations were recorded (see Dataset Source Documentation). Files are organized in named folders: `gtfs/` for the original feeds, `integrated/` for derived joins, and `inventory/` for the inventory outputs.

**Task 2 - Understand the dataset structure.** Every file was opened and its column names and number of records recorded in the inventory. The relationship between the files is explained in the section on how the GTFS files are connected. Data types and sample values per column are not yet recorded in the notebook (see Deliverables Checklist).

**Task 3 - Load the files using Python.** Pandas is used to read the CSV and GTFS text files into DataFrames. A short loading example is given in Setup Instructions.

**Task 4 - Inspect data quality.** Missing values, duplicate identifiers, missing required files, unusual time values and unlinked identifiers were checked and logged (see Data-Quality Observations).
**Task 5** **-** a table of routes.txt, trips.txt, stop\_times.txt, stops.txt and calendar.txt showing their key columns and how each joins to the next. It also gives the route → trips → stop\_times → stops path and notes where shapes.txt and frequencies.txt fit in.

**Task 6 -** a per-city inventory table with the route-list file and record count, the GTFS zip, counts of routes, trips, stop times and stops, missing files, and the main data-quality concerns. It points to inventory/dataset\_inventory.xlsx for the full detail. The 16 cities with no data are named in the Overview, and each city’s row is kept separate.

## Tools and Technologies

Python with Pandas is used for loading and inspecting the data, with NumPy used lightly. The notebook runs in Jupyter Notebook (Google Colab also works if the folder is uploaded and the working directory is set to it). Excel or a similar spreadsheet application can be used for preliminary inspection of `inventory/dataset\_inventory.xlsx` and the CSV files. The openpyxl package writes the Excel inventory. Git and GitHub are to be used for the code according to the project repository guidelines; this folder has not been pushed to a repository as part of this work.

## Dataset Source Documentation

The list of 23 cities comes from the supplied `INDIA\_23\_CITIES\_GTFS\_Coverage\_Report.pdf`, which states that it is a source and coverage package and not a reproduction of the commercial Lepton 23-city bundle. The Pune route list is the supplied `pmpml\_routes.csv`, copied unchanged. All other data was downloaded from public GitHub repositories, with no login or API key needed.

|City / system|Source repository|File obtained|Format|Licence stated by source|
|-|-|-|-|-|
|Pune route list|supplied by you|`pmpml\_routes.csv`|CSV|-|
|Pune GTFS|`croyla/pmpml-gtfs`|`pmpml\_gtfs.zip` (community feed)|GTFS zip|MIT-style|
|Bengaluru (BMTC)|`Vonter/bmtc-gtfs`|`gtfs/bmtc.zip` (unofficial, from the Namma BMTC app)|GTFS zip|ODbL|
|Mumbai region|`croyla/mumbai-gtfs`|`gtfs.zip` (community)|GTFS zip|MIT-style|
|Hyderabad bus (TGSRTC)|`surajreddykarra/interactive-gtfs`|`data/Telangana\_opendata\_gtfs\_TGSRTC\_27\_December\_2025.zip`|GTFS zip|none stated|
|Hyderabad metro (HMRL)|`surajreddykarra/interactive-gtfs`|`data/Telangana\_opendata\_gtfs\_hmrl\_03\_January\_2026.zip`|GTFS zip|none stated|
|Chennai (MTC bus)|`mohammadamir0762-arch/Chennai\_transit`|`otp/chennai/mtc-bus-gtfs.zip`|GTFS zip|none stated|
|Kolkata (bus + metro)|`arkodeepg/calcutta-transport`|`gtfs/` folder, filtered to bus and metro routes|GTFS text files|ODbL|
|Delhi|`ss-sparsh/BusRoutes`|`routes.txt`, `trips.txt`, `stop\_times.txt`, `stops.txt`|GTFS text files|none stated|

Access and download limitations: the Lepton Software bundle was not available; the official Delhi feed (otd.delhi.gov.in) could not be reached from the environment used, so Delhi comes from a GitHub mirror and was not compared with the official feed; Bengaluru, Mumbai, Pune and Chennai are unofficial community feeds; several sources carry no licence file; and the Kolkata zip keeps only bus and metro routes, with the full original feed available in its source repository. Details for every city are in `city\_status\_23.csv`.

## Cities Covered

|City|Systems|Route records|GTFS routes|GTFS trips|GTFS stop\_times|GTFS stops|
|-|-|-|-|-|-|-|
|Pune|PMPML|1,030|628|10,128|429,302|6,745|
|Bengaluru|BMTC|7,493|4,434|57,836|1,540,686|9,960|
|Mumbai|BEST / TMT / KDMT / VVMT|1,609|1,609|99,080|2,655,026|10,279|
|Hyderabad|TGSRTC bus + HMRL metro|2,025|1,158|51,924|1,279,491|6,635|
|Chennai|MTC bus|4,611|4,611|47,047|1,360,443|5,477|
|Kolkata|Bus + Metro|610|608|1,230|17,858|1,234|
|Delhi|DTC / DIMTS buses|543|543|16,562|674,909|3,465|

No data was obtained for: Ahmedabad, Bhopal, Bhubaneswar, Coimbatore, Indore, Jaipur, Kanpur, Kochi, Lucknow, Nagpur, Panaji/Goa, Patna, Rajkot, Surat, Vadodara, Visakhapatnam.

## Repository Structure

```
india\_transit\_routes/
|-- README.md                          this file
|-- dataset\_inventory.ipynb            notebook that builds the inventory
|-- pune\_pmpml\_routes.csv              route lists, one per city, in the PMPML layout
|-- bengaluru\_bmtc\_routes.csv            (Route ID | Route Description | Route Description <language> | Kilometer)
|-- mumbai\_region\_routes.csv
|-- hyderabad\_routes.csv
|-- chennai\_mtc\_routes.csv
|-- kolkata\_routes.csv
|-- delhi\_routes.csv
|-- all\_cities\_routes\_combined.csv     the 7 route lists stacked, with City, System and Km Method
|-- city\_status\_23.csv                 status and source of all 23 cities
|-- gtfs\_file\_availability.csv         record counts and link checks per GTFS feed
|-- crosswalk\_combined\_to\_gtfs.csv     link from each route-list row to a GTFS route
|-- gtfs/                              8 GTFS zips (routes, trips, stop\_times, stops, calendar, shapes, ...)
|-- integrated/                        route lists joined with GTFS, per city
|   |-- <city>\_routes\_integrated.csv
|   |-- <city>\_trips\_and\_stops\_integrated.zip
|   `-- all\_cities\_routes\_integrated.csv
`-- inventory/                         output of the notebook
    |-- dataset\_inventory.xlsx
    `-- city\_summary.csv, file\_inventory.csv, gtfs\_file\_matrix.csv, data\_quality\_log.csv, column\_dictionary.csv
```

The original data is kept in `gtfs/` and in the supplied Pune route list. Everything in `integrated/`, the route lists for the other six cities, and the combined files are derived from it and never overwrite it. The only changes to a downloaded feed are the Kolkata filtering and the Delhi file selection described above.

## How the GTFS Files Are Connected

A GTFS feed is a set of related tables joined by identifier columns:

```
agency --< routes --< trips --< stop\_times >-- stops
                        |
                        |-- service\_id --> calendar
                        `-- shape\_id   --> shapes   (optional)
```

`routes.txt` lists each route once, identified by `route\_id`. `trips.txt` lists every scheduled run of a route; each trip carries the `route\_id` it belongs to, a `service\_id` that says on which days it runs, and sometimes a `direction\_id` and a `shape\_id`. `stop\_times.txt` lists, for every `trip\_id`, the ordered stops it serves (`stop\_sequence`) with arrival and departure times, and each row points to a `stop\_id`. `stops.txt` holds the name and latitude/longitude of every stop. `calendar.txt` turns a `service\_id` into weekday flags (monday to sunday) and a start and end date. `shapes.txt` (optional) draws the route line and `frequencies.txt` (optional) replaces explicit timetables with a departure every N seconds, linked through `trip\_id`. `agency.txt` names the operator that runs each route.

So the path from a route to its stops is routes -> trips (by `route\_id`) -> stop\_times (by `trip\_id`) -> stops (by `stop\_id`), and the days a trip runs come from trips -> calendar (by `service\_id`). No broken links between these tables were found in any of the 8 feeds; for Delhi the calendar link could not be checked because the file is missing. The supplied route lists are joined to these tables through `crosswalk\_combined\_to\_gtfs.csv`.

## Dataset Inventory

`inventory/dataset\_inventory.xlsx` summarizes the collected data. The `City\_Summary` sheet has one row for each of the 23 cities, with its files, record counts, missing data and main concerns. `File\_Inventory` lists all 113 files and files inside zips with record counts, column counts and important columns. `GTFS\_File\_Matrix` shows which required and optional GTFS files each feed has, `Data\_Quality\_Log` holds the numbered data-quality entries, and `Column\_Dictionary` explains the important columns. The same sheets are saved as CSV files in `inventory/`.

## Data-Quality Observations

The full log has 67 numbered entries (12 high, 15 medium, 25 low and 15 passed checks) in `inventory/data\_quality\_log.csv`. The main findings, grouped by the checks Task 4 asks for:

* **Missing or empty values:** Kilometer is blank for 543 of 610 Kolkata routes (most bus stops have no coordinates), 497 of 1,609 Mumbai routes, 677 of 4,611 Chennai routes, and smaller numbers elsewhere. The local-language description column is empty for every city except Pune.
* **Duplicate records:** no duplicate Route IDs were found in any of the 7 route lists.
* **Missing required files:** Delhi has no `agency.txt` and no `calendar.txt`, so its service days are unknown.
* **Unusual time or date values:** 40,434 of 51,924 Hyderabad trips (78%) have a duration over 24 hours; Delhi has 125 trips with negative durations and 147 trips with no stop times; Mumbai's median trip duration is 9 minutes, which looks implausible for a city bus. Kolkata bus times are modelled by the source, not published timetables.
* **Invalid or inconsistent identifiers:** 494 Mumbai routes and 677 Chennai routes have no trips. For Pune, 793 of the 1,030 route-list rows have no matching route in the community GTFS, and 5,389 of its 10,128 trips do not belong to any route on your list.
* **Unexpected data types:** not yet profiled column by column.

## Deliverables Checklist

|#|Deliverable|Status|Where|
|-|-|-|-|
|1|Dataset source documentation|Done|Dataset Source Documentation above, `city\_status\_23.csv`|
|2|Organized dataset, original data unaltered|Done|`gtfs/`, folder structure above|
|3|Python notebook loading and inspecting files with Pandas|Done: the notebook loads the CSV and zip files with Pandas and builds the inventory, but does not yet show raw GTFS tables loaded as DataFrames with data types and sample values|`dataset\_inventory.ipynb`|
|4|Dataset inventory|Done|`inventory/dataset\_inventory.xlsx`|
|5|Data-quality observations|Done: file-level and record-level issues are logged; column-by-column null, duplicate and data-type profiling of the raw GTFS tables is not yet included|`inventory/data\_quality\_log.csv`|
|6|Relationship documentation|Done|How the GTFS Files Are Connected above|

## Setup Instructions

**Locating the data.** All data is already in this folder, laid out as in Repository Structure. Start with `inventory/dataset\_inventory.xlsx` to see what exists for each city, then open the city's route list in the root folder or its GTFS zip in `gtfs/`.

**Obtaining the data again.** Open `https://github.com/<repository>` for the repository in the source table, open the file path shown, and download the raw file (or clone the repository). Save the zip in `gtfs/` with the same name as in this folder. For a city that has no data yet, look for the operator's GTFS on its official open-data page, data.gov.in, or a GTFS directory such as the Mobility Database or Transitland; availability is not guaranteed. Save it in `gtfs/` as `<city>\_<operator>\_gtfs.zip` and add the city to `CITY\_REGISTRY` and `FEEDS` in the first section of the notebook.

**Running the notebook.** You need Python 3.9 or newer and the packages pandas, openpyxl and jupyter.

1. Keep the folder structure unchanged, with the notebook next to `all\_cities\_routes\_combined.csv`.
2. Open a terminal in the folder: `cd path/to/india\_transit\_routes`
3. Install the packages: `pip install pandas openpyxl jupyter`
4. Start the notebook: `jupyter notebook dataset\_inventory.ipynb` (in VS Code, open the file, choose a Python kernel and click Run All).
5. Run every cell from top to bottom (Kernel -> Restart and Run All). It takes about one to two minutes because the large stop\_times files are counted line by line.
6. Open the results in `inventory/`: `dataset\_inventory.xlsx` or the matching CSV files.

**Loading a GTFS file with Pandas.** A GTFS zip holds several files, so open it with `zipfile` and read the file you need. Reading identifiers as text keeps leading zeros intact:

```python
import zipfile
import pandas as pd

with zipfile.ZipFile("gtfs/bengaluru\_bmtc\_gtfs.zip") as z:
    routes = pd.read\_csv(z.open("routes.txt"), dtype=str)
    trips = pd.read\_csv(z.open("trips.txt"), dtype=str)

print(routes.shape, list(routes.columns))
```

**Troubleshooting.** If the notebook stops with "Run this notebook from the india\_transit\_routes folder", it is not next to the data files; move it or start Jupyter from the data folder. If Python reports `ModuleNotFoundError` for openpyxl or pandas, repeat step 3. If the TOTAL row on the `City\_Summary` sheet looks empty in a viewer, open the workbook once in Excel or LibreOffice so the SUM formulas calculate; the delivered copy already holds the values, and the CSV files contain no formulas.

## Output

Running the notebook writes `dataset\_inventory.xlsx` and five CSV files to `inventory/`: the city summary, the file inventory with record counts and important columns, the GTFS file matrix, the data-quality log, and the column dictionary. Every table has a City column and a System or feed column so each city's data stays distinguishable.

## Limitations

Only 7 of the 23 cities have data, and none of it comes from the Lepton Software bundle. Several feeds are unofficial community products. Kilometer values outside Pune are calculated from route shapes or stop-to-stop distances and are approximate: on 217 Pune routes the median was within about 2-6% of PMPML's own values, but only about 45% of routes were within 10%. Hyderabad bus times and Mumbai trip durations look unreliable in the source feeds. Kolkata bus times are modelled. Delhi has no calendar and its completeness is unverified. The Pune GTFS covers only part of the supplied PMPML route list. The delivered GTFS feeds describe schedules and stop locations only and contain no passenger counts.

## Next Steps

Week 2 starts with cleaning the data (handling the missing values and erroneous entries logged here) and engineering time-based features such as hour of day and weekday versus weekend from the stop times and calendar. Route length and trip counts per route already exist in the integrated route tables and can seed the route profiles. The Week 2 task of aggregating passengers per route per hour needs ridership data, which none of the collected feeds contain, so a separate ridership source or an agreed proxy such as trips per hour will be needed. The notebook should also be extended with column-level profiling of the raw GTFS tables to complete deliverables 3 and 5.

## Academic Context

This work is Module 1 of Milestone 1 (Data Collection and Feature Engineering) of the project. It covers data collection, organization, loading and inspection only, and no machine-learning models have been built at this stage.

## License

The project license is to be set according to the repository guidelines. The data keeps the licences of its sources (see the source table): ODbL for Bengaluru and Kolkata, MIT-style for Mumbai and the Pune GTFS, and no licence file for the Hyderabad, Chennai and Delhi sources. Check each licence before redistributing the data.

