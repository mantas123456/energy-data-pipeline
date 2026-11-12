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
