# LT electricity report

Updated 2026-11-23 21:31 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    69.04 |       4.39 |    -34.95 |
| Naive (same hour last week) |    1344 |    82.39 |       5.25 |    -32.78 |
| TSO day-ahead forecast      |    1344 |   108.03 |       7.05 |    -89.23 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-09-28  |     168 |             53.3 |              3.8 |              23.7 |          146.5 |           10.2 |          -143.8 |
| 2026-10-05  |     168 |             64.2 |              4.1 |             -53.9 |          212.7 |           14   |          -209.6 |
| 2026-10-12  |     168 |             75.1 |              4.8 |             -73.3 |          132.8 |            8.6 |          -111   |
| 2026-10-19  |     168 |             62.6 |              4.1 |             -13.6 |          186.8 |           12.2 |          -183.3 |
| 2026-10-26  |     168 |             48.1 |              3.2 |             -19.7 |           74.5 |            4.8 |           -44.1 |
| 2026-11-02  |     168 |             71.9 |              4.6 |             -59.6 |           29.7 |            1.9 |            -0.6 |
| 2026-11-09  |     168 |            132.4 |              7.8 |             -60.7 |           52.8 |            3   |           -28.5 |
| 2026-11-16  |     168 |             44.7 |              2.7 |             -22.6 |           28.4 |            1.7 |             7   |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-17   |         40.2 |         1931.3 |               223.5 |                      0 |                     2.9 |
| 2026-11-18   |         41.4 |         2000.7 |               179.8 |                      0 |                     0.9 |
| 2026-11-19   |         40.3 |         1922.1 |               229.1 |                      0 |                     1.3 |
| 2026-11-20   |         40.9 |         2001.6 |               196.4 |                      0 |                     2   |
| 2026-11-21   |         38.1 |         1864   |                52.7 |                      0 |                     1.9 |
| 2026-11-22   |         37.6 |         1859.5 |               138.9 |                      0 |                     1.2 |
| 2026-11-23   |         42.8 |         2065.9 |               232.1 |                      0 |                     1.5 |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-23 21:31 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-23 21:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 720 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 745 hours outside range |
| LT | complete hours | ⚠️ warn | 2 hours built from incomplete sub-hourly data |
