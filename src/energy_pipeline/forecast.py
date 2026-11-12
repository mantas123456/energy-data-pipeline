"""Day-ahead load forecast, benchmarked against the TSO's own forecast.

The model only uses load values at least 48 hours old. A forecast for any hour
of tomorrow is made by late morning today, when the most recent complete
actuals are roughly 24-48 hours behind, so 48 hours is a safe minimum lag.
Weather is not used, which is the main reason the TSO forecast should be
hard to beat.
"""

from __future__ import annotations

import holidays
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

MIN_LAG_H = 48


def calendar(index: pd.DatetimeIndex, tz: str, country: str) -> pd.DataFrame:
    local = index.tz_convert(tz)
    hol = holidays.country_holidays(country, years=range(local.year.min(), local.year.max() + 1))
    return pd.DataFrame(
        {
            "hour": local.hour,
            "dow": local.dayofweek,
            "doy_sin": np.sin(2 * np.pi * local.dayofyear / 365.25),
            "doy_cos": np.cos(2 * np.pi * local.dayofyear / 365.25),
            "holiday": [int(d in hol) for d in local.date],
        },
        index=index,
    )


def lag_features(y: pd.Series) -> pd.DataFrame:
    """Lags of the load series, none newer than MIN_LAG_H hours."""
    past = y.shift(MIN_LAG_H)
    return pd.DataFrame(
        {
            "lag_48h": past,
            "lag_168h": y.shift(168),
            "lag_336h": y.shift(336),
            "mean_24h": past.rolling(24, min_periods=20).mean(),
            "mean_168h": past.rolling(168, min_periods=150).mean(),
        },
        index=y.index,
    )


def features(h: pd.DataFrame, tz: str, country: str, extra_hours: int = 0) -> pd.DataFrame:
    """Feature table on a complete hourly index.

    h: hourly rows for one zone with ts_hour (UTC), load_mw and tso_forecast_mw.
    extra_hours: extend the index past the last row, for forecasting ahead.
    """
    df = h.set_index("ts_hour").sort_index()
    end = df.index.max() + pd.Timedelta(hours=extra_hours)
    df = df.reindex(pd.date_range(df.index.min(), end, freq="h"))
    out = pd.concat([calendar(df.index, tz, country), lag_features(df["load_mw"])], axis=1)
    out["load_mw"] = df["load_mw"]
    out["tso_forecast_mw"] = df.get("tso_forecast_mw")
    return out


FEATURES = [
    "hour",
    "dow",
    "doy_sin",
    "doy_cos",
    "holiday",
    "lag_48h",
    "lag_168h",
    "lag_336h",
    "mean_24h",
    "mean_168h",
]


def model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_iter=400, learning_rate=0.05, categorical_features=[0, 1], random_state=42
    )


def evaluate(feat: pd.DataFrame, weeks: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Weekly rolling-origin backtest over the last `weeks` complete weeks.

    Returns (metrics per method, hourly predictions).
    """
    data = feat.dropna(subset=["load_mw"])
    end = data.index.max().floor("D")
    preds = []
    for k in range(weeks, 0, -1):
        start = end - pd.Timedelta(weeks=k)
        stop = start + pd.Timedelta(weeks=1)
        train = data[data.index < start].dropna(subset=FEATURES)
        test = data[(data.index >= start) & (data.index < stop)].dropna(subset=FEATURES)
        if len(train) < 24 * 60 or test.empty:
            continue
        m = model().fit(train[FEATURES], train["load_mw"])
        preds.append(
            pd.DataFrame(
                {
                    "actual": test["load_mw"],
                    "Model (no weather)": m.predict(test[FEATURES]),
                    "Naive (same hour last week)": test["lag_168h"],
                    "TSO day-ahead forecast": test["tso_forecast_mw"],
                },
                index=test.index,
            )
        )
    if not preds:
        raise ValueError("not enough history for the backtest (need about 10 weeks)")
    p = pd.concat(preds)
    rows = []
    for method in p.columns.drop("actual"):
        both = p[["actual", method]].dropna()
        err = both[method] - both["actual"]
        rows.append(
            {
                "method": method,
                "hours": len(both),
                "mae_mw": err.abs().mean(),
                "mape_pct": 100 * (err.abs() / both["actual"]).mean(),
                "bias_mw": err.mean(),
            }
        )
    return pd.DataFrame(rows).sort_values("mae_mw").round(2), p


def forecast_ahead(feat: pd.DataFrame) -> pd.DataFrame:
    """Train on all history and predict the hours after the latest actual value.

    `feat` must extend at least MIN_LAG_H hours past the last actual
    (see `features(..., extra_hours=...)`).
    """
    known = feat.dropna(subset=["load_mw"])
    last = known.index.max()
    train = known.dropna(subset=FEATURES)
    future = feat[(feat.index > last) & (feat.index <= last + pd.Timedelta(hours=MIN_LAG_H))]
    future = future.dropna(subset=FEATURES)
    m = model().fit(train[FEATURES], train["load_mw"])
    return pd.DataFrame(
        {"forecast_mw": m.predict(future[FEATURES]), "tso_forecast_mw": future["tso_forecast_mw"]},
        index=future.index,
    )
