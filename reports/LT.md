# LT electricity report

Updated 2026-11-25 19:24 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    64.69 |       4.1  |    -27.9  |
| Naive (same hour last week) |    1344 |    83.56 |       5.28 |    -35.04 |
| TSO day-ahead forecast      |    1344 |   102.72 |       6.69 |    -84.01 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-09-30  |     168 |             53.5 |              3.6 |               5.6 |          160   |           11   |          -155.8 |
| 2026-10-07  |     168 |             66.2 |              4.3 |             -57.9 |          183.5 |           12.1 |          -180.6 |
| 2026-10-14  |     168 |             57.1 |              3.5 |             -50.2 |          150.5 |            9.6 |          -127.6 |
| 2026-10-21  |     168 |             61.6 |              4.3 |              21.2 |          169.5 |           11.3 |          -164.8 |
| 2026-10-28  |     168 |             49.1 |              3.3 |             -18.9 |           48.9 |            3.2 |           -11.8 |
| 2026-11-04  |     168 |             84.3 |              5.2 |             -80.4 |           33.9 |            2   |           -14.5 |
| 2026-11-11  |     168 |             98.4 |              5.8 |             -20.9 |           49.8 |            2.8 |            -8   |
| 2026-11-18  |     168 |             47.3 |              2.8 |             -21.7 |           25.7 |            1.5 |            -8.9 |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-18   |         41.4 |         2000.7 |               179.8 |                      0 |                     0.9 |
| 2026-11-19   |         40.3 |         1922.1 |               229.1 |                      0 |                     1.3 |
| 2026-11-20   |         40.9 |         2001.6 |               196.4 |                      0 |                     2   |
| 2026-11-21   |         38.1 |         1864   |                52.7 |                      0 |                     1.9 |
| 2026-11-22   |         37.6 |         1859.5 |               138.9 |                      0 |                     1.2 |
| 2026-11-23   |         42.8 |         2065.9 |               232.1 |                      0 |                     1.4 |
| 2026-11-24   |         43.2 |         2055.6 |               241.4 |                      0 |                     1.6 |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-25 19:24 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-25 18:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 719 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 747 hours outside range |
| LT | complete hours | ⚠️ warn | 1 hours built from incomplete sub-hourly data |
