"""Data quality checks on the hourly mart."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy.engine import Engine

from .db import read_sql


@dataclass(frozen=True)
class Check:
    zone: str
    name: str
    status: str  # "pass", "warn" or "fail"
    detail: str


def longest_gap_hours(present: pd.Series, start: pd.Timestamp, end: pd.Timestamp) -> int:
    """Longest run of consecutive missing hours between start and end (inclusive)."""
    expected = pd.date_range(start, end, freq="h", tz="UTC")
    have = set(pd.to_datetime(present, utc=True))
    longest = run = 0
    for ts in expected:
        run = 0 if ts in have else run + 1
        longest = max(longest, run)
    return longest


def run_checks(
    eng: Engine, cfg: dict, window_days: int = 30, now: pd.Timestamp | None = None
) -> list[Check]:
    c = cfg["checks"]
    now = now or pd.Timestamp.now(tz="UTC")
    results: list[Check] = []
    for zone in cfg["zones"]:
        h = read_sql(
            eng, "SELECT * FROM mart_hourly WHERE zone = :zone ORDER BY ts_hour", zone=zone
        )
        if h.empty:
            results.append(Check(zone, "data present", "fail", "no rows in mart_hourly"))
            continue
        h["ts_hour"] = pd.to_datetime(h["ts_hour"], utc=True)
        recent = h[h["ts_hour"] >= now - pd.Timedelta(days=window_days)]
        load = recent.dropna(subset=["load_mw"])

        # Freshness of actual load.
        last = h.dropna(subset=["load_mw"])["ts_hour"].max()
        age = (now - last) / pd.Timedelta(hours=1) if pd.notna(last) else float("inf")
        results.append(
            Check(
                zone,
                "load is fresh",
                "pass" if age <= c["stale_after_hours"] else "fail",
                f"latest actual load {last:%Y-%m-%d %H:%M} UTC ({age:.0f} h old)"
                if pd.notna(last)
                else "no actual load",
            )
        )

        # Gaps in actual load within the window, up to the latest value.
        if not load.empty:
            gap = longest_gap_hours(load["ts_hour"], load["ts_hour"].min(), last)
            missing = int((last - load["ts_hour"].min()) / pd.Timedelta(hours=1)) + 1 - len(load)
            status = "pass" if gap == 0 else ("warn" if gap <= c["max_gap_hours"] else "fail")
            results.append(
                Check(
                    zone,
                    "no gaps in actual load",
                    status,
                    f"{missing} missing hours, longest gap {gap} h (last {window_days} days)",
                )
            )

        # Plausible ranges.
        for col, bounds, label in [
            ("load_mw", c["load_mw"], "load"),
            ("price_eur_mwh", c["price_eur_mwh"], "price"),
        ]:
            vals = recent[col].dropna()
            bad = vals[(vals < bounds[0]) | (vals > bounds[1])]
            results.append(
                Check(
                    zone,
                    f"{label} within {bounds[0]}..{bounds[1]}",
                    "pass" if bad.empty else "fail",
                    f"{len(bad)} of {len(vals)} hours outside range",
                )
            )

        # Partial hours (sub-hourly points missing).
        partial = (load["load_completeness"] < 0.999).sum() if not load.empty else 0
        results.append(
            Check(
                zone,
                "complete hours",
                "pass" if partial == 0 else "warn",
                f"{partial} hours built from incomplete sub-hourly data",
            )
        )
    return results


def to_markdown(results: list[Check], now: pd.Timestamp | None = None) -> str:
    now = now or pd.Timestamp.now(tz="UTC")
    icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
    lines = [
        f"# Data quality report\n\nGenerated {now:%Y-%m-%d %H:%M} UTC\n",
        "| Zone | Check | Result | Detail |",
        "|---|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.zone} | {r.name} | {icon[r.status]} {r.status} | {r.detail} |")
    return "\n".join(lines) + "\n"
