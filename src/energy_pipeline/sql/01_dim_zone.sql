-- Zones and their local time zones. Rows are written by the pipeline from config.yaml.
CREATE TABLE IF NOT EXISTS dim_zone (
    zone      varchar(8) PRIMARY KEY,
    eic       varchar(32) NOT NULL,
    timezone  text NOT NULL
);
