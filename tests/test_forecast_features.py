import numpy as np
import pandas as pd

from energy_pipeline.forecast import FEATURES, MIN_LAG_H, features


def test_lags_never_newer_than_min_lag():
    ts = pd.date_range("2026-01-01", periods=24 * 30, freq="h", tz="UTC")
    h = pd.DataFrame(
        {"ts_hour": ts, "load_mw": np.arange(len(ts), dtype=float), "tso_forecast_mw": np.nan}
    )
    f = features(h, "Europe/Vilnius", "LT").dropna(subset=FEATURES)
    for col in ["lag_48h", "lag_168h", "lag_336h", "mean_24h", "mean_168h"]:
        assert (f[col] <= f["load_mw"] - MIN_LAG_H).all(), col


def test_holiday_flag_uses_local_date():
    ts = pd.date_range("2026-02-15T20:00Z", periods=8, freq="h", tz="UTC")
    h = pd.DataFrame({"ts_hour": ts, "load_mw": 1.0, "tso_forecast_mw": np.nan})
    f = features(h, "Europe/Vilnius", "LT")
    # 16 February is a Lithuanian public holiday; it starts at 22:00 UTC on the 15th
    assert f.loc["2026-02-15T21:00Z", "holiday"] == 0
    assert f.loc["2026-02-15T22:00Z", "holiday"] == 1


def test_weekly_metrics_per_backtest_week():
    from energy_pipeline.forecast import weekly_metrics

    idx = pd.date_range("2026-10-01", periods=14 * 24, freq="h", tz="UTC")
    week = np.where(idx < idx[0] + pd.Timedelta(weeks=1), idx[0], idx[0] + pd.Timedelta(weeks=1))
    first = idx < idx[0] + pd.Timedelta(weeks=1)
    preds = pd.DataFrame(
        {
            "actual": 1000.0,
            # Week 1: TSO 10 % low, model 2 % high. Week 2: TSO exact, model 5 % low.
            "TSO day-ahead forecast": np.where(first, 900.0, 1000.0),
            "Model (no weather)": np.where(first, 1020.0, 950.0),
            "Naive (same hour last week)": 1000.0,
            "week_start": pd.DatetimeIndex(week),
        },
        index=idx,
    )
    preds.iloc[5, preds.columns.get_loc("TSO day-ahead forecast")] = np.nan  # left out
    w = weekly_metrics(preds, "Europe/Vilnius")
    assert w["week_from"].tolist() == ["2026-10-01", "2026-10-08"]
    assert w["hours"].tolist() == [168, 168]
    np.testing.assert_allclose(w["TSO MAPE (%)"], [10, 0])
    np.testing.assert_allclose(w["TSO bias (MW)"], [-100, 0])
    np.testing.assert_allclose(w["TSO MAE (MW)"], [100, 0])
    np.testing.assert_allclose(w["Model MAPE (%)"], [2, 5])
    np.testing.assert_allclose(w["Model bias (MW)"], [20, -50])
