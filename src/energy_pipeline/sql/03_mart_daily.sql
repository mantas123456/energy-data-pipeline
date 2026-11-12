-- Daily summary per zone, using the zone's local calendar day.
DROP TABLE IF EXISTS mart_daily;

CREATE TABLE mart_daily AS
SELECT h.zone,
       CAST(h.ts_hour AT TIME ZONE z.timezone AS date)                     AS local_date,
       count(h.load_mw)                                                    AS hours_with_load,
       sum(h.load_mw) / 1000                                               AS energy_gwh,
       max(h.load_mw)                                                      AS peak_load_mw,
       min(h.load_mw)                                                      AS min_load_mw,
       avg(h.price_eur_mwh)                                                AS avg_price_eur_mwh,
       sum(h.price_eur_mwh * h.load_mw)
         / nullif(sum(h.load_mw) FILTER (WHERE h.price_eur_mwh IS NOT NULL), 0)
                                                                           AS load_weighted_price_eur_mwh,
       count(*) FILTER (WHERE h.price_eur_mwh < 0)                         AS negative_price_hours,
       100 * avg(abs(h.tso_forecast_mw - h.load_mw) / nullif(h.load_mw, 0)) AS tso_forecast_mape_pct
FROM mart_hourly h
JOIN dim_zone z USING (zone)
GROUP BY h.zone, CAST(h.ts_hour AT TIME ZONE z.timezone AS date);

ALTER TABLE mart_daily ADD PRIMARY KEY (zone, local_date);
