# Module 1 – Dataset source documentation

_Generated 2026-10-18 by `run_module1.py`._

## Official source named in the project document: Lepton Software (Datarade)

* Listing: https://datarade.ai/data-products/india-transit-data-railways-metro-and-public-buses-routes-lepton-software
* Description on the page: GTFS for **23 Indian cities** plus Indian Railways.
* **Accessibility finding:** this is a *commercial* listing. The page gives no download link; pricing is only 'by contacting Lepton Software' (delivery via S3/SFTP/API after purchase), and the sample table shown on the page is masked. **The Lepton dataset was therefore NOT obtained**, and the page does not list which 23 cities are included.
* We have **not** collected 23 cities. We have not verified that Lepton data would contain every required file.

## What was actually collected instead (open GTFS feeds, same file format)

| City | Operator | Downloaded file size (MB) | Direct URL | Publisher / provenance |
|---|---|---|---|---|
| ahmedabad | AMTS + Janmarg BRTS | 4.64 | https://github.com/croyla/amd-gtfs/raw/main/gtfs.zip | Community GitHub repo (croyla/amd-gtfs), compiled from amts.co.in and ahmedabadbrts.org |
| bengaluru | BMTC | 44.39 | https://github.com/Vonter/bmtc-gtfs/raw/main/gtfs/bmtc.zip | Unofficial GTFS built by a community project (Vonter/bmtc-gtfs); not published by BMTC itself |
| chennai | Chennai unified feed (buses + others) | 9.82 | https://raw.githubusercontent.com/ungalsoththu/ChennaiGTFS/main/data/chennai-unified-gtfs.zip | Community repo (ungalsoththu/ChennaiGTFS); listed on MobilityDatabase as mdb-3360 |
| delhi | Delhi buses (DTC / cluster) | 19.78 | https://raw.githubusercontent.com/transitland/gtfs-archives-not-hosted-elsewhere/3db26c0092b6efeb1886a99b4fc0765122b0282b/delhi-bus.zip | Archived copy of the Delhi Open Transit Data feed in the Transitland archive; service dates are old (see calendar check) |
| hyderabad | TGSRTC | 10.55 | https://files.mobilitydatabase.org/mdb-3361/latest.zip | MobilityDatabase feed mdb-3361 (TGSRTC also lists open data at tgsrtc.telangana.gov.in/open-data) |
| kochi | Kochi buses and boats | 5.48 | https://jungle-bus.github.io/KochiTransport/KochiTransport.zip | Community project (Jungle Bus / KochiTransport); MobilityDatabase mdb-1835 |
| pune | PMPML | 4.86 | https://files.mobilitydatabase.org/mdb-3137/latest.zip | MobilityDatabase feed mdb-3137 |

**Cities from the project plan with no open GTFS feed found:** Mumbai (BEST), Rajkot, Hubli-Dharwad (checked MobilityDatabase and public repositories; nothing usable). Delhi's official feed needs an API key; the archived copy above was used.

## Folder layout
```
data/raw/<city>/<city>_gtfs.zip   <- original download, untouched
data/raw/<city>/*.txt             <- same files extracted by run_module1.py (read-only use)
data/processed/                   <- reserved for Module 2 outputs
```

## How to obtain the data again
`python download_data.py` (all) or `python download_data.py pune kochi`; if a URL fails, download the ZIP manually from the link above into `data/raw/<city>/`.

## Access / licence limitations
* All files are third-party feeds; check each publisher's licence before redistributing. Raw files are therefore **not committed to Git** (see `.gitignore`).
* Bengaluru and Ahmedabad feeds are community-compiled, not operator-published. Kochi and Delhi service dates are old.
