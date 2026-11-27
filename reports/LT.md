# LT electricity report

Updated 2026-11-27 19:04 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    66.55 |       4.19 |    -31.77 |
| Naive (same hour last week) |    1344 |    86.21 |       5.39 |    -41.77 |
| TSO day-ahead forecast      |    1344 |   101.16 |       6.56 |    -82.54 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-10-02  |     168 |             57.3 |              3.8 |             -12.6 |          196.6 |           13.2 |          -192.4 |
| 2026-10-09  |     168 |             82   |              5.2 |             -79.6 |          161   |           10.6 |          -153.7 |
| 2026-10-16  |     168 |             67   |              4.2 |             -60.8 |          175.1 |           11.2 |          -157   |
| 2026-10-23  |     168 |             58.8 |              4.1 |              10.7 |          132.2 |            9   |          -122.3 |
| 2026-10-30  |     168 |             53.1 |              3.5 |             -24.5 |           30.8 |            2.1 |             5.5 |
| 2026-11-06  |     168 |            109.4 |              6.4 |            -103.4 |           52.5 |            3   |           -37.9 |
| 2026-11-13  |     168 |             64.7 |              4   |              45.9 |           28.7 |            1.7 |            22.8 |
| 2026-11-20  |     168 |             40.1 |              2.3 |             -29.9 |           32.2 |            1.8 |           -25.2 |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-20   |         40.9 |         2001.6 |               196.4 |                      0 |                     2   |
| 2026-11-21   |         38.1 |         1864   |                52.7 |                      0 |                     1.9 |
| 2026-11-22   |         37.6 |         1859.5 |               138.9 |                      0 |                     1.2 |
| 2026-11-23   |         42.8 |         2065.9 |               232.1 |                      0 |                     1.4 |
| 2026-11-24   |         43.2 |         2055.6 |               241.4 |                      0 |                     1.6 |
| 2026-11-25   |         44.1 |         2091.1 |               270.3 |                      0 |                     2.8 |
| 2026-11-26   |         44.3 |         2112.3 |               303   |                      0 |                     1.8 |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-27 19:04 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-27 18:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 719 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 747 hours outside range |
| LT | complete hours | ⚠️ warn | 2 hours built from incomplete sub-hourly data |
