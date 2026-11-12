-- One row per zone and UTC hour, with the three series side by side.
-- Sub-hourly points (15-minute prices, for example) are averaged to the hour.
SET LOCAL TIME ZONE 'UTC';

DROP TABLE IF EXISTS mart_hourly CASCADE;

CREATE TABLE mart_hourly AS
WITH hourly AS (
    SELECT zone,
           series,
           date_trunc('hour', ts_utc)              AS ts_hour,
           avg(value)                              AS value,
           count(*) * min(resolution_min) / 60.0   AS completeness
    FROM raw_observations
    GROUP BY zone, series, date_trunc('hour', ts_utc)
)
SELECT zone,
       ts_hour,
       max(value) FILTER (WHERE series = 'load_actual')         AS load_mw,
       max(value) FILTER (WHERE series = 'load_forecast_tso')   AS tso_forecast_mw,
       max(value) FILTER (WHERE series = 'price_day_ahead')     AS price_eur_mwh,
       max(completeness) FILTER (WHERE series = 'load_actual')  AS load_completeness
FROM hourly
GROUP BY zone, ts_hour;

ALTER TABLE mart_hourly ADD PRIMARY KEY (zone, ts_hour);
