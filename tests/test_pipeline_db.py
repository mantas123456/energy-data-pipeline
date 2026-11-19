import numpy as np
import pandas as pd
import pytest

from energy_pipeline import db, forecast, pipeline, quality

CFG = {
    "zones": {"LT": {"eic": "10YLT-1001A0008Q", "timezone": "Europe/Vilnius"}},
    "series": ["load_actual", "load_forecast_tso", "price_day_ahead"],
    "checks": {
        "max_gap_hours": 3,
        "stale_after_hours": 48,
        "load_mw": [100, 5000],
        "price_eur_mwh": [-500, 4000],
    },
    "forecast": {"holdout_weeks": 2},
}


def synthetic(days=112, seed=0):
    """Hourly load with daily and weekly shape, a TSO forecast and 15-minute prices."""
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2026-01-01", periods=days * 24, freq="h", tz="UTC")
    local = ts.tz_convert("Europe/Vilnius")
    load = (
        1300
        + 300 * np.sin((local.hour - 6) / 24 * 2 * np.pi)
        - 150 * (local.dayofweek >= 5)
        + rng.normal(0, 25, len(ts))
    )
    tso = load + rng.normal(0, 30, len(ts))
    q = pd.date_range(ts[0], periods=len(ts) * 4, freq="15min", tz="UTC")
    price = 90 + 40 * np.sin((q.hour - 4) / 24 * 2 * np.pi) + rng.normal(0, 5, len(q))

    def frame(t, v, res):
        return pd.DataFrame({"ts_utc": t, "resolution_min": res, "value": v})

    return frame(ts, load, 60), frame(ts, tso, 60), frame(q, price, 15)


def load_all(eng):
    pipeline.sync_zones(eng, CFG)
    load, tso, price = synthetic()
    db.upsert_observations(eng, "LT", "load_actual", load)
    db.upsert_observations(eng, "LT", "load_forecast_tso", tso)
    db.upsert_observations(eng, "LT", "price_day_ahead", price)
    db.transform(eng)
    return load, price


def test_upsert_is_idempotent_and_keeps_finer_resolution(eng):
    pipeline.sync_zones(eng, CFG)
    q = pd.DataFrame(
        {
            "ts_utc": pd.date_range("2026-01-01", periods=4, freq="15min", tz="UTC"),
            "resolution_min": 15,
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )
    db.upsert_observations(eng, "LT", "price_day_ahead", q)
    db.upsert_observations(eng, "LT", "price_day_ahead", q)
    hourly = pd.DataFrame(
        {"ts_utc": [pd.Timestamp("2026-01-01", tz="UTC")], "resolution_min": [60], "value": [99.0]}
    )
    db.upsert_observations(eng, "LT", "price_day_ahead", hourly)
    rows = db.read_sql(eng, "SELECT value, resolution_min FROM raw_observations ORDER BY ts_utc")
    assert len(rows) == 4
    assert rows["value"].iloc[0] == 1.0  # hourly value did not overwrite 15-minute data


def test_marts(eng):
    load, price = load_all(eng)
    h = db.read_sql(eng, "SELECT * FROM mart_hourly ORDER BY ts_hour")
    assert len(h) == len(load)
    # 15-minute prices are averaged to the hour
    first_hour = price["value"].iloc[:4].mean()
    assert abs(h["price_eur_mwh"].iloc[0] - first_hour) < 1e-9
    d = db.read_sql(eng, "SELECT * FROM mart_daily ORDER BY local_date")
    full = d[d["hours_with_load"] == 24]
    assert abs(full["energy_gwh"].iloc[0] * 1000 / 24 - full["peak_load_mw"].iloc[0]) < 1000
    p = db.read_sql(eng, "SELECT * FROM mart_price_profile")
    assert set(p["local_hour"]) == set(range(24))


def test_quality_checks_find_gaps_and_staleness(eng):
    load_all(eng)
    with eng.begin() as conn:
        conn.exec_driver_sql(
            "DELETE FROM mart_hourly WHERE ts_hour BETWEEN '2026-04-10 00:00+00' "
            "AND '2026-04-10 05:00+00'"
        )
    now = pd.Timestamp("2026-04-23T12:00Z")
    res = {c.name: c for c in quality.run_checks(eng, CFG, now=now)}
    assert res["no gaps in actual load"].status == "fail"
    assert "longest gap 6 h" in res["no gaps in actual load"].detail
    assert res["load is fresh"].status == "pass"
    later = {c.name: c for c in quality.run_checks(eng, CFG, now=now + pd.Timedelta(days=5))}
    assert later["load is fresh"].status == "fail"


def test_forecast_and_report(eng, tmp_path):
    load_all(eng)
    metrics, preds, ahead = pipeline.run_forecast(eng, CFG, "LT")
    assert set(metrics["method"]) == {
        "Model (no weather)",
        "Naive (same hour last week)",
        "TSO day-ahead forecast",
    }
    assert len(ahead) == forecast.MIN_LAG_H
    assert ahead.index.min() > preds.index.max()
    checks = quality.run_checks(eng, CFG, now=pd.Timestamp("2026-04-23T12:00Z"))
    path = pipeline.write_report(eng, CFG, "LT", metrics, preds, checks, out=tmp_path)
    report = path.read_text()
    assert "Day-ahead load forecast" in report
    # One row per backtest week (holdout_weeks = 2), with the same week boundaries.
    assert "### Week by week" in report
    weekly = forecast.weekly_metrics(preds, "Europe/Vilnius")
    assert len(weekly) == CFG["forecast"]["holdout_weeks"]
    assert weekly["hours"].sum() == len(preds)
    assert (tmp_path / "LT_forecast.png").exists()


def test_export_restore_round_trip(eng, tmp_path):
    load_all(eng)
    files = pipeline.export_raw(eng, tmp_path)
    assert len(files) == 3
    assert pipeline.export_raw(eng, tmp_path) == []  # unchanged data rewrites nothing
    with eng.begin() as conn:
        conn.exec_driver_sql("TRUNCATE raw_observations")
    n = pipeline.restore_raw(eng, CFG, tmp_path)
    total = db.read_sql(eng, "SELECT count(*) AS n FROM raw_observations")["n"].iloc[0]
    assert n == total == 112 * 24 * 2 + 112 * 96


class FlakyClient:
    """Returns data for load but fails for prices."""

    def fetch(self, series, eic, start, end):
        if series == "price_day_ahead":
            raise RuntimeError("HTTP 503")
        load, _, _ = synthetic(days=2)
        return load


def test_ingest_loads_other_series_when_one_fails(eng):
    import pytest

    start, end = pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-01-03", tz="UTC")
    with pytest.raises(RuntimeError, match="price_day_ahead"):
        pipeline.ingest(eng, CFG, FlakyClient(), start, end)
    runs = db.read_sql(eng, "SELECT series, status FROM ingest_runs ORDER BY id")
    assert runs["status"].tolist() == ["ok", "ok", "error"]
    n = db.read_sql(eng, "SELECT count(*) AS n FROM raw_observations")["n"].iloc[0]
    assert n == 2 * 48


def test_forecast_without_data_raises_clear_error(eng):
    pipeline.sync_zones(eng, CFG)
    db.transform(eng)
    with pytest.raises(pipeline.NoDataError, match="No load data for zone LT"):
        pipeline.run_forecast(eng, CFG, "LT")
