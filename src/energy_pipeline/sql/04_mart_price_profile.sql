-- Average day-ahead price by local hour of day and calendar month: the daily price shape.
DROP TABLE IF EXISTS mart_price_profile;

CREATE TABLE mart_price_profile AS
SELECT h.zone,
       CAST(extract(month FROM h.ts_hour AT TIME ZONE z.timezone) AS int)  AS month,
       CAST(extract(hour  FROM h.ts_hour AT TIME ZONE z.timezone) AS int)  AS local_hour,
       avg(h.price_eur_mwh)                                                AS avg_price_eur_mwh,
       count(h.price_eur_mwh)                                              AS n_hours
FROM mart_hourly h
JOIN dim_zone z USING (zone)
WHERE h.price_eur_mwh IS NOT NULL
GROUP BY 1, 2, 3;
