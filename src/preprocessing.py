"""Module 4 - preprocessing of the Module-2 route features for the planned UNSUPERVISED models (KMeans, DBSCAN).

GTFS has no passenger data, so no performance label / demand value is created here. Every statistic that is
learned from data (medians, skewness decisions, means, standard deviations, category lists, correlation drops) is
fitted on the TRAINING routes only and then applied unchanged to the validation routes - no data leakage.
"""
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ID_COLS = ["city", "route_id", "route_name"]
NUMERIC = ["n_trips", "n_unique_stops", "median_stops_per_trip", "length_km", "service_span_h", "n_active_hours",
           "trips_per_active_hour", "median_headway_min", "avg_trip_duration_min", "stops_per_km", "avg_speed_kmh",
           "max_stop_overlap", "mean_routes_per_stop", "weekend_to_weekday_ratio",
           "share_morning", "share_afternoon", "share_evening"]   # the 4 period shares sum to 1: share_night is implied, so it is left out
CATEGORICAL = ["length_method", "peak_period"]
# Feeds whose route features are NOT comparable with the others (documented in Module 2 / 3)
EXCLUDE_FEEDS = {"hyderabad": "trips look like whole vehicle duties (about 68% last over 8 hours), so n_trips, headway, "
                              "duration and speed do not mean the same as in the other feeds"}
SPEED_RANGE = (3, 80)      # km/h; outside this the scheduled speed is treated as invalid
SKEW_LIMIT = 1.0           # |skewness| above this (on training data) -> log1p
CONSTANT_SHARE = 0.95      # a feature whose most frequent value covers > 95% of training routes carries almost no information
CORR_LIMIT = 0.95          # of two features correlated above this, the later one in NUMERIC order is dropped


def period_of_hour(h):
    h = pd.Series(h)
    return np.select([h.between(5, 11), h.between(12, 16), h.between(17, 20)], ["morning", "afternoon", "evening"], default="night")


def load_features(path="data/processed/all_cities_route_features.csv"):
    return pd.read_csv(path, dtype={"route_id": str, "route_name": str})


def add_derived(df):
    """Derived columns needed for modelling. Nothing is invented: shares and a period label are recomputed from existing columns."""
    d = df.copy()
    for p in ["morning", "afternoon", "evening", "night"]:
        d[f"share_{p}"] = d[f"trips_{p}"] / d.n_trips          # n_trips >= 1 for every route in the feature table
    d["peak_period"] = period_of_hour(d.peak_hour)
    bad = ~d.avg_speed_kmh.between(*SPEED_RANGE)
    d["speed_invalid"] = bad.astype(int)
    d.loc[bad, "avg_speed_kmh"] = np.nan                        # an impossible speed is an invalid value, not a measurement
    return d


def split_exclusions(df, exclude=EXCLUDE_FEEDS):
    mask = df.city.isin(exclude)
    ex = df.loc[mask, ["city", "route_id", "route_name"]].copy()
    ex["reason"] = ex.city.map(exclude)
    return df.loc[~mask].copy(), ex


def missing_report(df, cols):
    rows = []
    for c in cols:
        n = int(df[c].isna().sum())
        if n:
            per = df.groupby("city")[c].apply(lambda s: s.isna().mean()).round(3)
            rows.append(dict(column=c, missing=n, pct=round(100 * n / len(df), 2),
                             worst_city=per.idxmax(), worst_city_pct=round(100 * per.max(), 1)))
    return pd.DataFrame(rows)


def train_validation_split(df, test_size=0.2, seed=42):
    """80:20 split by route NAME within city, so the up/down/variant routes of one bus line never sit on both sides."""
    groups = df.city + "|" + df.route_name
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    tr, va = next(gss.split(df, groups=groups))
    return df.iloc[tr].copy(), df.iloc[va].copy()


class RoutePreprocessor:
    """fit() learns everything from the training routes; transform() applies it to any routes."""

    def fit(self, train):
        X = train[NUMERIC]
        self.dropped_constant = [c for c in NUMERIC if X[c].dropna().value_counts(normalize=True).iloc[0] > CONSTANT_SHARE]
        self.num = [c for c in NUMERIC if c not in self.dropped_constant]
        self.has_missing = [c for c in self.num if X[c].isna().any()]
        self.imputer = SimpleImputer(strategy="median").fit(train[self.num])
        imp = pd.DataFrame(self.imputer.transform(train[self.num]), columns=self.num, index=train.index)
        skew = imp.skew()
        self.log_cols = [c for c in self.num if skew[c] > SKEW_LIMIT and imp[c].min() >= 0]
        imp[self.log_cols] = np.log1p(imp[self.log_cols])
        self.scaler = StandardScaler().fit(imp)
        sc = pd.DataFrame(self.scaler.transform(imp), columns=self.num, index=train.index)
        self.dropped_corr = []
        corr = sc.corr().abs()
        for i, a in enumerate(self.num):
            for b in self.num[i + 1:]:
                if a not in self.dropped_corr and b not in self.dropped_corr and corr.loc[a, b] > CORR_LIMIT:
                    self.dropped_corr.append(b)
        self.num_final = [c for c in self.num if c not in self.dropped_corr]
        self.ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False).fit(train[CATEGORICAL])
        self.skew_before = skew
        self.corr_pairs = [(a, b, round(float(corr.loc[a, b]), 3)) for i, a in enumerate(self.num) for b in self.num[i + 1:] if corr.loc[a, b] > CORR_LIMIT]
        return self

    def transform(self, df):
        imp = pd.DataFrame(self.imputer.transform(df[self.num]), columns=self.num, index=df.index)
        out = pd.DataFrame(index=df.index)
        for c in self.has_missing:                       # keep the information "this value was missing / invalid"
            if c in self.num_final:
                out[f"{c}_was_missing"] = df[c].isna().astype(int)
        imp[self.log_cols] = np.log1p(imp[self.log_cols])
        sc = pd.DataFrame(self.scaler.transform(imp), columns=self.num, index=df.index)[self.num_final]
        enc = pd.DataFrame(self.ohe.transform(df[CATEGORICAL]), index=df.index,
                           columns=[f"{c}__{v}" for c, vs in zip(CATEGORICAL, self.ohe.categories_) for v in vs])
        return pd.concat([out, sc, enc], axis=1)

    @property
    def feature_names(self):
        flag = [f"{c}_was_missing" for c in self.has_missing if c in self.num_final]
        enc = [f"{c}__{v}" for c, vs in zip(CATEGORICAL, self.ohe.categories_) for v in vs]
        return flag + self.num_final + enc
