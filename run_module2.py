"""Module 2 runner: clean -> engineer features -> save CSVs -> write reports.

    python run_module2.py              # all cities in data/raw/
    python run_module2.py pune kochi   # selected cities
Raw data is never touched; outputs go to data/processed/<city>/ and reports/.
"""
import glob, os, re, sys, datetime
import pandas as pd
from src import cleaning, inspect_gtfs as ig, module2_features as m2
from src.feature_dictionary import FEATURES

RAW, PROC, REP = "data/raw", "data/processed", "reports"
SKIP = {"sample_city", "demo"}


def md_table(df, floatfmt="{:,.2f}"):
    if df.empty:
        return "_none_\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if pd.isna(v) else (floatfmt.format(v) if isinstance(v, float) else str(v)) for v in r) + " |")
    return "\n".join(out) + "\n"


def process_city(city):
    d = f"{RAW}/{city}"
    raw = cleaning.load_raw(d)
    clean, log = cleaning.clean_city(raw, city)
    shapes = ig.read_file(d, "shapes")
    out = m2.build_all(clean, shapes)
    os.makedirs(f"{PROC}/{city}", exist_ok=True)
    out["route_features"].insert(0, "city", city)
    out["route_features"].to_csv(f"{PROC}/{city}/route_features.csv", index=False)
    out["route_hour_features"].to_csv(f"{PROC}/{city}/route_hour_features.csv", index=False)
    out["stop_usage"].to_csv(f"{PROC}/{city}/stop_usage.csv", index=False)
    out["trip_features"].to_csv(f"{PROC}/{city}/trip_features.csv", index=False)      # large: git-ignored
    log.to_csv(f"{PROC}/{city}/cleaning_log.csv", index=False)
    return out, log, shapes is not None


def main(cities):
    os.makedirs(REP, exist_ok=True)
    found = [os.path.basename(p) for p in sorted(glob.glob(f"{RAW}/*")) if os.path.isdir(p) and os.path.basename(p) not in SKIP]
    cities = cities or found
    logs, rfs, miss_rows, summ, has_shapes = [], [], [], [], {}
    for c in cities:
        print(f"[{c}] processing ...", flush=True)
        out, log, shp = process_city(c)
        has_shapes[c] = shp
        rf = out["route_features"]; logs.append(log); rfs.append(rf)
        m = rf.isna().sum(); m = m[m > 0]
        for col, n in m.items():
            miss_rows.append(dict(city=c, feature=col, missing=int(n), pct=round(100 * n / len(rf), 1)))
        tf = out["trip_features"]
        summ.append(dict(city=c, routes=len(rf), trips=len(tf), stops=len(out["stop_usage"]),
                         median_trips_per_route=rf.n_trips.median(), median_stops_per_route=rf.n_unique_stops.median(),
                         median_length_km=round(rf.length_km.median(), 1),
                         length_from_shapes=f"{(rf.length_method == 'shapes.txt').mean():.0%}",
                         share_trips_over_8h=round(float((tf.duration_min > 480).mean()), 3),
                         median_trip_min=round(float(tf.duration_min.median()), 1),
                         speed_p10_kmh=round(float(rf.avg_speed_kmh.quantile(.1)), 1), speed_p90_kmh=round(float(rf.avg_speed_kmh.quantile(.9)), 1),
                         duplicate_route_ids=int(rf.route_id.duplicated().sum()), speed_flagged=int(rf.speed_implausible.sum()),
                         backwards_trip_routes=int(rf.has_time_backwards_trip.sum()),
                         weekend_ratio_all_1=bool(rf.weekend_to_weekday_ratio.dropna().round(6).eq(1).all()) if "weekend_to_weekday_ratio" in rf else None))
        print(f"[{c}] done: {len(rf)} routes, {len(tf)} trips", flush=True)
    allrf = pd.concat(rfs, ignore_index=True)
    allrf.to_csv(f"{PROC}/all_cities_route_features.csv", index=False)
    logs = pd.concat(logs, ignore_index=True); logs.to_csv(f"{REP}/module2_cleaning_log.csv", index=False)
    summ, miss = pd.DataFrame(summ), pd.DataFrame(miss_rows)
    stamp = datetime.date.today().isoformat()

    # ---- feature dictionary (and coverage check: every saved route feature must be documented)
    documented = " ".join(f[1] for f in FEATURES)
    undocumented = [c for c in allrf.columns if not re.search(r"(^|[ ,/])" + re.escape(c) + r"($|[ ,/])", documented)]
    fd = pd.DataFrame(FEATURES, columns=["table", "feature", "data type", "numeric / categorical", "direct / derived", "source file(s)", "meaning and calculation"])
    txt = [f"# Module 2 - Feature dictionary\n\n_Generated {stamp}._ `direct` = a field copied from the GTFS files; `derived` = calculated by us. "
           "IDs (route_id, trip_id, stop_id) are identifiers, never numeric measurements.\n",
           "**Time periods (clearly defined rules):** " + "; ".join(f"{k} {v}" for k, v in m2.PERIOD_RULES.items()) + ". GTFS times can exceed 24:00:00 "
           "(trip runs past midnight); they are converted to seconds first and the clock hour is `(seconds // 3600) % 24`.\n"]
    for t in ["route_features", "route_hour_features", "trip_features", "stop_usage"]:
        txt += [f"\n## {t}.csv\n", md_table(fd[fd.table == t].drop(columns="table"))]
    txt += ["\n**Undocumented columns (should be empty):** " + (", ".join(undocumented) or "none") + "\n"]
    open(f"{REP}/module2_feature_dictionary.md", "w", encoding="utf-8").write("\n".join(txt))

    # ---- data quality report
    ch = logs[logs.rows_changed > 0].rename(columns={"rows_changed": "rows_affected"})
    q = [f"# Module 2 - Data quality report\n\n_Generated {stamp}._ Raw files are untouched (`data/raw/`); cleaned tables are rebuilt in memory and the features saved to `data/processed/`. "
         "Each action below lists how many rows it affected and why. Missing values are **not** replaced by zero.\n",
         "## Cleaning actions (only steps that affected at least one row; full log incl. before/after counts: `reports/module2_cleaning_log.csv`)\n\n`removed` = rows dropped (reason given); `expanded` = rows added; `filled` = a missing value copied from the other time of the same stop visit; `flagged` = kept and marked; `derived` = label created.\n", md_table(ch[["city", "table", "step", "action", "rows_affected", "reason"]], floatfmt="{:,.0f}"),
         "\n## Missing values in the route-level feature table (and why)\n",
         md_table(miss) if len(miss) else "_none_\n",
         "**Reading the table:** `median_headway_min` is missing when a route has fewer than 2 distinct departure times (headway undefined); `length_km_shape` when the feed has no shapes.txt or "
         "the trip has no shape_id (length then comes from stop coordinates, see `length_method`); `n_directions` when direction_id is absent; `weekend_to_weekday_ratio` when the route has no weekday trips; "
         "`trips_<day>` columns are absent when the feed has no calendar.txt. These are *unknown or undefined*, not zero.\n",
         "\n## Other checks per city\n", md_table(summ[["city", "duplicate_route_ids", "speed_flagged", "backwards_trip_routes"]]),
         "\n`speed_flagged` = routes with scheduled average speed > 80 or < 3 km/h; `backwards_trip_routes` = routes with a trip whose arrival times go backwards. "
         "These rows are **kept and flagged**; whether each is an error, a valid unusual case or a source limitation is examined in Module 3 (EDA).\n"]
    open(f"{REP}/module2_data_quality_report.md", "w", encoding="utf-8").write("\n".join(q))

    # ---- assumptions and limitations
    lm = allrf.groupby("city").length_method.value_counts(normalize=True).unstack(fill_value=0).round(3)
    lm.insert(0, "city", lm.index)
    a = [f"# Module 2 - Assumptions and limitations\n\n_Generated {stamp}._\n",
         "## What the features are - and are not\n",
         "* All features come from **scheduled** GTFS data. `n_trips`, `trips_per_active_hour`, `median_headway_min` and `scheduled_stop_visits` describe the planned service. "
         "They are **not passenger counts, occupancy or demand**, and no ridership is estimated anywhere in this module.",
         "* A route with few scheduled trips is not automatically inefficient, and a route with many is not automatically overcrowded.",
         "\n## Assumptions and decisions\n",
         "* **Bus scope:** routes whose route_type is not a bus code (3, 700-799, 200-299, 11) are excluded from the cleaned tables (visible in the cleaning report); they stay in the raw files.",
         "* **Distinct trips:** `n_trips` counts distinct `trip_id`. Feeds with several service patterns (e.g. seasonal or holiday schedules) are counted together, so `n_trips` can exceed the trips run on one actual day; "
         "`trips_monday..trips_sunday` give the per-weekday view from calendar.txt.",
         "* **Frequency-based feeds** (Kochi) are expanded into explicit trips; each expanded trip is a *scheduled* departure derived from the published headway.",
         "* **Time periods** use the fixed rules in the feature dictionary and are based on the trip's first departure.",
         "* **Route length** uses `shapes.txt` when present and plausible (0.5x-3x of the stop-based length); otherwise the straight-line sum between consecutive stops of the longest trip. Straight-line length is shorter than the road distance. Shares by city:\n",
         md_table(lm.reset_index(drop=True), floatfmt="{:.1%}"),
         "* **Overlap** is based on shared stops (Jaccard similarity) and excludes routes with the same name and opposite-direction twins. Shared stops do not prove that two routes are redundant.",
         "\n## Limitations\n",
         "* **No passenger data** in any collected feed. Overcrowding / underutilisation cannot be concluded from schedules alone.",
         "* **Weekday vs weekend:** computed from calendar.txt only. `calendar_dates.txt` exceptions (holidays) are not applied. Cities whose services all run every day show a ratio of exactly 1.0 - "
         "that is what the schedule says, not a computation artefact: " + ", ".join(summ[summ.weekend_ratio_all_1 == True].city.tolist() or ["none"]) + ".",
         "* **Expired schedules:** Delhi and Kochi calendars are from 2022-24 (see Module 1 report). The features describe that past timetable.",
         "* **Community-compiled feeds** (Ahmedabad, Bengaluru, Chennai, Kochi) may have been generated from public timetables or estimates by their maintainers; timing quality is unverified. "
         "Identical consecutive arrival times seen in Module 1 suggest interpolated times in some feeds.",
         "* **Stop usage** = scheduled calls per stop, not boardings.",
         "* Lepton Software / Datarade data could not be obtained (paid), so results cover 7 cities, not 23.",
         "\n## Timing plausibility check (what the schedules themselves look like)\n",
         md_table(summ[["city", "median_trip_min", "share_trips_over_8h", "speed_p10_kmh", "speed_p90_kmh"]]),
         "Scheduled speed = estimated route length / median scheduled trip duration.\n"]
    for r in summ.itertuples():
        if r.share_trips_over_8h > 0.2:
            a.append(f"* **{r.city}:** {r.share_trips_over_8h:.0%} of trips last more than 8 hours (median {r.median_trip_min:.0f} min) and the typical scheduled speed is implausibly low. "
                     "The feed's 'trips' therefore appear to be whole vehicle duties (many round trips chained under one trip_id), so trip counts and headways of this city are **not comparable** with cities whose trips are single runs. To be confirmed with the publisher.")
        if (r.speed_p90_kmh - r.speed_p10_kmh) < 3:
            a.append(f"* **{r.city}:** scheduled speed is almost identical for every route (10th-90th percentile: {r.speed_p10_kmh}-{r.speed_p90_kmh} km/h), which suggests that stop times may have been *generated with a near-constant speed* rather than taken from an operational timetable (to be verified with the publisher). If so, durations in this feed describe a model schedule, not measured operations.")
    a.append("* **Chennai:** shapes.txt exists but only contains 13 metro (CMRL) shapes; bus trips carry no shape_id, so bus route lengths come from stop coordinates.")
    open(f"{REP}/module2_assumptions_limitations.md", "w", encoding="utf-8").write("\n".join(a))

    # ---- route profile summary + a sample profile per city
    p = [f"# Module 2 - Route profile summary\n\n_Generated {stamp}._ Full route profiles: `data/processed/<city>/route_features.csv` "
         "(all cities combined: `data/processed/all_cities_route_features.csv`).\n", "## Overview per city\n",
         md_table(summ.drop(columns=["duplicate_route_ids", "speed_flagged", "backwards_trip_routes", "weekend_ratio_all_1"])), "\n## Example route profiles (the route with the median number of trips in each city)\n"]
    show = ["route_id", "route_name", "n_trips", "n_unique_stops", "length_km", "length_method", "service_span_h", "trips_per_active_hour",
            "median_headway_min", "trips_morning", "trips_afternoon", "trips_evening", "trips_night", "max_stop_overlap"]
    ex = []
    for c in cities:
        r = allrf[allrf.city == c]
        ex.append(r.iloc[(r.n_trips - r.n_trips.median()).abs().argsort().iloc[0]][["city"] + show])
    p.append(md_table(pd.DataFrame(ex)))
    open(f"{REP}/module2_route_profile_summary.md", "w", encoding="utf-8").write("\n".join(p))
    print("done. undocumented columns:", undocumented)


if __name__ == "__main__":
    main(sys.argv[1:])
