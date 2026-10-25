"""Module 3 runner: exploratory data analysis of the Module-2 dataset for every city.

    python run_module3.py              # all cities in data/processed/
    python run_module3.py pune kochi
Writes figures (reports/figures/<city>/), maps (reports/maps/), tables (reports/tables/) and the four Module-3 reports.
Everything describes SCHEDULED service; no passenger figure is created.
"""
import glob, os, sys, datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src import eda
from run_module2 import md_table

PROC, REP = "data/processed", "reports"
CAPTIONS = {
 "f01": "Histogram of scheduled trips per route on a log scale. Each bar counts routes with that many trips; the dashed line is the median. A long right tail means a few routes have far more scheduled trips than most.",
 "f02": "Histogram of distinct stops per route. It shows whether most routes serve a similar number of stops or whether stop counts differ a lot.",
 "f03": "Histogram of estimated route length (km, log scale). Lengths come from shapes.txt where available, otherwise from straight-line distances between stops.",
 "f04": "Box plots of four route features (log scale where skewed): the box holds the middle 50% of routes, the line is the median and dots are statistical outliers (not necessarily errors).",
 "f05": "Distinct scheduled trips whose first departure falls in each clock hour, coloured by time period. This is planned service supply; it is not passenger demand.",
 "f06": "Scheduled trips by time period with each period's share of all scheduled trips. Periods have different lengths in hours, so compare trips per hour (in the table) as well.",
 "f07": "Scheduled trips per hour on a typical weekday (services running on Wednesday) vs Sunday, from calendar.txt.",
 "f08": "The 15 routes with the most scheduled trips. High scheduled trip counts show where the timetable offers most departures; they do not show crowding.",
 "f09": "Each dot is a route: estimated length against scheduled trips (log scale). The Spearman rho in the title measures how consistently they rise or fall together - an association, not a cause.",
 "f10": "Distinct stops against scheduled trips for each route; rho in the title as above.",
 "f11": "Spearman correlation matrix of numeric route features. Colour shows the direction and strength of association between two features; identifiers are not included. Some pairs (scheduled trips, trips per active hour, headway, service span) are linked by definition, so their high correlation is expected and is not a finding.",
 "f12": "Box plots used to investigate unusual values (trips, stops, length, scheduled speed, headway). Unusual values are investigated in the data-quality summary, not deleted.",
 "f13": "Histogram of the median scheduled gap between consecutive departures of a route (headway, minutes, log scale). Routes with a single departure time have no headway and are not shown.",
}


def make_figures(R, outdir):
    rf, h, p, city = R["rf"], R["h"], R["p"], R["city"]
    os.makedirs(outdir, exist_ok=True)
    figs = {"f01_trips_per_route": ("f01", eda.f_hist(rf, "n_trips", city, log_x=True)),
            "f02_stops_per_route": ("f02", eda.f_hist(rf, "n_unique_stops", city)),
            "f03_route_length": ("f03", eda.f_hist(rf, "length_km", city, log_x=True)),
            "f04_boxplots": ("f04", eda.f_box_panel(rf, city)),
            "f05_hourly_trips": ("f05", eda.f_hourly(h, city)),
            "f06_period_trips": ("f06", eda.f_period(p, city))}
    if "trips_weekday_wed" in h and h.trips_weekday_wed.sum() != h.trips_sunday.sum():
        figs["f07_weekday_vs_sunday"] = ("f07", eda.f_weekday_sunday(h, city))
    figs.update({"f08_top_routes": ("f08", eda.f_top_routes(rf, city)),
                 "f09_length_vs_trips": ("f09", eda.f_scatter(rf, "length_km", "n_trips", city)),
                 "f10_stops_vs_trips": ("f10", eda.f_scatter(rf, "n_unique_stops", "n_trips", city)),
                 "f11_corr_heatmap": ("f11", eda.f_corr(rf, city)),
                 "f12_outlier_boxplots": ("f12", eda.f_outliers(rf, city)),
                 "f13_headway": ("f13", eda.f_hist(rf, "median_headway_min", city, log_x=True))})
    out = {}
    for name, (key, fig) in figs.items():
        fig.savefig(f"{outdir}/{name}.png", dpi=110); plt.close(fig); out[name] = key
    return out


def make_maps(R, outdir):
    os.makedirs(outdir, exist_ok=True)
    city, rf = R["city"], R["rf"]
    made = [f"{city}_stops_heatmap.html"]
    eda.stop_map(R["su"], city, f"{outdir}/{made[0]}")
    if R["shapes"] is not None:
        top = rf[rf.length_method == "shapes.txt"].nlargest(8, "n_trips")
        eda.draw_routes_map(R["shapes"], R["trip_shape"], [(r.route_id, f"route {r.route_name}: {r.n_trips} scheduled trips, {r.length_km:.1f} km") for r in top.itertuples()], f"{outdir}/{city}_top_route_shapes.html")
        made.append(f"{city}_top_route_shapes.html")
        so = R["shape_ov"]
        if so is not None and len(so):
            best = so.sort_values("shape_overlap_jaccard", ascending=False).iloc[0]
            nm = rf.set_index("route_id").route_name
            eda.draw_routes_map(R["shapes"], R["trip_shape"], [(best.route_id, f"route {nm[best.route_id]} (shape overlap {best.shape_overlap_jaccard:.0%})"),
                                (best.shape_overlap_partner, f"route {nm[best.shape_overlap_partner]}")], f"{outdir}/{city}_shape_overlap_pair.html")
            made.append(f"{city}_shape_overlap_pair.html")
    return made


def city_row(R):
    rf, h, p, c = R["rf"], R["h"], R["p"], R["corr"]
    return dict(city=R["city"], routes=len(rf), scheduled_trips=int(rf.n_trips.sum()), stops=len(R["su"]), median_trips_per_route=rf.n_trips.median(),
                p90_trips=rf.n_trips.quantile(.9), max_over_median=round(rf.n_trips.max() / rf.n_trips.median(), 1),
                share_routes_le5_trips=f"{(rf.n_trips <= 5).mean():.0%}", median_stops=rf.n_unique_stops.median(), median_length_km=round(rf.length_km.median(), 1),
                busiest_hour=f"{h.scheduled_trips.idxmax():02d}:00", quietest_hour=f"{h.scheduled_trips.idxmin():02d}:00",
                busiest_period_per_hour=p.trips_per_hour.idxmax(), rho_length_trips=c.loc["length_km", "n_trips"], rho_stops_trips=c.loc["n_unique_stops", "n_trips"],
                overlap_pairs_ge80=len(R["ov"]), routes_speed_flagged=int(rf.speed_implausible.sum()),
                shape_overlap_routes_ge80=(int((R["shape_ov"].shape_overlap_jaccard >= .8).sum()) if R["shape_ov"] is not None else None))


def main(cities):
    found = [os.path.basename(p) for p in sorted(glob.glob(f"{PROC}/*")) if os.path.isdir(p)]
    cities = cities or found
    stamp = datetime.date.today().isoformat()
    os.makedirs(f"{REP}/tables", exist_ok=True)
    rows, sections, cmp_md, dq_md, find_md = [], [], [], [], []
    for c in cities:
        print(f"[{c}] EDA ...", flush=True)
        R = eda.analyze(c)
        figs = make_figures(R, f"{REP}/figures/{c}")
        maps = make_maps(R, f"{REP}/maps")
        rf, ov, low = R["rf"], R["ov"], R["low"]
        rows.append(city_row(R))
        # ---- tables
        cols = [x for x in ["route_id", "route_name", "n_trips", "n_unique_stops", "length_km", "length_method", "service_span_h", "median_headway_min",
                            "trips_morning", "trips_afternoon", "trips_evening", "trips_night", "avg_speed_kmh", "max_stop_overlap", "overlap_partner_name"] if x in rf]
        rf.sort_values("n_trips", ascending=False)[cols].to_csv(f"{REP}/tables/{c}_route_comparison.csv", index=False)
        ov.to_csv(f"{REP}/tables/{c}_overlap_candidates.csv", index=False)
        low.to_csv(f"{REP}/tables/{c}_low_service_candidates.csv", index=False)
        caveats = eda.timing_caveats(rf)
        # ---- main report section
        s = [f"\n---\n## {c.title()}\n"]
        if caveats:
            s += ["**Data caveats for this city:**\n"] + [f"* {x}" for x in caveats] + [""]
        s += ["### 1. Dataset inspection\n",
              f"* {R['info'][1]['rows']:,} rows x {R['info'][1]['columns']} columns (one row per route); duplicate rows: {R['info'][1]['duplicate_rows']}; duplicate route_id: {R['info'][1]['duplicate_route_id']}.",
              "* Columns with missing values: " + (", ".join(f"`{k}` ({v})" for k, v in R['info'][0].missing[R['info'][0].missing > 0].items()) or "none") + " (missing = undefined/unknown, never replaced by zero).",
              "\nSummary statistics of the main numeric features:\n", md_table(R["desc"].reset_index().rename(columns={"index": "feature"})), ""]
        s += ["### 2. Univariate analysis\n"] + [f"* {x}" for x in eda.obs_univariate(rf)] + [""]
        for k in ["f01_trips_per_route", "f02_stops_per_route", "f03_route_length", "f04_boxplots"]:
            s += [f"![{k}](figures/{c}/{k}.png)\n", f"*{CAPTIONS[figs[k]]}*\n"]
        s += ["### 3. Scheduled service by time of day\n"] + [f"* {x}" for x in eda.obs_hourly(R["h"], R["p"])] + ["", md_table(R["p"].reset_index()), ""]
        for k in ["f05_hourly_trips", "f06_period_trips", "f07_weekday_vs_sunday"]:
            if k in figs:
                s += [f"![{k}](figures/{c}/{k}.png)\n", f"*{CAPTIONS[figs[k]]}*\n"]
        s += ["### 4. Route-wise comparison\n"] + [f"* {x}" for x in eda.obs_routes(rf, R["groups"])] + ["", md_table(R["groups"].reset_index().rename(columns={"group": "group (by scheduled trips)"})), ""]
        for k in ["f08_top_routes", "f13_headway"]:
            s += [f"![{k}](figures/{c}/{k}.png)\n", f"*{CAPTIONS[figs[k]]}*\n"]
        s += ["### 5. Geographical analysis and overlap\n",
              f"* Stop map: `maps/{maps[0]}` (heat map of the {len(R['su']):,} stops weighted by the number of routes calling there; the 15 stops with most routes are marked)."]
        if R["shapes"] is not None:
            s += [f"* Route shapes available for {100 * (rf.length_method == 'shapes.txt').mean():.0f}% of routes: " + ", ".join(f"`maps/{m}`" for m in maps[1:]) + "."]
        else:
            s += ["* **No usable route-shape data for buses in this feed**, so route paths are not drawn and path-based overlap is not computed (stop-based overlap only)."]
        s += [f"* {x}" for x in eda.obs_overlap(rf, ov, R["shape_ov"])]
        s += ["\nMost similar route pairs by shared stops (candidates for further investigation, not conclusions):\n", md_table(ov.head(8).reset_index(drop=True)), ""]
        s += ["### 6. Association between features\n"] + [f"* {x}" for x in eda.obs_corr(rf)] + [""]
        for k in ["f09_length_vs_trips", "f10_stops_vs_trips", "f11_corr_heatmap"]:
            s += [f"![{k}](figures/{c}/{k}.png)\n", f"*{CAPTIONS[figs[k]]}*\n"]
        s += ["Correlation shows association only; it does not show that longer routes cause more or fewer trips.\n"]
        sections.append("\n".join(s))
        # ---- route comparison summary
        top = rf.nlargest(10, "n_trips")[["route_name", "n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min"]]
        lowt = low.head(10)[["route_name", "n_trips", "n_unique_stops", "length_km", "service_span_h"]]
        cmp_md += [f"\n## {c.title()}\n", "**Routes grouped by number of scheduled trips (median of each feature):**\n", md_table(R["groups"].reset_index().rename(columns={"group": "group"})),
                   "**10 routes with the most scheduled trips:**\n", md_table(top), f"**10 of the {len(low)} routes in the lowest 10% of scheduled trips (<= {rf.n_trips.quantile(.1):.0f} trips):**\n", md_table(lowt),
                   f"Full table: `tables/{c}_route_comparison.csv`. " + ("*Caveat: " + " ".join(caveats) + "*" if caveats else "")]
        # ---- data quality
        miss = R["info"][0].missing[R["info"][0].missing > 0]
        dq_md += [f"\n## {c.title()}\n", f"* Dataset: {R['info'][1]['rows']:,} routes x {R['info'][1]['columns']} features; duplicate rows {R['info'][1]['duplicate_rows']}; duplicate route_id {R['info'][1]['duplicate_route_id']}.",
                  "* Missing values: " + (", ".join(f"`{k}` {v} ({100 * v / len(rf):.1f}%)" for k, v in miss.items()) or "none") + " (undefined values, not zeros).",
                  *([f"* **Feed-level caveat (source limitation):** {x}" for x in caveats]),
                  "\n**Outlier screening (Tukey 1.5 x IQR, log scale for skewed features):**\n", md_table(R["out"]),
                  "\n**Investigation of unusual values (kept in the data; classified, not deleted):**\n", md_table(R["inv"]), f"\n![outliers](figures/{c}/f12_outlier_boxplots.png)\n", f"*{CAPTIONS['f12']}*\n"]
        # ---- findings
        find_md += [f"\n### {c.title()}\n",
                    f"* {len(ov)} route pairs share >= 80% of their stops (see `tables/{c}_overlap_candidates.csv`)."
                    + (f" {int((R['shape_ov'].shape_overlap_jaccard >= .8).sum())} routes also share >= 80% of their path (shapes.txt)." if R["shape_ov"] is not None else ""),
                    f"* {len(low)} routes have very few scheduled trips (lowest 10%, <= {rf.n_trips.quantile(.1):.0f}); {int((rf.n_trips < 3).sum())} have fewer than 3 (`tables/{c}_low_service_candidates.csv`).",
                    f"* {int(rf.speed_implausible.sum())} routes have a scheduled speed outside 3-80 km/h (possible data problem)."] + [f"* Caveat: {x}" for x in caveats]
        del R

    cc = pd.DataFrame(rows)
    cc.to_csv(f"{REP}/module3_cross_city_summary.csv", index=False)
    head = [f"# Module 3 - Exploratory analysis report\n\n_Generated {stamp}._ Data: the feature-engineered dataset from Module 2 (`data/processed/<city>/route_features.csv`, `route_hour_features.csv`, `stop_usage.csv`) for {len(cities)} cities.\n",
            "> **What this report describes.** GTFS contains the *planned* routes, trips, stops and times. Every number below is a count of **scheduled** trips or stops. It is not a count of passengers: GTFS has no ridership or occupancy data, so no route is called overcrowded or underutilised here. "
            "Routes that look different are *candidates for further investigation*, nothing more.\n",
            "## Cross-city summary\n", md_table(cc.drop(columns=["shape_overlap_routes_ge80"]), floatfmt="{:,.2f}"),
            "\n## Answers to the guiding questions\n",
            f"1. **Hours with the highest / lowest scheduled trip counts** - busiest hour per city: " + ", ".join(f"{r.city} {r.busiest_hour}" for r in cc.itertuples()) + "; quietest: " + ", ".join(f"{r.city} {r.quietest_hour}" for r in cc.itertuples()) + ". Busiest period per hour: " + ", ".join(f"{r.city} {r.busiest_period_per_hour}" for r in cc.itertuples()) + ".",
            "2. **How service varies across routes** - scheduled trips per route are very unevenly spread: " + ", ".join(f"{r.city} median {r.median_trips_per_route:.0f}, max {r.max_over_median:.0f}x median, {r.share_routes_le5_trips} of routes <= 5 trips" for r in cc.itertuples()) + ".",
            "3. **Routes with the most distinct stops** - listed per city in section 4 below.",
            "4. **Route length vs scheduled trips** - Spearman rho: " + ", ".join(f"{r.city} {r.rho_length_trips:.2f}" for r in cc.itertuples()) + ". Values near 0 mean the two vary almost independently; this is an association, not a cause.",
            "5. **Shared stops / geographical segments** - route pairs with >= 80% shared stops: " + ", ".join(f"{r.city} {r.overlap_pairs_ge80}" for r in cc.itertuples()) + ". Path-based overlap (shapes.txt) was computed only where bus shapes exist: " + ", ".join(f"{r.city} {int(r.shape_overlap_routes_ge80)} routes" for r in cc.itertuples() if pd.notna(r.shape_overlap_routes_ge80)) + ".",
            "6. **Unusual values and quality issues** - see `module3_data_quality_summary.md`: very uneven trip counts, implausible scheduled speeds in some routes, undefined headways for single-departure routes, and feed-level caveats (Hyderabad duty-level trips, Delhi/Kochi/Pune near-constant speeds, expired Delhi/Kochi calendars).",
            "7. **What the data supports and what it does not** - supported: how many trips and stops each route has, when scheduled service is concentrated, which routes share stops or corridors. Not supported: any statement about crowding, passenger demand, profitability, or whether a route should be merged or cut. That needs ridership/boarding counts by route and time, vehicle capacity and fleet data, run-time or delay data, and the operator's service objectives (see `module3_findings_and_limitations.md`)."]
    open(f"{REP}/module3_exploratory_analysis_report.md", "w", encoding="utf-8").write("\n".join(head) + "\n" + "\n".join(sections))
    open(f"{REP}/module3_route_comparison_summary.md", "w", encoding="utf-8").write(
        f"# Module 3 - Route comparison summary\n\n_Generated {stamp}._ Differences between routes in **scheduled** service. They identify routes worth a closer look; they do not show that any route is inefficient.\n"
        + "\n".join(cmp_md) + "\n\n## What would be needed for stronger conclusions\n* Boardings/ridership by route, stop and time (verified to match GTFS route ids, dates and periods).\n* Vehicle capacity, fleet allocation and operating cost per route.\n* Measured run times / delays (GTFS times are planned).\n* The operator's purpose for each route (coverage, feeder, express, school/office services).\n* Validated route shapes for every route.\n")
    open(f"{REP}/module3_data_quality_summary.md", "w", encoding="utf-8").write(
        f"# Module 3 - Data quality summary\n\n_Generated {stamp}._ Unusual values were **investigated, not deleted**. Original GTFS files stay in `data/raw/`; the Module-2 dataset is unchanged by this module (no corrections or exclusions were applied).\n"
        "Outliers are statistical (Tukey fences) and are classified as: *valid but unusual*, *suspect* (contradicts other attributes of the route) or *source limitation* (property of the feed).\n" + "\n".join(dq_md))
    open(f"{REP}/module3_findings_and_limitations.md", "w", encoding="utf-8").write(
        f"# Module 3 - Findings and limitations\n\n_Generated {stamp}._\n\n## Patterns that need further investigation (candidates only)\n"
        "A candidate is a route or pair that looks different in the **scheduled** data. None is a confirmed inefficiency: fewer trips does not mean underutilised, and overlapping routes may serve different passengers.\n" + "\n".join(find_md) +
        "\n\n## What the dataset supports\n* Distinct scheduled trips, stops, estimated lengths, operating spans and hourly/period patterns per route.\n* Which routes share stops (all cities) or road corridors (cities with shapes).\n* Which feeds have structural caveats (below).\n"
        "\n## What it does not support\n* Passenger demand, crowding, load factors, revenue, or any 'overcrowded' / 'underutilised' label.\n* Whether overlapping routes are redundant, or whether a route should be merged, split or cut.\n* Weekday-vs-weekend differences in feeds whose calendar says every day is identical.\n"
        "\n## Assumptions and limitations of the analysis\n* Time periods: morning 05:00-11:59, afternoon 12:00-16:59, evening 17:00-20:59, night 21:00-04:59, by first departure.\n* `n_trips` counts distinct trips over all service patterns of a feed; per-weekday views come from calendar.txt (calendar_dates exceptions not applied).\n"
        "* Route length from stop coordinates is a straight-line lower bound; shapes are used where available and plausible.\n* Stop overlap = Jaccard similarity of stop sets; path overlap = Jaccard similarity of ~200 m grid cells along shapes.txt. Same-name and opposite-direction routes are excluded.\n"
        "* Feeds are community-compiled or old (Delhi/Kochi calendars 2022-24); Hyderabad trips look like vehicle duties; Delhi, Kochi and Pune show near-constant scheduled speeds.\n* 7 cities only: the Lepton/Datarade dataset (23 cities) is paid and was not available; Mumbai, Rajkot and Hubli-Dharwad have no open feed.\n"
        "\n## Next step\nModule 4 (data preprocessing) should decide, with the mentor, how to treat flagged rows and non-comparable feeds, and whether a real ridership source can be obtained before any model uses the word 'demand'.\n")
    print("done")


if __name__ == "__main__":
    main(sys.argv[1:])
