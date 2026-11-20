"""Random Forest and XGBoost predictions. The models are the ones saved in Module 5 and are applied live; no value is typed in.

The supervised target is the CITY of a route (the only real label in GTFS-based data): it shows which known feed a route resembles. It is NOT a route-quality or
demand prediction."""
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from src import inference as inf
from . import data_loader as dl

IDS = ["city", "route_id", "route_name"]


@st.cache_data(show_spinner=False)
def classes():
    return sorted(pd.read_csv(f"{dl.PROC}/module4/train_preprocessed.csv", usecols=["city"]).city.unique())


@st.cache_data(show_spinner="Evaluating the saved models on the held-out validation routes ...")
def validation_evaluation():
    models, va, cls = dl.load_models(), dl.load_module4_validation(), classes()
    feats = [c for c in va.columns if c not in IDS]
    X, y = va[feats].values, va.city.map({c: i for i, c in enumerate(cls)}).values
    res, cms, per = [], {}, {}
    for label, key in (("XGBoost", "xgb"), ("Random Forest", "rf")):
        pred = models[key].predict(X)
        p, r, f, _ = precision_recall_fscore_support(y, pred, average="macro", zero_division=0)
        res.append(dict(model=label, accuracy=round(accuracy_score(y, pred), 3), precision_macro=round(p, 3), recall_macro=round(r, 3), f1_macro=round(f, 3)))
        cms[label] = confusion_matrix(y, pred, labels=range(len(cls)))
        pc, rc, fc, sc = precision_recall_fscore_support(y, pred, labels=range(len(cls)), zero_division=0)
        per[label] = pd.DataFrame({"city": cls, "precision": pc.round(3), "recall": rc.round(3), "f1": fc.round(3), "validation routes": sc})
    return pd.DataFrame(res), cms, per


def predict_routes(rows):
    """Apply the saved preprocessor and both saved classifiers to raw route rows. Returns a DataFrame of probabilities per model and city."""
    models, cls = dl.load_models(), classes()
    d, X = inf.prepare_new(rows, models["prep"])
    out = []
    for label, key in (("XGBoost", "xgb"), ("Random Forest", "rf")):
        proba = models[key].predict_proba(X.values)
        df = pd.DataFrame(proba, columns=cls, index=rows.index)
        df.insert(0, "model", label)
        df["predicted_feed"] = np.array(cls)[proba.argmax(axis=1)]
        df["confidence"] = proba.max(axis=1).round(3)
        out.append(df)
    return pd.concat(out)
