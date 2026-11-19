"""Command line interface.

pipeline backfill              load everything from backfill_start to tomorrow
pipeline update                re-fetch the last daily_lookback_days days
pipeline restore               rebuild the database from data/observations
pipeline transform             run the SQL models
pipeline check [--strict]      data quality checks (exit 1 on failure with --strict)
pipeline report                backtest the forecast and write reports/
pipeline export                write data/observations from the database
pipeline daily                 restore, update, transform, check, report, export
pipeline weekly                restore, transform, write reports/latest.* and the README block
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

from . import db, pipeline, quality, weekly
from .entsoe import EntsoeClient

log = logging.getLogger("energy_pipeline")


def client() -> EntsoeClient:
    token = os.environ.get("ENTSOE_API_KEY", "")
    if not token:
        sys.exit("ENTSOE_API_KEY is not set. See README: Getting an API key.")
    return EntsoeClient(token)


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    ap = argparse.ArgumentParser(
        prog="pipeline", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "command",
        choices=[
            "backfill",
            "update",
            "restore",
            "transform",
            "check",
            "report",
            "export",
            "daily",
            "weekly",
        ],
    )
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--strict", action="store_true", help="exit 1 if a check fails")
    ap.add_argument("--start", help="backfill start date, YYYY-MM-DD (overrides config)")
    args = ap.parse_args(argv)

    cfg = pipeline.load_config(args.config)
    eng = db.engine()
    pipeline.sync_zones(eng, cfg)
    cmd = args.command

    if cmd in ("restore", "daily", "weekly"):
        log.info("Restored %d points from data/", pipeline.restore_raw(eng, cfg))
    if cmd == "backfill":
        start = datetime.fromisoformat(args.start or cfg["backfill_start"]).replace(
            tzinfo=timezone.utc
        )
        _, end = pipeline.window(0)
        log.info("Ingested %d points", pipeline.ingest(eng, cfg, client(), start, end))
    if cmd in ("update", "daily"):
        start, end = pipeline.window(cfg["daily_lookback_days"])
        log.info("Ingested %d points", pipeline.ingest(eng, cfg, client(), start, end))
    if cmd in ("backfill", "update", "restore", "transform", "daily", "weekly"):
        log.info("Ran SQL models: %s", ", ".join(db.transform(eng)))

    checks = None
    if cmd in ("check", "report", "daily"):
        checks = quality.run_checks(eng, cfg)
        for c in checks:
            log.info("[%s] %s %s: %s", c.status.upper(), c.zone, c.name, c.detail)
    if cmd in ("report", "daily"):
        for zone in cfg["zones"]:
            try:
                metrics, preds, _ = pipeline.run_forecast(eng, cfg, zone)
            except pipeline.NoDataError as e:
                log.error("%s", e)
                return 1
            log.info("Forecast backtest %s:\n%s", zone, metrics.to_string(index=False))
            log.info("Wrote %s", pipeline.write_report(eng, cfg, zone, metrics, preds, checks))
    if cmd == "weekly":
        for zone, z in cfg["zones"].items():
            h = db.read_sql(
                eng, "SELECT * FROM mart_hourly WHERE zone = :zone ORDER BY ts_hour", zone=zone
            )
            if h.empty or h["load_mw"].isna().all():
                log.error(
                    "No load data for zone %s: nothing to report. Has the daily job run?", zone
                )
                return 1
            report = weekly.build(h, zone, z["timezone"])
            readme = pipeline.ROOT / "README.md"
            for path in weekly.write(report, pipeline.ROOT / "reports", readme):
                log.info("Wrote %s", path)
            log.info(
                "%s: MAPE %.2f %%, MAE %.0f MW, %d of %d hours with missing data",
                zone,
                report.mape_pct,
                report.mae_mw,
                report.hours_with_gaps,
                report.n_hours,
            )
            break  # reports/latest.* holds one zone; the first configured zone is reported
    if cmd in ("export", "daily"):
        log.info("Exported %d changed files", len(pipeline.export_raw(eng)))

    if args.strict and checks and any(c.status == "fail" for c in checks):
        log.error("One or more data quality checks failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
