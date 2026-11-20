# LT electricity report

Updated 2026-11-20 17:53 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    67.63 |       4.32 |    -27.5  |
| Naive (same hour last week) |    1344 |    82.21 |       5.27 |    -31.47 |
| TSO day-ahead forecast      |    1344 |   115.01 |       7.56 |    -96.99 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-09-25  |     168 |             48.7 |              3.4 |               4.3 |          143.1 |            9.8 |          -140.8 |
| 2026-10-02  |     168 |             57.3 |              3.8 |             -12.6 |          196.6 |           13.2 |          -192.4 |
| 2026-10-09  |     168 |             82   |              5.2 |             -79.6 |          161   |           10.6 |          -153.7 |
| 2026-10-16  |     168 |             67   |              4.2 |             -60.8 |          175.1 |           11.2 |          -157   |
| 2026-10-23  |     168 |             58.8 |              4.1 |              10.7 |          132.2 |            9   |          -122.3 |
| 2026-10-30  |     168 |             53.1 |              3.5 |             -24.5 |           30.8 |            2.1 |             5.5 |
| 2026-11-06  |     168 |            109.4 |              6.4 |            -103.4 |           52.5 |            3   |           -37.9 |
| 2026-11-13  |     168 |             64.7 |              4   |              45.9 |           28.7 |            1.7 |            22.8 |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-13   |         40.2 |         1944.3 |               139.9 |                      0 |                     1.9 |
| 2026-11-14   |         36.6 |         1783.3 |                96.7 |                      0 |                     1.9 |
| 2026-11-15   |         35.7 |         1790.7 |                49.6 |                      0 |                     1.6 |
| 2026-11-16   |         40.7 |         1988.5 |               141.8 |                      0 |                     1.5 |
| 2026-11-17   |         40.2 |         1931.3 |               223.5 |                      0 |                     2.9 |
| 2026-11-18   |         41.4 |         2000.7 |               179.8 |                      0 |                     0.9 |
| 2026-11-19   |         40.3 |         1922.1 |               229.1 |                      0 |                     1.3 |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-20 17:53 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-20 17:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 720 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 749 hours outside range |
| LT | complete hours | ⚠️ warn | 2 hours built from incomplete sub-hourly data |
