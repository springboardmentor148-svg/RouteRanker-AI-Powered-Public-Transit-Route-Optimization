"""Module 1 runner (read-only): extract raw GTFS, inspect every city, write the reports.

    python run_module1.py            # all cities found in data/raw/
    python run_module1.py pune kochi # selected cities

Outputs (reports/):  module1_data_sources.md, module1_dataset_inventory.md, module1_relationships.md,
                     module1_file_inventory.csv, module1_quality_issues.csv
Original downloaded ZIPs are never modified; only their .txt files are extracted next to them.
"""
import glob, os, sys, datetime
import pandas as pd
from src import inspect_gtfs as ig

RAW, REP = "data/raw", "reports"
SKIP = {"sample_city", "demo"}  # synthetic demo data is not part of the dataset
SOURCES = {  # what we actually obtained and from where (Lepton/Datarade could NOT be accessed - see sources report)
    "ahmedabad": ("AMTS + Janmarg BRTS", "https://github.com/croyla/amd-gtfs/raw/main/gtfs.zip",
                  "Community GitHub repo (croyla/amd-gtfs), compiled from amts.co.in and ahmedabadbrts.org"),
    "bengaluru": ("BMTC", "https://github.com/Vonter/bmtc-gtfs/raw/main/gtfs/bmtc.zip",
                  "Unofficial GTFS built by a community project (Vonter/bmtc-gtfs); not published by BMTC itself"),
    "chennai": ("Chennai unified feed (buses + others)", "https://raw.githubusercontent.com/ungalsoththu/ChennaiGTFS/main/data/chennai-unified-gtfs.zip",
                "Community repo (ungalsoththu/ChennaiGTFS); listed on MobilityDatabase as mdb-3360"),
    "delhi": ("Delhi buses (DTC / cluster)", "https://raw.githubusercontent.com/transitland/gtfs-archives-not-hosted-elsewhere/3db26c0092b6efeb1886a99b4fc0765122b0282b/delhi-bus.zip",
              "Archived copy of the Delhi Open Transit Data feed in the Transitland archive; service dates are old (see calendar check)"),
    "hyderabad": ("TGSRTC", "https://files.mobilitydatabase.org/mdb-3361/latest.zip",
                  "MobilityDatabase feed mdb-3361 (TGSRTC also lists open data at tgsrtc.telangana.gov.in/open-data)"),
    "kochi": ("Kochi buses and boats", "https://jungle-bus.github.io/KochiTransport/KochiTransport.zip",
              "Community project (Jungle Bus / KochiTransport); MobilityDatabase mdb-1835"),
    "pune": ("PMPML", "https://files.mobilitydatabase.org/mdb-3137/latest.zip", "MobilityDatabase feed mdb-3137"),
}


def md_table(df):
    if df.empty:
        return "_none_\n"
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |")
    return "\n".join(lines) + "\n"


def main(cities):
    os.makedirs(REP, exist_ok=True)
    today = pd.Timestamp.today().normalize()
    found = {os.path.basename(d): d for d in sorted(glob.glob(f"{RAW}/*")) if os.path.isdir(d)
             and os.path.basename(d) not in SKIP}
    cities = cities or list(found)
    inv, qual, rel, zips = [], [], [], {}
    for c in cities:
        d = found.get(c)
        if d is None:
            print(f"[{c}] folder not found in {RAW}/ - skipped"); continue
        z = glob.glob(f"{d}/*.zip")
        zips[c] = round(os.path.getsize(z[0]) / 1e6, 2) if z else None
        print(f"[{c}] {ig.ensure_extracted(d)} ...", flush=True)
        tables = ig.load_city(d)
        inv += ig.file_inventory(c, tables)
        qual += ig.quality_checks(c, tables, today)
        rel.append(ig.relationship_stats(c, tables))
        print(f"[{c}] inspected: {sum(len(t) for t in tables.values()):,} records in {len(tables)} files", flush=True)
        del tables
    inv, qual, rel = pd.DataFrame(inv), pd.DataFrame(qual), pd.DataFrame(rel)
    inv.to_csv(f"{REP}/module1_file_inventory.csv", index=False)
    qual.to_csv(f"{REP}/module1_quality_issues.csv", index=False)
    stamp = datetime.date.today().isoformat()

    # ---------------- 1. data sources -------------------------------------------------------
    s = [f"# Module 1 – Dataset source documentation\n\n_Generated {stamp} by `run_module1.py`._\n",
         "## Official source named in the project document: Lepton Software (Datarade)\n",
         "* Listing: https://datarade.ai/data-products/india-transit-data-railways-metro-and-public-buses-routes-lepton-software",
         "* Description on the page: GTFS for **23 Indian cities** plus Indian Railways.",
         "* **Accessibility finding:** this is a *commercial* listing. The page gives no download link; pricing is only 'by contacting Lepton Software' "
         "(delivery via S3/SFTP/API after purchase), and the sample table shown on the page is masked. "
         "**The Lepton dataset was therefore NOT obtained**, and the page does not list which 23 cities are included.",
         "* We have **not** collected 23 cities. We have not verified that Lepton data would contain every required file.\n",
         "## What was actually collected instead (open GTFS feeds, same file format)\n",
         "| City | Operator | Downloaded file size (MB) | Direct URL | Publisher / provenance |", "|---|---|---|---|---|"]
    for c in cities:
        if c in SOURCES:
            op, url, note = SOURCES[c]
            s.append(f"| {c} | {op} | {zips.get(c)} | {url} | {note} |")
    s += ["", "**Cities from the project plan with no open GTFS feed found:** Mumbai (BEST), Rajkot, Hubli-Dharwad "
          "(checked MobilityDatabase and public repositories; nothing usable). Delhi's official feed needs an API key; the archived copy above was used.",
          "", "## Folder layout", "```", "data/raw/<city>/<city>_gtfs.zip   <- original download, untouched",
          "data/raw/<city>/*.txt             <- same files extracted by run_module1.py (read-only use)", "data/processed/                   <- reserved for Module 2 outputs", "```",
          "", "## How to obtain the data again", "`python download_data.py` (all) or `python download_data.py pune kochi`; "
          "if a URL fails, download the ZIP manually from the link above into `data/raw/<city>/`.",
          "", "## Access / licence limitations", "* All files are third-party feeds; check each publisher's licence before redistributing. Raw files are therefore **not committed to Git** (see `.gitignore`).",
          "* Bengaluru and Ahmedabad feeds are community-compiled, not operator-published. Kochi and Delhi service dates are old."]
    open(f"{REP}/module1_data_sources.md", "w", encoding="utf-8").write("\n".join(s) + "\n")

    # ---------------- 2. dataset inventory + quality ----------------------------------------
    m = [f"# Module 1 – Dataset inventory and data-quality observations\n\n_Generated {stamp}. Counts only – **no record was deleted, imputed or modified**._\n",
         "## Summary: required files and record counts per city\n"]
    piv = inv[inv.kind == "required"].pivot(index="city", columns="file", values="records").reindex(cities)
    piv.insert(0, "city", piv.index)
    m.append(md_table(piv.reset_index(drop=True)))
    miss = inv[(inv.kind == "required") & (~inv.available)]
    m.append("**Missing required files:** " + (", ".join(f"{r.city}/{r.file}" for r in miss.itertuples()) if len(miss) else "none") + "\n")
    opt = inv[inv.kind == "optional"].assign(v=lambda d: d.available.map({True: "yes", False: "–"}) )
    po = opt.pivot(index="city", columns="file", values="v").reindex(cities)
    po.insert(0, "city", po.index)
    m += ["\n## Optional files available\n", md_table(po.reset_index(drop=True)), "",
          "**Why optional files matter:**\n"] + [f"* `{k}.txt` – {v}" for k, v in ig.USEFULNESS.items()] + [""]
    m.append("## Important columns per file\n")
    m += [f"* `{k}.txt`: {v}" for k, v in ig.IMPORTANT.items()] + [""]
    for c in cities:
        op = SOURCES.get(c, ("",))[0]
        m += [f"\n---\n## {c.capitalize()} – {op}\n", f"Download size: {zips.get(c)} MB\n",
              md_table(inv[inv.city == c][["file", "kind", "available", "records", "columns", "column_names"]]),
              "\n### Data-quality observations (only checks with at least one finding)\n"]
        q = qual[(qual.city == c) & (qual["count"] > 0)][["file", "check", "count", "pct", "note"]]
        m.append(md_table(q))
        m.append("\n_Checks that found nothing are in `module1_quality_issues.csv`._\n")
    def cities_with(prefix, min_pct=0.0):
        d = qual[qual.check.str.startswith(prefix) & (qual["count"] > 0) & (qual.pct.fillna(0) >= min_pct)]
        return [f"{r.city} ({r.pct:g}%)" for r in d.itertuples()]
    exp, all7, over24, dups = (cities_with("service already expired"), cities_with("service runs all 7 days", 100),
                               cities_with("time >= 24:00:00", 5), qual[qual.check.str.startswith("duplicate key") & (qual["count"] > 0)])
    nb = cities_with("route_type is not a bus")
    m += ["\n---\n## Key observations (computed from the checks above)\n",
          "* **Weekday/weekend cannot be separated** in these feeds (every service runs all 7 days, usually one service_id): " + (", ".join(all7) or "none") + ". The planned 'weekday vs weekend' feature will need another source or must be dropped for these cities.",
          "* **Schedules already expired** (share of calendar rows with end_date before today): " + (", ".join(exp) or "none") + ". These describe a past timetable, not today's.",
          "* **Many times beyond 24:00:00** (valid GTFS, but must be handled when deriving hour-of-day): " + (", ".join(over24) or "none") + ".",
          "* **Duplicate keys:** " + (", ".join(f"{r.city} {r.file} ({r.count})" for r in dups.itertuples()) or "none") + ".",
          "* **Non-bus rows mixed into routes.txt:** " + (", ".join(nb) or "none") + ".",
          "* GTFS contains **no passenger counts or occupancy** in any city – this limitation is unchanged by these checks.", ""]
    m += ["\n---\n## How to read these findings\n",
          "* 'time >= 24:00:00' is **valid GTFS** (trip continues after midnight) – it must be handled later, not removed.",
          "* A very high count of 'identical arrival time at consecutive stops' suggests the publisher interpolated/estimated stop times – such timings must not be treated as measured.",
          "* 'service already expired' means the schedule dates in calendar.txt are in the past; the *pattern* of service can still be studied, but it is not a current timetable.",
          "* 'trip with no stop_times' in a feed that has frequencies.txt usually means a frequency template rather than an error.",
          "* Decisions on how to treat each issue (drop / fix / keep) are deferred to the data-cleaning module and will be justified there."]
    open(f"{REP}/module1_dataset_inventory.md", "w", encoding="utf-8").write("\n".join(m) + "\n")

    # ---------------- 3. relationships ------------------------------------------------------
    r = ["# Module 1 – How the GTFS files are connected\n",
         "```", "calendar.txt ──service_id──▶ trips.txt ◀──route_id── routes.txt", "                              │", "                           trip_id", "                              ▼",
         "stops.txt ◀──stop_id── stop_times.txt  (one row per stop visit of a trip, ordered by stop_sequence)", "```", "",
         "| Link | Meaning | Join key |", "|---|---|---|",
         "| routes → trips | one route has many scheduled trips (directions, times of day) | `route_id` |",
         "| trips → stop_times | one trip visits an ordered list of stops with arrival/departure times | `trip_id` (+ `stop_sequence`) |",
         "| stop_times → stops | each visit refers to a physical stop with coordinates | `stop_id` |",
         "| trips → calendar | decides on which weekdays/date range the trip runs | `service_id` |",
         "| frequencies → trips (optional) | 'a bus every N seconds' template for a trip | `trip_id` |",
         "| shapes → trips (optional) | road geometry of a trip | `shape_id` |", "",
         "**Example:** a trip may reach Stop A at 08:00, Stop B at 08:15, Stop C at 08:30 – three rows in `stop_times.txt` with the same `trip_id`, "
         "increasing `stop_sequence`, and three different `stop_id`s that are looked up in `stops.txt` for names and coordinates.", "",
         "## Measured on the collected feeds\n", md_table(rel.round(2)), "",
         "`trips_per_route_*` shows that routes have many trips; `stops_per_trip_median` the typical trip length; the two `*_matching_*_pct` columns "
         "show how cleanly the identifiers link (100 = every reference resolves). Gaps are listed in the inventory report.", "",
         "## Things to keep in mind", "* A *route_id* in many Indian feeds is a **route pattern** (one direction/variant), not a whole bus line; several route_ids can share a `route_short_name`.",
         "* GTFS holds **scheduled** service only – no passenger counts, occupancy or live traffic. Nothing in this module estimates or invents them."]
    open(f"{REP}/module1_relationships.md", "w", encoding="utf-8").write("\n".join(r) + "\n")
    print("Reports written to", REP)


if __name__ == "__main__":
    main(sys.argv[1:])
