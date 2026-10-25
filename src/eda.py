"""Module 3 helpers: loading the Module-2 dataset, summary tables, charts and maps.

Everything here describes SCHEDULED service. Labels say 'scheduled trips', never 'passengers'.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

PERIOD_ORDER = ["morning", "afternoon", "evening", "night"]
PERIOD_COLORS = {"morning": "#f4a261", "afternoon": "#e9c46a", "evening": "#2a9d8f", "night": "#264653"}
NUM_COLS = ["n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "avg_trip_duration_min",
            "trips_per_active_hour", "stops_per_km", "avg_speed_kmh", "max_stop_overlap", "mean_routes_per_stop"]
LABELS = {"n_trips": "scheduled trips per route", "n_unique_stops": "distinct stops per route", "length_km": "estimated route length (km)",
          "service_span_h": "scheduled service span (hours)", "median_headway_min": "median headway (min)", "avg_trip_duration_min": "mean scheduled trip duration (min)",
          "trips_per_active_hour": "scheduled trips per active hour", "stops_per_km": "stops per km", "avg_speed_kmh": "scheduled speed (km/h)",
          "max_stop_overlap": "max stop overlap with another route (0-1)", "mean_routes_per_stop": "mean routes per stop"}
sns.set_theme(style="whitegrid", context="notebook")


def load(city, base="data/processed"):
    d = f"{base}/{city}"
    rf = pd.read_csv(f"{d}/route_features.csv", dtype={"route_id": str, "route_name": str, "overlap_partner": str, "overlap_partner_name": str})
    rh = pd.read_csv(f"{d}/route_hour_features.csv", dtype={"route_id": str})
    su = pd.read_csv(f"{d}/stop_usage.csv", dtype={"stop_id": str})
    return rf, rh, su


# ------------------------------------------------------------------ tables
def inspect_table(df):
    """Section 2 of the brief: shape, dtypes, missing values, duplicates."""
    info = pd.DataFrame({"dtype": df.dtypes.astype(str), "non_null": df.notna().sum(), "missing": df.isna().sum(),
                         "missing_%": (100 * df.isna().mean()).round(1), "unique": df.nunique()})
    return info, dict(rows=len(df), columns=df.shape[1], duplicate_rows=int(df.duplicated().sum()),
                      duplicate_route_id=int(df.route_id.duplicated().sum()) if "route_id" in df else None)


def describe(rf, cols=None):
    cols = [c for c in (cols or NUM_COLS) if c in rf]
    d = rf[cols].agg(["count", "min", "median", "mean", "std", "max"]).T
    d["p90"] = rf[cols].quantile(.9)
    return d.round(2)


def hourly_table(rh):
    h = rh.groupby("hour").agg(scheduled_trips=("trips_all", "sum"), scheduled_stop_visits=("scheduled_stop_visits", "sum"),
                               routes_with_trip_start=("trips_all", lambda x: int((x > 0).sum())))
    for c, n in [("trips_typical_weekday", "trips_weekday_wed"), ("trips_typical_sunday", "trips_sunday")]:
        if c in rh:
            h[n] = rh.groupby("hour")[c].sum()
    h = h.reindex(range(24)).fillna(0).astype(int)        # an hour with no scheduled start is a real 0 trips
    h["period"] = pd.Series(h.index, index=h.index).map(lambda x: "morning" if 5 <= x <= 11 else "afternoon" if 12 <= x <= 16 else "evening" if 17 <= x <= 20 else "night")
    return h


def period_table(h):
    p = h.groupby("period").agg(hours=("scheduled_trips", "size"), scheduled_trips=("scheduled_trips", "sum")).reindex(PERIOD_ORDER)
    p["share_%"] = (100 * p.scheduled_trips / p.scheduled_trips.sum()).round(1)
    p["trips_per_hour"] = (p.scheduled_trips / p.hours).round(0)
    return p


def group_comparison(rf):
    """Compare routes with low / middle / high scheduled trip counts on their other characteristics."""
    q1, q3 = rf.n_trips.quantile([.25, .75])
    g = np.where(rf.n_trips <= q1, "low (<= Q1)", np.where(rf.n_trips >= q3, "high (>= Q3)", "middle"))
    cols = [c for c in ["n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "avg_speed_kmh", "max_stop_overlap"] if c in rf]
    t = rf.assign(group=g).groupby("group")[cols].median().round(2)
    t.insert(0, "routes", rf.assign(group=g).groupby("group").size())
    return t.reindex(["low (<= Q1)", "middle", "high (>= Q3)"])


def overlap_candidates(rf, thr=0.8):
    c = rf[rf.max_stop_overlap >= thr].copy()
    c["pair"] = [tuple(sorted(x)) for x in zip(c.route_id, c.overlap_partner)]
    c = c.drop_duplicates("pair")
    n = rf.set_index("route_id").n_trips
    c["partner_trips"] = c.overlap_partner.map(n)
    return c[["route_name", "overlap_partner_name", "max_stop_overlap", "n_trips", "partner_trips", "length_km"]].sort_values("max_stop_overlap", ascending=False)


def low_service_candidates(rf):
    p10 = rf.n_trips.quantile(.10)
    c = rf[(rf.n_trips <= p10)].copy()
    return c[["route_name", "n_trips", "n_unique_stops", "length_km", "service_span_h", "trips_morning", "trips_afternoon", "trips_evening", "trips_night"]].sort_values(["n_trips", "length_km"])


def corr_table(rf, cols=None):
    cols = [c for c in (cols or ["n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "stops_per_km",
                                  "avg_speed_kmh", "max_stop_overlap", "mean_routes_per_stop", "trips_per_active_hour"]) if c in rf]
    return rf[cols].corr(method="spearman").round(2)


def outlier_table(rf, cols=("n_trips", "n_unique_stops", "length_km", "service_span_h", "median_headway_min", "avg_speed_kmh")):
    """Tukey fences (1.5 x IQR) on log1p for the strongly skewed count/length features, raw for the rest."""
    rows = []
    for c in cols:
        if c not in rf:
            continue
        x = rf[c].dropna(); y = np.log1p(x) if c in ("n_trips", "n_unique_stops", "length_km", "median_headway_min") else x
        q1, q3 = y.quantile([.25, .75]); lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        low, high = x[y < lo], x[y > hi]
        rows.append(dict(feature=c, min=round(x.min(), 2), median=round(x.median(), 2), max=round(x.max(), 2),
                         n_low_outliers=len(low), n_high_outliers=len(high), outliers_pct=round(100 * (len(low) + len(high)) / len(x), 1)))
    return pd.DataFrame(rows)


def outlier_investigation(rf):
    """Classify unusual values with evidence instead of deleting them.
    valid-but-unusual: value is consistent with the route's other attributes; suspect: contradicts them; source limitation: property of the feed."""
    rows = []
    sp = rf.avg_speed_kmh
    n_bad_speed = int(rf.speed_implausible.sum())
    rows.append(dict(check="scheduled speed < 3 or > 80 km/h", routes=n_bad_speed, pct=round(100 * n_bad_speed / len(rf), 1),
                     reading="suspect: length, duration or both look wrong for these routes (check publisher / shape); flagged, not deleted"))
    big = rf.length_km > rf.length_km.quantile(.75) + 3 * (rf.length_km.quantile(.75) - rf.length_km.quantile(.25))
    cons = big & ~rf.speed_implausible
    rows.append(dict(check="very long routes (> Q3 + 3 IQR)", routes=int(big.sum()), pct=round(100 * big.mean(), 1),
                     reading=f"{int(cons.sum())} of them have a plausible scheduled speed -> valid but unusual (long-distance routes); {int((big & rf.speed_implausible).sum())} do not -> suspect"))
    hi = rf.n_trips > rf.n_trips.quantile(.75) + 3 * (rf.n_trips.quantile(.75) - rf.n_trips.quantile(.25))
    multi = hi & (rf.n_service_ids > 1) if "n_service_ids" in rf else hi & False
    rows.append(dict(check="very many scheduled trips (> Q3 + 3 IQR)", routes=int(hi.sum()), pct=round(100 * hi.mean(), 1),
                     reading=f"{int(multi.sum())} combine several service patterns (counts add up alternative timetables); the rest are valid high-frequency routes or a feed property"))
    one = rf.n_trips < 3
    rows.append(dict(check="routes with fewer than 3 scheduled trips", routes=int(one.sum()), pct=round(100 * one.mean(), 1),
                     reading="valid but sparse; headway undefined for many; NOT evidence of inefficiency"))
    rows.append(dict(check="missing median headway (single departure time)", routes=int(rf.median_headway_min.isna().sum()), pct=round(100 * rf.median_headway_min.isna().mean(), 1),
                     reading="undefined, not zero; kept missing"))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ charts (each returns a Figure)
def _fin(fig, ax_title=None):
    fig.tight_layout()
    return fig


def f_hist(rf, col, city, log_x=False, bins=40):
    x = rf[col].dropna()
    fig, ax = plt.subplots(figsize=(7, 4))
    sns.histplot(x, bins=bins, log_scale=log_x, ax=ax, color="#3a86a8")
    ax.axvline(x.median(), color="crimson", ls="--", label=f"median = {x.median():.1f}")
    ax.set_title(f"{city.title()}: distribution of {LABELS.get(col, col)}"); ax.set_xlabel(LABELS.get(col, col) + (" (log scale)" if log_x else ""))
    ax.set_ylabel("number of routes"); ax.legend()
    return _fin(fig)


def f_box_panel(rf, city, cols=("n_trips", "n_unique_stops", "length_km", "service_span_h")):
    cols = [c for c in cols if c in rf]
    fig, axes = plt.subplots(1, len(cols), figsize=(3.6 * len(cols), 4))
    for ax, c in zip(np.atleast_1d(axes), cols):
        sns.boxplot(y=rf[c], ax=ax, color="#8ecae6", fliersize=2)
        if c in ("n_trips", "n_unique_stops", "length_km"):
            ax.set_yscale("log")
        ax.set_ylabel(LABELS.get(c, c)); ax.set_title(c)
    fig.suptitle(f"{city.title()}: box plots of route features (log scale where skewed)")
    return _fin(fig)


def f_hourly(h, city, col="scheduled_trips", title=None):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(h.index, h[col], color=[PERIOD_COLORS[p] for p in h.period])
    ax.set_xticks(range(24)); ax.set_xlabel("clock hour of first departure"); ax.set_ylabel("distinct scheduled trips")
    ax.set_title(title or f"{city.title()}: scheduled trips starting in each hour (planned supply, not passenger demand)")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=PERIOD_COLORS[p], label=p) for p in PERIOD_ORDER], title="period", ncol=4,
              loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
    return _fin(fig)


def f_period(p, city):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(p.index, p.scheduled_trips, color=[PERIOD_COLORS[x] for x in p.index])
    for i, (v, s) in enumerate(zip(p.scheduled_trips, p["share_%"])):
        ax.text(i, v, f"{s}%", ha="center", va="bottom")
    ax.set_title(f"{city.title()}: scheduled trips by time period"); ax.set_xlabel("period (morning 05-11:59, afternoon 12-16:59, evening 17-20:59, night 21-04:59)")
    ax.set_ylabel("distinct scheduled trips")
    return _fin(fig)


def f_weekday_sunday(h, city):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(h.index, h.trips_weekday_wed, marker="o", label="typical weekday (Wednesday service)")
    ax.plot(h.index, h.trips_sunday, marker="s", ls="--", label="Sunday service")
    ax.set_xticks(range(24)); ax.set_xlabel("clock hour of first departure"); ax.set_ylabel("distinct scheduled trips")
    ax.set_title(f"{city.title()}: weekday vs Sunday scheduled trips by hour"); ax.legend()
    return _fin(fig)


def f_top_routes(rf, city, n=15):
    t = rf.nlargest(n, "n_trips").iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    ax.barh(t.route_name.astype(str), t.n_trips, color="#457b9d")
    ax.set_title(f"{city.title()}: {n} routes with the most scheduled trips"); ax.set_xlabel("distinct scheduled trips"); ax.set_ylabel("route name")
    return _fin(fig)


def f_scatter(rf, x, y, city, log_y=True):
    d = rf[[x, y]].dropna()
    rho = d.corr(method="spearman").iloc[0, 1]
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.scatter(d[x], d[y], s=10, alpha=.4, color="#1d3557")
    if log_y: ax.set_yscale("log")
    ax.set_xlabel(LABELS.get(x, x)); ax.set_ylabel(LABELS.get(y, y))
    ax.set_title(f"{city.title()}: {y} vs {x} (Spearman rho = {rho:.2f})")
    return _fin(fig)


def f_corr(rf, city):
    c = corr_table(rf)
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(c, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax, annot_kws={"size": 8})
    ax.set_title(f"{city.title()}: Spearman correlation of route features (association, not causation)")
    return _fin(fig)


def f_outliers(rf, city):
    return f_box_panel(rf, city, cols=("n_trips", "n_unique_stops", "length_km", "avg_speed_kmh", "median_headway_min"))


# ------------------------------------------------------------------ geography
def stop_map(su, city, path):
    """Folium heat map of stop locations weighted by the number of routes calling there."""
    import folium
    from folium.plugins import HeatMap
    s = su.dropna(subset=["stop_lat", "stop_lon"])
    m = folium.Map(location=[s.stop_lat.median(), s.stop_lon.median()], zoom_start=11, tiles="OpenStreetMap")
    HeatMap(s[["stop_lat", "stop_lon", "n_routes"]].values.tolist(), radius=9, blur=12, min_opacity=.3).add_to(m)
    top = s.nlargest(15, "n_routes")
    for r in top.itertuples():
        folium.CircleMarker([r.stop_lat, r.stop_lon], radius=5, color="crimson", fill=True,
                            tooltip=f"{r.stop_name}: {r.n_routes} routes, {r.scheduled_visits} scheduled calls").add_to(m)
    m.save(path)
    return m


def draw_routes_map(shapes, trip_shape, routes, path):
    """Draw shapes.txt paths. `routes` = list of (route_id, label). One shape (most used) per route."""
    import folium
    colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "black", "pink", "gray"]
    rep = trip_shape.dropna().groupby("route_id").shape_id.agg(lambda x: x.value_counts().index[0])
    sh = shapes[shapes.shape_id.isin([rep[r] for r, _ in routes if r in rep.index])]
    m, pts_all = None, []
    for col, (rid, label) in zip(colors, routes):
        if rid not in rep.index:
            continue
        pts = sh[sh.shape_id == rep[rid]].copy()
        pts["seq"] = pts.shape_pt_sequence.astype(float)
        xy = pts.sort_values("seq")[["shape_pt_lat", "shape_pt_lon"]].astype(float).values.tolist()
        if m is None:
            m = folium.Map(location=xy[len(xy) // 2], zoom_start=11, tiles="OpenStreetMap")
        folium.PolyLine(xy, color=col, weight=4, opacity=.8, tooltip=label).add_to(m)
    if m is not None:
        m.save(path)
    return m


def shape_overlap(rf, shapes, trip_shape, cell=0.002):
    """Path overlap from shapes.txt: each route's longest shape is turned into a set of ~200 m grid cells;
    Jaccard similarity of two cell sets = share of the road corridor they have in common.
    Same-name routes and opposite-direction twins (start/end swapped) are excluded. Returns one row per route."""
    from scipy import sparse
    sh = shapes[shapes.shape_id.isin(set(trip_shape.shape_id.dropna()))].copy()
    sh["lat"] = sh.shape_pt_lat.astype(float); sh["lon"] = sh.shape_pt_lon.astype(float); sh["seq"] = sh.shape_pt_sequence.astype(float)
    sh = sh.sort_values(["shape_id", "seq"])
    sh["cell"] = (sh.lat // cell).astype(int).astype(str) + "_" + (sh.lon // cell).astype(int).astype(str)
    ends = sh.groupby("shape_id").agg(first=("cell", "first"), last=("cell", "last"))
    ends["fc"] = ((sh.groupby("shape_id").lat.first() // 0.01).astype(int).astype(str) + "_" + (sh.groupby("shape_id").lon.first() // 0.01).astype(int).astype(str))
    ends["lc"] = ((sh.groupby("shape_id").lat.last() // 0.01).astype(int).astype(str) + "_" + (sh.groupby("shape_id").lon.last() // 0.01).astype(int).astype(str))
    # representative shape per route = the one used by most trips of the route
    rep = trip_shape.dropna().groupby("route_id").shape_id.agg(lambda x: x.value_counts().index[0])
    rep = rep[rep.index.isin(rf.route_id) & rep.isin(ends.index)]
    cells = sh[sh.shape_id.isin(rep.values)].drop_duplicates(["shape_id", "cell"])
    shape_idx = {s: i for i, s in enumerate(rep.values)}
    cell_idx = {c: i for i, c in enumerate(cells.cell.unique())}
    X = sparse.csr_matrix((np.ones(len(cells), dtype=np.float32), (cells.shape_id.map(shape_idx).values, cells.cell.map(cell_idx).values)),
                          shape=(len(rep), len(cell_idx)))
    size = np.asarray(X.sum(axis=1)).ravel()
    inter = (X @ X.T).toarray()
    with np.errstate(invalid="ignore", divide="ignore"):
        J = inter / (size[:, None] + size[None, :] - inter)
    J = np.nan_to_num(J, nan=-1.0)          # a route with an empty cell set has no overlap partner
    names = rf.set_index("route_id").route_name.reindex(rep.index).astype(str).to_numpy(dtype=object)
    codes = pd.factorize(names)[0]
    J[codes[:, None] == codes[None, :]] = -1                       # same line name
    fc, lc = ends.loc[rep.values, "fc"].to_numpy(dtype=object), ends.loc[rep.values, "lc"].to_numpy(dtype=object)
    J[(fc[:, None] == lc[None, :]) & (lc[:, None] == fc[None, :])] = -1   # opposite direction
    np.fill_diagonal(J, -1)
    j = J.argmax(axis=1)
    ids = rep.index.to_numpy(dtype=object)
    out = pd.DataFrame({"route_id": ids, "shape_overlap_partner": ids[j], "shape_overlap_jaccard": J[np.arange(len(j)), j]})
    out["shape_overlap_partner_name"] = out.shape_overlap_partner.map(rf.set_index("route_id").route_name)
    return out.loc[out.shape_overlap_jaccard > 0]


# ------------------------------------------------------------------ data-driven observations (text computed from the data)
def _strength(r):
    a = abs(r)
    return "almost no association" if a < .2 else "a weak association" if a < .4 else "a moderate association" if a < .7 else "a strong association"


def timing_caveats(rf):
    """Feed-level warnings derived from the data itself."""
    out = []
    if (rf.median_trip_duration_min > 480).mean() > .2:
        out.append(f"{100 * (rf.median_trip_duration_min > 480).mean():.0f}% of routes have a median scheduled trip longer than 8 hours: the feed's 'trips' appear to be whole vehicle duties, so trip counts and headways are NOT comparable with cities whose trips are single runs.")
    spread = rf.avg_speed_kmh.quantile(.9) - rf.avg_speed_kmh.quantile(.1)
    if spread < 3:
        out.append(f"Scheduled speed is almost identical on all routes (10th-90th percentile {rf.avg_speed_kmh.quantile(.1):.1f}-{rf.avg_speed_kmh.quantile(.9):.1f} km/h), suggesting generated rather than operational stop times; durations and headways should be read as a model schedule.")
    if "trips_from_frequency" in rf and (rf.trips_from_frequency > 0).mean() > .5:
        out.append("Trip counts come from expanding frequency templates (a bus every N minutes), so routes look uniform because the publisher used a uniform pattern; this is not measured service.")
    return out


def obs_univariate(rf):
    t, st, l, sp = rf.n_trips, rf.n_unique_stops, rf.length_km, rf.service_span_h
    q1, q3 = l.quantile([.25, .75])
    L = [f"{len(rf):,} routes in the dataset. Scheduled trips per route: median {t.median():.0f}, mean {t.mean():.1f}, maximum {t.max():,} ({t.max() / t.median():.0f} times the median). "
         f"{100 * (t <= 5).mean():.0f}% of routes have 5 or fewer scheduled trips and {100 * (t >= 50).mean():.0f}% have 50 or more, so service levels differ widely between routes.",
         f"Distinct stops per route: median {st.median():.0f} (range {st.min()}-{st.max()}).",
         f"Estimated route length: median {l.median():.1f} km (middle half of routes {q1:.1f}-{q3:.1f} km). {100 * (rf.length_method == 'shapes.txt').mean():.0f}% of lengths come from shapes.txt; the rest are straight-line stop-to-stop distances, which understate road length.",
         f"Scheduled service span (first to last departure): median {sp.median():.1f} h; {100 * (sp >= 12).mean():.0f}% of routes span 12 hours or more."]
    if "weekend_to_weekday_ratio" in rf and rf.weekend_to_weekday_ratio.notna().any():
        same = (rf.weekend_to_weekday_ratio.dropna().round(6) == 1).mean()
        L.append(f"Operating days: {100 * same:.0f}% of routes have the same number of scheduled trips on weekend days as on weekdays according to calendar.txt.")
    return L


def obs_hourly(h, p):
    top, low = h.scheduled_trips.nlargest(3), h.scheduled_trips.nsmallest(3)
    zero = [f"{i:02d}" for i in h.index[h.scheduled_trips == 0]]
    L = ["Hours with the most scheduled trip starts: " + ", ".join(f"{i:02d}:00 ({v:,})" for i, v in top.items()) + ". Hours with the fewest: " + ", ".join(f"{i:02d}:00 ({v:,})" for i, v in low.items())
         + (f". No trip starts at all in hours {', '.join(zero)}." if zero else "."),
         "By period: " + "; ".join(f"{k} {r['share_%']}% of scheduled trips ({int(r.trips_per_hour):,} per hour)" for k, r in p.iterrows())
         + f". The busiest period per hour is {p.trips_per_hour.idxmax()} and the quietest is {p.trips_per_hour.idxmin()}. These are planned services, not passenger numbers; strong concentration in a few hours can also reflect how the publisher compiled the timetable, so it should be checked with the operator before it is read as a real service pattern."]
    if "trips_weekday_wed" in h:
        wd, su = h.trips_weekday_wed.sum(), h.trips_sunday.sum()
        L.append(f"Weekday vs weekend: scheduled trips on a typical weekday (Wednesday services) {wd:,}; on Sunday {su:,} ({100 * su / wd:.0f}% of the weekday level)."
                 + (" The calendar describes identical service on both days." if wd == su else ""))
    return L


def obs_routes(rf, groups):
    lo, hi = groups.loc["low (<= Q1)"], groups.loc["high (>= Q3)"]
    L = [f"Routes in the lowest quarter of scheduled trips (<= {lo.n_trips:.0f}) have a median of {lo.n_unique_stops:.0f} stops and {lo.length_km:.1f} km; routes in the highest quarter (>= {hi.n_trips:.0f} trips) have {hi.n_unique_stops:.0f} stops and {hi.length_km:.1f} km.",
         f"Median service span: {lo.service_span_h:.1f} h (low-trip group) vs {hi.service_span_h:.1f} h (high-trip group)."
         + (" A route with a single trip has a span of 0 by definition, so this difference is partly built in." if lo.n_trips <= 1 else "")
         + " It describes what the schedule looks like - not whether a route is efficient.",
         "Most stops on one route: " + ", ".join(f"{r.route_name} ({r.n_unique_stops})" for r in rf.nlargest(3, "n_unique_stops").itertuples()) + ". Most scheduled trips: " + ", ".join(f"{r.route_name} ({r.n_trips:,})" for r in rf.nlargest(3, "n_trips").itertuples()) + "."]
    return L


def obs_corr(rf):
    pairs = [("length_km", "n_trips"), ("n_unique_stops", "n_trips"), ("length_km", "n_unique_stops"), ("length_km", "median_headway_min")]
    L = []
    for a, b in pairs:
        d = rf[[a, b]].dropna()
        if len(d) > 10:
            r = d.corr(method="spearman").iloc[0, 1]
            L.append(f"{a} vs {b}: Spearman rho = {r:.2f} -> {_strength(r)} ({'longer/larger routes tend to have higher values of both' if r > .2 else 'larger values of one tend to go with smaller values of the other' if r < -.2 else 'the two vary almost independently'}).")
    return L


def obs_overlap(rf, ov, shape_ov=None):
    L = [f"Stop-based overlap (Jaccard similarity of the stop sets of two routes): {int((rf.max_stop_overlap >= .8).sum())} routes have a partner with >= 80% similar stops, {int((rf.max_stop_overlap >= .5).sum())} with >= 50% ({len(ov)} distinct pairs at >= 80%). "
         "Same-name routes and opposite-direction twins are excluded. Sharing stops does not prove that two routes are redundant."]
    if shape_ov is not None:
        L.append(f"Path-based overlap from shapes.txt (~200 m grid cells): {int((shape_ov.shape_overlap_jaccard >= .8).sum())} routes share >= 80% of their corridor with another route, {int((shape_ov.shape_overlap_jaccard >= .5).sum())} share >= 50%.")
    return L


def analyze(city, base="data/processed"):
    rf, rh, su = load(city, base)
    h = hourly_table(rh)
    R = dict(city=city, rf=rf, rh=rh, su=su, h=h, p=period_table(h), groups=group_comparison(rf),
             ov=overlap_candidates(rf, .8), low=low_service_candidates(rf), info=inspect_table(rf),
             desc=describe(rf), corr=corr_table(rf), out=outlier_table(rf), inv=outlier_investigation(rf),
             shapes=None, trip_shape=None, shape_ov=None)
    raw, tfp = f"data/raw/{city}/shapes.txt", f"{base}/{city}/trip_features.csv"
    if os.path.exists(raw) and os.path.exists(tfp) and (rf.length_method == "shapes.txt").any():
        R["trip_shape"] = pd.read_csv(tfp, usecols=["route_id", "shape_id"], dtype=str).drop_duplicates()
        R["shapes"] = pd.read_csv(raw, dtype={"shape_id": str})
        R["shape_ov"] = shape_overlap(rf, R["shapes"], R["trip_shape"])
    return R




def f_stop_scatter(su, city):
    """Static map of stop locations coloured by the number of routes calling there."""
    s = su.dropna(subset=["stop_lat", "stop_lon"]).sort_values("n_routes")
    fig, ax = plt.subplots(figsize=(6.5, 6))
    sc = ax.scatter(s.stop_lon, s.stop_lat, c=s.n_routes, s=4, cmap="YlOrRd", norm=matplotlib.colors.LogNorm())
    fig.colorbar(sc, ax=ax, label="routes calling at the stop (log scale)")
    ax.set_title(f"{city.title()}: stop locations (longitude / latitude)"); ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
    ax.set_aspect(1 / np.cos(np.radians(s.stop_lat.median())))
    return _fin(fig)


def f_shapes_static(shapes, trip_shape, routes, city):
    """Static drawing of shapes.txt paths for chosen routes: routes = list of (route_id, label)."""
    rep = trip_shape.dropna().groupby("route_id").shape_id.agg(lambda x: x.value_counts().index[0])
    sh = shapes[shapes.shape_id.isin([rep[r] for r, _ in routes if r in rep.index])].copy()
    sh["seq"] = sh.shape_pt_sequence.astype(float)
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for rid, label in routes:
        if rid in rep.index:
            p = sh[sh.shape_id == rep[rid]].sort_values("seq")
            ax.plot(p.shape_pt_lon.astype(float), p.shape_pt_lat.astype(float), lw=1.8, label=label)
    ax.set_title(f"{city.title()}: route paths from shapes.txt"); ax.set_xlabel("longitude"); ax.set_ylabel("latitude"); ax.legend(fontsize=7)
    ax.set_aspect(1 / np.cos(np.radians(sh.shape_pt_lat.astype(float).median())))
    return _fin(fig)
