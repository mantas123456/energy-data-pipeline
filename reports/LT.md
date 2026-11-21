# LT electricity report

Updated 2026-11-21 16:51 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    63.97 |       4.07 |    -27.53 |
| Naive (same hour last week) |    1344 |    81.95 |       5.25 |    -31.36 |
| TSO day-ahead forecast      |    1344 |   112.68 |       7.4  |    -94.31 |

### Week by week

The table above averages over all backtest weeks. A forecast can come out ahead overall because of a few weeks where the other did badly, so check here whether the ranking holds week by week. Bias is forecast minus actual: negative means the forecast was too low.

| week_from   |   hours |   Model MAE (MW) |   Model MAPE (%) |   Model bias (MW) |   TSO MAE (MW) |   TSO MAPE (%) |   TSO bias (MW) |
|:------------|--------:|-----------------:|-----------------:|------------------:|---------------:|---------------:|----------------:|
| 2026-09-26  |     168 |             52.8 |              3.8 |              16.9 |          142.1 |            9.9 |          -139.8 |
| 2026-10-03  |     168 |             58.9 |              3.8 |             -31.9 |          210.8 |           13.9 |          -206.6 |
| 2026-10-10  |     168 |             73.7 |              4.6 |             -68.6 |          143.8 |            9.5 |          -123   |
| 2026-10-17  |     168 |             47.7 |              2.9 |             -30.7 |          175.5 |           11.2 |          -170.9 |
| 2026-10-24  |     168 |             57.7 |              4   |               8   |          114.6 |            7.8 |          -103.6 |
| 2026-10-31  |     168 |             62.5 |              4.1 |             -42.4 |           33.3 |            2.2 |             2.9 |
| 2026-11-07  |     168 |            109.9 |              6.3 |             -90.6 |           51.7 |            2.9 |           -29.7 |
| 2026-11-14  |     168 |             48.6 |              3   |              19.1 |           29.6 |            1.8 |            16.3 |

![Forecasts](LT_forecast.png)

## Last 7 days

| local_date   |   energy_gwh |   peak_load_mw |   avg_price_eur_mwh |   negative_price_hours |   tso_forecast_mape_pct |
|:-------------|-------------:|---------------:|--------------------:|-----------------------:|------------------------:|
| 2026-11-14   |         36.6 |         1783.3 |                96.7 |                      0 |                     1.9 |
| 2026-11-15   |         35.7 |         1790.7 |                49.6 |                      0 |                     1.6 |
| 2026-11-16   |         40.7 |         1988.5 |               141.8 |                      0 |                     1.5 |
| 2026-11-17   |         40.2 |         1931.3 |               223.5 |                      0 |                     2.9 |
| 2026-11-18   |         41.4 |         2000.7 |               179.8 |                      0 |                     0.9 |
| 2026-11-19   |         40.3 |         1922.1 |               229.1 |                      0 |                     1.3 |
| 2026-11-20   |         40.9 |         2001.6 |               196.4 |                      0 |                     2   |

![Daily](LT_daily.png)

## Data quality

Generated 2026-11-21 16:51 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-21 16:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 720 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 750 hours outside range |
| LT | complete hours | ⚠️ warn | 2 hours built from incomplete sub-hourly data |
