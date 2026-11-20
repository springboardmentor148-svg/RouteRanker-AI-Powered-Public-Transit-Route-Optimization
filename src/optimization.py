"""Module 6 - investigation candidates, optimisation suggestions (merge / split / frequency) and a SIMULATED network.

Everything is derived from SCHEDULE data. No passenger, demand or capacity value exists in the data, so none is used or invented:
suggestions are candidates to verify, and the simulation changes only a copy of the schedule features under stated assumptions.
"""
import numpy as np
import pandas as pd

MERGE_JACCARD, MERGE_LOW_Q, MERGE_LEN_RATIO = 0.80, 0.25, 1.5
SPLIT_MIN_KM, SPLIT_LEN_Q, SPLIT_MIN_STOPS = 40.0, 0.90, 30
FREQ_MIN_TRIPS, FREQ_HEADWAY_STANDARD = 6, 30          # standard in minutes -> at least 60/30 = 2 departures in the route's busiest hour
FREQ_NEED = int(np.ceil(60 / FREQ_HEADWAY_STANDARD))


# ------------------------------------------------------------------ multi-evidence screening
def evidence_flags(df, sparse_clusters, overlap_min=MERGE_JACCARD):
    """Independent evidence flags from the models and the schedule. One flag alone is never enough."""
    d = df.copy()
    d["ev_dbscan_noise"] = d.dbscan_label == -1
    d["ev_sparse_cluster"] = d.kmeans_cluster.isin(sparse_clusters)
    d["ev_high_stop_overlap"] = d.max_stop_overlap >= overlap_min
    # low service compared with routes of similar length in the same city (length quintiles)
    q = d.groupby("city").length_km.transform(lambda s: pd.qcut(s, 5, labels=False, duplicates="drop"))
    grp = d.assign(q=q).groupby(["city", "q"]).n_trips
    thr, med = grp.transform(lambda s: s.quantile(.25)), grp.transform("median")
    # 'few trips for its length' only means something when peers differ: if the 25th percentile equals the median (e.g. a feed built from one
    # uniform frequency template) no route is called lightly scheduled
    d["ev_low_trips_for_length"] = (d.n_trips <= thr) & (thr < med)
    flags = ["ev_dbscan_noise", "ev_sparse_cluster", "ev_high_stop_overlap", "ev_low_trips_for_length"]
    d["n_evidence"] = d[flags].sum(axis=1)
    d["data_check_first"] = d.speed_invalid.astype(bool)     # an unreliable speed means the length/timetable needs checking before anything else
    return d, flags


# ------------------------------------------------------------------ suggestions
def merge_candidates(rf, jac_min=MERGE_JACCARD, low_q=MERGE_LOW_Q, len_ratio=MERGE_LEN_RATIO):
    """Route r (the lighter one) is a candidate to be merged into its best stop-sharing partner p: different line names, >= 80% similar stop sets
    (geographical connectivity), r is lightly scheduled (<= 25th percentile of its city), and similar length (ratio <= 1.5)."""
    out = []
    for city, g in rf.groupby("city"):
        idx = g.set_index("route_id")
        q = g.n_trips.quantile(low_q)
        if q >= g.n_trips.median():        # uniform trip counts (e.g. frequency-template feed): no route is lightly scheduled relative to its peers
            continue
        c = g[(g.max_stop_overlap >= jac_min) & g.overlap_partner.isin(idx.index)].copy()
        if c.empty:                        # strict thresholds can leave no candidate in a city (an empty string column cannot be compared with numbers)
            continue
        c["p_trips"] = c.overlap_partner.map(idx.n_trips); c["p_len"] = c.overlap_partner.map(idx.length_km)
        c = c[(c.n_trips <= c.p_trips) & (c.n_trips <= q) & (c.length_km / c.p_len).between(1 / len_ratio, len_ratio)]
        absorbed, targets = set(), set()
        for r in c.sort_values(["max_stop_overlap", "n_trips"], ascending=[False, True]).itertuples():
            if r.route_id in targets or r.overlap_partner in absorbed:
                continue
            absorbed.add(r.route_id); targets.add(r.overlap_partner)
            out.append(dict(city=city, absorbed_route_id=r.route_id, absorbed_route=r.route_name, target_route_id=r.overlap_partner,
                            target_route=idx.route_name[r.overlap_partner], stop_overlap_jaccard=round(r.max_stop_overlap, 3),
                            share_of_absorbed_stops_also_on_target=round(r.overlap_share_of_route, 3), trips_absorbed=int(r.n_trips),
                            trips_target=int(r.p_trips), length_absorbed_km=round(r.length_km, 1), length_target_km=round(r.p_len, 1),
                            stops_absorbed=int(r.n_unique_stops)))
    return pd.DataFrame(out)


def split_candidates(rf, exclude_ids=(), min_km=SPLIT_MIN_KM, len_q=SPLIT_LEN_Q, min_stops=SPLIT_MIN_STOPS):
    out = []
    for city, g in rf.groupby("city"):
        thr = max(min_km, g.length_km.quantile(len_q))
        s = g[(g.length_km >= thr) & (g.n_unique_stops >= min_stops) & (~g.speed_invalid.astype(bool)) & (~g.route_id.isin(exclude_ids))]
        for r in s.itertuples():
            out.append(dict(city=city, route_id=r.route_id, route=r.route_name, length_km=round(r.length_km, 1), length_method=r.length_method,
                            stops=int(r.n_unique_stops), trips=int(r.n_trips), service_span_h=round(r.service_span_h, 1)))
    return pd.DataFrame(out)


def frequency_candidates(rf, exclude_ids=(), min_trips=FREQ_MIN_TRIPS, standard=FREQ_HEADWAY_STANDARD):
    """Assumption-based service-standard check (NOT demand-based): routes with >= 6 scheduled trips that have fewer than 2 departures in their
    busiest hour, i.e. a headway above 30 minutes even at their own peak."""
    need = int(np.ceil(60 / standard))
    s = rf[(rf.n_trips >= min_trips) & (rf.peak_hour_trips < need) & (~rf.route_id.isin(exclude_ids))]
    return pd.DataFrame(dict(city=s.city, route_id=s.route_id, route=s.route_name, trips=s.n_trips, peak_hour=s.peak_hour,
                             departures_in_peak_hour=s.peak_hour_trips, trips_to_add=need - s.peak_hour_trips)).reset_index(drop=True)


# ------------------------------------------------------------------ simulation (on a COPY)
SIMCOLS = ["city", "route_id", "route_name", "n_trips", "n_unique_stops", "length_km", "peak_hour_trips"]


def simulate(rf, merges, splits, freqs, scenario="combined"):
    """Return the simulated route table (a COPY; the original data is never changed). route_id is only unique within a city, so routes are
    addressed by (city, route_id). Order of precedence in the combined network: merge > split > frequency (a route is changed once).
    Assumptions (also written in the report):
    * merge: the absorbed route's departures are kept (trips preserved); length grows by the unshared part of the absorbed route
      (length x (1 - shared-stop share)); stops grow likewise; the absorbed route disappears.
    * split: the route is cut at its middle stop into two routes of half length; each part keeps all original departures
      (scheduled trip-km unchanged, trip records double); transfer burden is ignored.
    * frequency: trips are added until the busiest hour has the standard number of departures."""
    sim = rf[SIMCOLS].copy()
    sim.index = pd.MultiIndex.from_arrays([sim.city, sim.route_id], names=["c", "r"])
    sim["status"] = "unchanged"
    used = set()
    if scenario in ("merge", "combined") and len(merges):
        for (city, t), g in merges.groupby(["city", "target_route_id"]):
            for r in g.itertuples():
                keep = 1 - r.share_of_absorbed_stops_also_on_target
                sim.loc[(city, t), "n_trips"] += r.trips_absorbed
                sim.loc[(city, t), "length_km"] += r.length_absorbed_km * keep
                sim.loc[(city, t), "n_unique_stops"] += int(round(r.stops_absorbed * keep))
            sim.loc[(city, t), "status"] = "merge_target"
            used.add((city, t))
        gone = list(zip(merges.city, merges.absorbed_route_id))
        sim = sim.drop(index=gone)
        used |= set(gone)
    rows = []
    if scenario in ("split", "combined") and len(splits):
        sp = splits[[(c, r) not in used for c, r in zip(splits.city, splits.route_id)]]
        for r in sp.itertuples():
            base = sim.loc[(r.city, r.route_id)]
            for part in ("A", "B"):
                rows.append(dict(city=base.city, route_id=f"{r.route_id}_{part}", route_name=f"{base.route_name} ({part})", n_trips=base.n_trips,
                                 n_unique_stops=int(np.ceil(base.n_unique_stops / 2)) + 1, length_km=base.length_km / 2, peak_hour_trips=base.peak_hour_trips,
                                 status=f"split_part_{part}"))
        gone = list(zip(sp.city, sp.route_id))
        sim = sim.drop(index=gone)
        used |= set(gone)
    if scenario in ("frequency", "combined") and len(freqs):
        fq = freqs[[(c, r) not in used for c, r in zip(freqs.city, freqs.route_id)]]
        for r in fq.itertuples():
            sim.loc[(r.city, r.route_id), "n_trips"] += r.trips_to_add
            sim.loc[(r.city, r.route_id), "peak_hour_trips"] += r.trips_to_add
            sim.loc[(r.city, r.route_id), "status"] = "frequency_adjusted"
    out = sim.reset_index(drop=True)
    if rows:
        out = pd.concat([out, pd.DataFrame(rows)], ignore_index=True)
    return out


def metrics(df, min_trips=FREQ_MIN_TRIPS, standard=FREQ_HEADWAY_STANDARD, long_km=SPLIT_MIN_KM):
    need = int(np.ceil(60 / standard))
    sparse_peak = ((df.n_trips >= min_trips) & (df.peak_hour_trips < need)).sum()
    return dict(routes=len(df), scheduled_trips=int(df.n_trips.sum()), est_route_distance_km=round(df.length_km.sum(), 1),
                avg_route_length_km=round(df.length_km.mean(), 2), scheduled_trip_km=round((df.n_trips * df.length_km).sum(), 1),
                avg_trips_per_route=round(df.n_trips.mean(), 2), routes_over_40km=int((df.length_km >= long_km).sum()),
                routes_with_under_2_departures_in_peak_hour=int(sparse_peak))
