# LT electricity report

Updated 2026-11-22 17:14 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    67.62 |       4.33 |    -28.88 |
| Naive (same hour last week) |    1344 |    81.95 |       5.24 |    -31.78 |
| TSO day-ahead forecast      |    1344 |   110.8  |       7.26 |    -92.25 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-09-27  |     168 |             62.6 |              4.5 |              31.8 |          151.5 |           10.5 |          -149.7 |
| 2026-10-04  |     168 |             61.5 |              4   |             -35.1 |          214.4 |           14.2 |          -210.4 |
| 2026-10-11  |     168 |             70.9 |              4.5 |             -63.3 |          127.2 |            8.3 |          -105.8 |
| 2026-10-18  |     168 |             61.6 |              4   |             -25.1 |          179.5 |           11.6 |          -175.5 |
| 2026-10-25  |     168 |             47.9 |              3.2 |             -10.6 |          102.2 |            6.8 |           -77.4 |
| 2026-11-01  |     168 |             73.8 |              4.8 |             -61.9 |           29.2 |            1.9 |            -2.6 |
| 2026-11-08  |     168 |            116.5 |              6.8 |             -46.9 |           53.4 |            3   |           -27.3 |
| 2026-11-15  |     168 |             46.2 |              2.8 |             -19.9 |           29.2 |            1.7 |            10.5 |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-15   |         35.7 |         1790.7 |                49.6 |                      0 |                     1.6 |
| 2026-11-16   |         40.7 |         1988.5 |               141.8 |                      0 |                     1.5 |
| 2026-11-17   |         40.2 |         1931.3 |               223.5 |                      0 |                     2.9 |
| 2026-11-18   |         41.4 |         2000.7 |               179.8 |                      0 |                     0.9 |
| 2026-11-19   |         40.3 |         1922.1 |               229.1 |                      0 |                     1.3 |
| 2026-11-20   |         40.9 |         2001.6 |               196.4 |                      0 |                     2   |
| 2026-11-21   |         38.1 |         1864   |                52.7 |                      0 |                     1.9 |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-22 17:14 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-22 16:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 719 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 749 hours outside range |
| LT | complete hours | ⚠️ warn | 2 hours built from incomplete sub-hourly data |
