# LT electricity report

Updated 2026-11-19 12:06 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    64.57 |       4.14 |    -27.72 |
| Naive (same hour last week) |    1344 |    80.69 |       5.19 |    -34.15 |
| TSO day-ahead forecast      |    1344 |   117.11 |       7.7  |    -99.78 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-09-24  |     168 |             52.7 |              3.6 |             -13.2 |          145.1 |            9.9 |          -142.6 |
| 2026-10-01  |     168 |             53.3 |              3.6 |              -7.1 |          180.6 |           12.2 |          -177.1 |
| 2026-10-08  |     168 |             75.6 |              4.8 |             -68.3 |          180.6 |           11.8 |          -177.1 |
| 2026-10-15  |     168 |             58.4 |              3.6 |             -47.7 |          161   |           10.3 |          -138.7 |
| 2026-10-22  |     168 |             55.9 |              4   |              26.3 |          150.4 |           10.1 |          -144.2 |
| 2026-10-29  |     168 |             50.4 |              3.3 |             -25.5 |           37.6 |            2.5 |            -0.3 |
| 2026-11-05  |     168 |             95.3 |              5.7 |             -90.2 |           44.8 |            2.6 |           -27.3 |
| 2026-11-12  |     168 |             75   |              4.5 |               3.9 |           36.7 |            2.1 |             9   |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-12   |         43.3 |         2093.4 |               208.5 |                      0 |                     4.4 |
| 2026-11-13   |         40.2 |         1944.3 |               139.9 |                      0 |                     1.9 |
| 2026-11-14   |         36.6 |         1783.3 |                96.7 |                      0 |                     1.9 |
| 2026-11-15   |         35.7 |         1790.7 |                49.6 |                      0 |                     1.6 |
| 2026-11-16   |         40.7 |         1988.5 |               141.8 |                      0 |                     1.5 |
| 2026-11-17   |         40.2 |         1931.3 |               223.5 |                      0 |                     2.9 |
| 2026-11-18   |         41.4 |         2000.7 |               179.8 |                      0 |                     0.9 |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-19 12:06 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-19 11:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 719 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 730 hours outside range |
| LT | complete hours | ⚠️ warn | 2 hours built from incomplete sub-hourly data |
