"""Smoke and behaviour tests of the dashboard (Streamlit AppTest) and of the validation helpers.

    python tests/test_dashboard.py          (or: pytest tests/test_dashboard.py)
Needs the project outputs (run_module2/4/5/6.py) to exist."""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

import pandas as pd
from streamlit.testing.v1 import AppTest

SECTIONS = ["1. Home / Project Overview", "2. Dataset Overview", "3. Exploratory Data Analysis", "4. Route Analysis", "5. Clustering Results",
            "6. Model Predictions", "7. Route Optimization", "8. Metrics Comparison", "9. About / Project Information"]


def app():
    return AppTest.from_file(os.path.join(ROOT, "app.py"), default_timeout=300)


def go(at, section):
    at.sidebar.radio[0].set_value(section).run()
    return at


def test_every_section_renders():
    at = app().run()
    assert not at.exception, [e.value for e in at.exception]
    for s in SECTIONS:
        go(at, s)
        assert not at.exception, (s, [e.value[:300] for e in at.exception])
        assert len(at.main) > 0, s


def test_home_metrics_come_from_data():
    at = go(app().run(), SECTIONS[0])
    routes = pd.read_csv("data/processed/all_cities_route_features.csv")
    shown = {m.label: m.value for m in at.metric}
    assert shown["Routes"] == f"{len(routes):,}"


def test_city_filter_changes_dataset_overview():
    at = go(app().run(), SECTIONS[1])
    full = [m.value for m in at.metric if m.label == "Records (routes)"][0]
    at.sidebar.multiselect[0].set_value(["pune"]).run()
    pune = [m.value for m in at.metric if m.label == "Records (routes)"][0]
    routes = pd.read_csv("data/processed/all_cities_route_features.csv")
    assert pune != full and pune == f"{int((routes.city == 'pune').sum()):,}", (full, pune)


def test_optimization_thresholds_change_candidates():
    at = go(app().run(), SECTIONS[6])
    base = [m.value for m in at.metric if m.label == "Merge candidates"][0]
    at.slider[0].set_value(0.95).run()                              # stricter stop-set similarity
    assert not at.exception, [e.value for e in at.exception]
    strict = [m.value for m in at.metric if m.label == "Merge candidates"][0]
    assert int(strict.replace(",", "")) <= int(base.replace(",", "")), (base, strict)


def test_default_metrics_equal_module6_outputs():
    at = go(app().run(), SECTIONS[7])
    assert not at.exception
    assert any("equal the metrics saved" in s.value for s in at.success), [s.value for s in at.success]


def test_predictions_use_saved_models():
    from modules import predictions
    res, cms, per = predictions.validation_evaluation()
    assert set(res.model) == {"XGBoost", "Random Forest"} and (res.accuracy > 0.8).all()
    rows = pd.read_csv("data/processed/all_cities_route_features.csv", dtype={"route_id": str, "route_name": str}).head(3)
    out = predictions.predict_routes(rows)
    assert len(out) == 6 and out.confidence.between(0, 1).all()


def test_validation_helpers():
    from modules import data_validation as dv
    good = pd.read_csv("data/processed/all_cities_route_features.csv", dtype={"route_id": str, "route_name": str}).head(30)
    assert dv.validate_for_inference(good)[0]
    assert not dv.validate_for_inference(good.drop(columns=["n_trips"]))[0]
    bad = good.copy(); bad["length_km"] = "abc"
    assert not dv.validate_for_inference(bad)[0]
    dup = pd.concat([good, good.head(1)])
    assert not dv.validate_for_inference(dup)[0]
    assert (dv.quality_report(good)["routes"] >= 0).all()


def test_all_cities_including_hyderabad():
    at = app().run()
    at.sidebar.multiselect[0].set_value(["ahmedabad", "bengaluru", "chennai", "delhi", "hyderabad", "kochi", "pune"]).run()
    for s in SECTIONS:
        go(at, s)
        assert not at.exception, (s, [e.value[:300] for e in at.exception])


def test_single_city_without_merge_candidates():
    at = app().run()
    at.sidebar.multiselect[0].set_value(["kochi"]).run()
    for s in (SECTIONS[1], SECTIONS[4], SECTIONS[6], SECTIONS[7]):
        go(at, s)
        assert not at.exception, (s, [e.value[:300] for e in at.exception])


def test_upload_reading():
    import io
    from modules import data_validation as dv
    f = io.BytesIO(pd.read_csv("data/processed/all_cities_route_features.csv").head(5).to_csv(index=False).encode()); f.name = "r.csv"
    df, err = dv.read_upload(f); assert err is None and len(df) == 5
    g = io.BytesIO(b""); g.name = "empty.csv"
    assert dv.read_upload(g)[1] is not None
    h = io.BytesIO(b"x"); h.name = "r.txt"
    assert "Unsupported" in dv.read_upload(h)[1]
    x = io.BytesIO(); pd.DataFrame({"a": [1]}).to_excel(x, index=False); x.seek(0); x.name = "r.xlsx"
    assert dv.read_upload(x)[1] is None


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"{len(tests)} tests passed")
