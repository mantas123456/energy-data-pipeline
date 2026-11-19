# LT electricity report

Updated 2026-11-19 11:25 UTC by the scheduled pipeline. Data: ENTSO-E Transparency Platform.

## Day-ahead load forecast, last 8 weeks

| method                      |   hours |   mae_mw |   mape_pct |   bias_mw |
|:----------------------------|--------:|---------:|-----------:|----------:|
| Model (no weather)          |    1344 |    64.57 |       4.14 |    -27.72 |
| Naive (same hour last week) |    1344 |    80.69 |       5.19 |    -34.15 |
| TSO day-ahead forecast      |    1344 |   117.11 |       7.7  |    -99.78 |

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

Generated 2026-11-19 11:25 UTC

| Zone | Check | Result | Detail |
|---|---|---|---|
| LT | load is fresh | ✅ pass | latest actual load 2026-11-19 10:00 UTC (1 h old) |
| LT | no gaps in actual load | ✅ pass | 0 missing hours, longest gap 0 h (last 30 days) |
| LT | load within 100..5000 | ✅ pass | 0 of 719 hours outside range |
| LT | price within -500..4000 | ✅ pass | 0 of 731 hours outside range |
| LT | complete hours | ⚠️ warn | 1 hours built from incomplete sub-hourly data |
