"""Pipeline steps: ingest, restore, transform, check, forecast, export, report."""

from __future__ import annotations

import gzip
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

from . import db, forecast, quality  # noqa: E402
from .entsoe import EntsoeClient  # noqa: E402

log = logging.getLogger(__name__)
ROOT = Path.cwd()


class NoDataError(RuntimeError):
    """A zone has no hourly data to forecast or report on."""


def load_config(path: str | Path = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def sync_zones(eng: Engine, cfg: dict) -> None:
    db.init(eng)
    with eng.begin() as conn:
        conn.exec_driver_sql(db.sql_files()[0][1])  # 01_dim_zone.sql
        for zone, z in cfg["zones"].items():
            conn.execute(
                text(
                    "INSERT INTO dim_zone (zone, eic, timezone) VALUES (:zone, :eic, :tz) "
                    "ON CONFLICT (zone) DO UPDATE "
                    "SET eic = EXCLUDED.eic, timezone = EXCLUDED.timezone"
                ),
                {"zone": zone, "eic": z["eic"], "tz": z["timezone"]},
            )


# ---------------------------------------------------------------- ingest


def ingest(eng: Engine, cfg: dict, client: EntsoeClient, start: datetime, end: datetime) -> int:
    """Fetch every configured series for every zone and upsert it.

    A failing series is logged and skipped so the others still load; the
    function raises at the end if anything failed.
    """
    sync_zones(eng, cfg)
    total, errors = 0, []
    for zone, z in cfg["zones"].items():
        for series in cfg["series"]:
            try:
                df = client.fetch(series, z["eic"], start, end)
                n = db.upsert_observations(eng, zone, series, df)
                db.log_run(
                    eng,
                    zone=zone,
                    series=series,
                    period_start=start,
                    period_end=end,
                    rows=n,
                    status="ok",
                )
                total += n
            except Exception as exc:
                log.error("%s %s failed: %s", zone, series, exc)
                db.log_run(
                    eng,
                    zone=zone,
                    series=series,
                    period_start=start,
                    period_end=end,
                    rows=0,
                    status="error",
                    message=str(exc)[:1000],
                )
                errors.append(f"{zone} {series}: {exc}")
    if errors:
        raise RuntimeError("ingest failed for: " + "; ".join(errors))
    return total


def window(days_back: int, now: datetime | None = None) -> tuple[datetime, datetime]:
    """From `days_back` days ago to the end of tomorrow (UTC), on day boundaries."""
    now = now or datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return today - timedelta(days=days_back), today + timedelta(days=2)


# ----------------------------------------------------- export / restore


def export_raw(eng: Engine, out: Path = ROOT / "data" / "observations") -> list[Path]:
    """Write raw observations as one gzipped CSV per zone, series and year.

    These files are committed by the scheduled job, so the database can be
    rebuilt from the repository at any time (`pipeline restore`).
    """
    df = db.read_sql(
        eng,
        "SELECT zone, series, ts_utc, resolution_min, value "
        "FROM raw_observations ORDER BY zone, series, ts_utc",
    )
    written = []
    if df.empty:
        return written
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    for (zone, series, year), g in df.groupby(["zone", "series", df["ts_utc"].dt.year]):
        path = out / zone / series / f"{year}.csv.gz"
        path.parent.mkdir(parents=True, exist_ok=True)
        csv = g[["ts_utc", "resolution_min", "value"]].to_csv(
            index=False, date_format="%Y-%m-%dT%H:%MZ"
        )
        new = csv.encode()
        if path.exists() and gzip.decompress(path.read_bytes()) == new:
            continue  # unchanged: keep the file byte-identical so git sees no diff
        path.write_bytes(gzip.compress(new, mtime=0))
        written.append(path)
    return written


def restore_raw(eng: Engine, cfg: dict, src: Path = ROOT / "data" / "observations") -> int:
    sync_zones(eng, cfg)
    total = 0
    for path in sorted(src.glob("*/*/*.csv.gz")):
        zone, series = path.parts[-3], path.parts[-2]
        df = pd.read_csv(path, parse_dates=["ts_utc"])
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
        total += db.upsert_observations(eng, zone, series, df)
    return total


# ------------------------------------------------- forecast and report


def run_forecast(eng: Engine, cfg: dict, zone: str, country: str | None = None):
    tz = cfg["zones"][zone]["timezone"]
    h = db.read_sql(
        eng,
        "SELECT ts_hour, load_mw, tso_forecast_mw FROM mart_hourly "
        "WHERE zone = :zone ORDER BY ts_hour",
        zone=zone,
    )
    if h["load_mw"].isna().all():
        raise NoDataError(
            f"No load data for zone {zone} in mart_hourly. ENTSO-E returned no points: "
            f"check the zone's EIC code in config.yaml and the ingest log above."
        )
    h["ts_hour"] = pd.to_datetime(h["ts_hour"], utc=True)
    feat = forecast.features(h, tz, country or zone, extra_hours=forecast.MIN_LAG_H)
    metrics, preds = forecast.evaluate(feat, cfg["forecast"]["holdout_weeks"])
    ahead = forecast.forecast_ahead(feat)
    with eng.begin() as conn:
        metrics.assign(zone=zone, evaluated_at=pd.Timestamp.now(tz="UTC")).to_sql(
            "mart_forecast_metrics", conn, if_exists="replace", index=False
        )
        ahead.rename_axis("ts_hour").reset_index().assign(zone=zone).to_sql(
            "mart_forecast_ahead", conn, if_exists="replace", index=False
        )
    return metrics, preds, ahead


def write_report(
    eng: Engine,
    cfg: dict,
    zone: str,
    metrics: pd.DataFrame,
    preds: pd.DataFrame,
    checks: list[quality.Check],
    out: Path = ROOT / "reports",
) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    tz = cfg["zones"][zone]["timezone"]
    daily = db.read_sql(
        eng, "SELECT * FROM mart_daily WHERE zone = :zone ORDER BY local_date", zone=zone
    )
    daily["local_date"] = pd.to_datetime(daily["local_date"])

    # Chart 1: last two weeks of the backtest.
    last = preds[preds.index >= preds.index.max() - pd.Timedelta(days=14)].tz_convert(tz)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(last.index, last["actual"], color="black", linewidth=1.4, label="Actual")
    for col, style in [("TSO day-ahead forecast", "--"), ("Model (no weather)", "-")]:
        ax.plot(last.index, last[col], style, linewidth=1.1, label=col)
    ax.set_ylabel("Load (MW)")
    ax.set_title(
        f"{zone}: actual load and day-ahead forecasts, last 14 days of backtest",
        loc="left",
        fontsize=10,
    )
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower right", bbox_to_anchor=(1, 1.0))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out / f"{zone}_forecast.png", dpi=130)
    plt.close(fig)

    # Chart 2: daily average price and energy.
    d = daily[daily["local_date"] >= daily["local_date"].max() - pd.Timedelta(days=365)]
    fig, ax1 = plt.subplots(figsize=(9, 3.6))
    ax1.plot(d["local_date"], d["avg_price_eur_mwh"], color="#2c6e8f", linewidth=1)
    ax1.set_ylabel("Day-ahead price (EUR/MWh)", color="#2c6e8f")
    ax2 = ax1.twinx()
    ax2.plot(d["local_date"], d["energy_gwh"], color="#c0392b", linewidth=1, alpha=0.7)
    ax2.set_ylabel("Consumption (GWh/day)", color="#c0392b")
    ax1.set_title(f"{zone}: daily price and consumption, last 12 months", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(out / f"{zone}_daily.png", dpi=130)
    plt.close(fig)

    complete = daily[daily["hours_with_load"] >= 23]  # 23 or 25 hours on DST change days
    recent = complete.tail(7)[
        [
            "local_date",
            "energy_gwh",
            "peak_load_mw",
            "avg_price_eur_mwh",
            "negative_price_hours",
            "tso_forecast_mape_pct",
        ]
    ].copy()
    recent["local_date"] = recent["local_date"].dt.strftime("%Y-%m-%d")
    now = pd.Timestamp.now(tz="UTC")
    md = [
        f"# {zone} electricity report\n",
        f"Updated {now:%Y-%m-%d %H:%M} UTC by the scheduled pipeline. "
        f"Data: ENTSO-E Transparency Platform.\n",
        f"## Day-ahead load forecast, last {cfg['forecast']['holdout_weeks']} weeks\n",
        metrics.to_markdown(index=False),
        "",
        "### Week by week\n",
        "The table above averages over all backtest weeks. A forecast can come out ahead "
        "overall because of a few weeks where the other did badly, so check here whether "
        "the ranking holds week by week. Bias is forecast minus actual: negative means "
        "the forecast was too low.\n",
        forecast.weekly_metrics(preds, tz).round(1).to_markdown(index=False),
        "",
        f"![Forecasts]({zone}_forecast.png)\n",
        "## Last 7 days\n",
        recent.round(1).to_markdown(index=False),
        "",
        f"![Daily]({zone}_daily.png)\n",
        quality.to_markdown(checks, now).replace("# Data quality report", "## Data quality"),
    ]
    path = out / f"{zone}.md"
    path.write_text("\n".join(md), encoding="utf-8")
    return path
