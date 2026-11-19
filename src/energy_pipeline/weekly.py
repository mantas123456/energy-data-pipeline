"""Weekly report: the last 7 days of load, the TSO forecast's error, data gaps and prices.

Writes reports/latest.md and reports/latest.png and refreshes a marked block at the top of
README.md. The calculations are plain functions over the hourly table so they can be tested
without a database.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SERIES = {
    "load_mw": "Actual load",
    "tso_forecast_mw": "TSO day-ahead forecast",
    "price_eur_mwh": "Day-ahead price",
}
README_START = "<!-- weekly-report:start -->"
README_END = "<!-- weekly-report:end -->"


@dataclass(frozen=True)
class Gap:
    series: str
    start: pd.Timestamp  # first missing hour, UTC
    hours: int


@dataclass
class WeeklyReport:
    zone: str
    tz: str
    start: pd.Timestamp  # first hour, UTC, inclusive
    end: pd.Timestamp  # last hour + 1 h, UTC, exclusive
    hourly: pd.DataFrame  # one row per hour in [start, end), NaN where missing
    mae_mw: float
    mape_pct: float
    hours_compared: int
    gaps: list[Gap]
    partial_hours: int  # hours with some but not all sub-hourly load points
    price_profile: pd.Series  # mean price by local hour of day (0..23)

    @property
    def n_hours(self) -> int:
        return len(self.hourly)

    @property
    def hours_with_gaps(self) -> int:
        """Hours where at least one of the three series is missing."""
        return int(self.hourly[list(SERIES)].isna().any(axis=1).sum())


def week_window(h: pd.DataFrame, days: int = 7) -> tuple[pd.Timestamp, pd.Timestamp]:
    """The `days` x 24 hours ending with the newest hour that has actual load."""
    last = h.loc[h["load_mw"].notna(), "ts_hour"].max()
    if pd.isna(last):
        raise ValueError("no actual load in the hourly data")
    end = last + pd.Timedelta(hours=1)
    return end - pd.Timedelta(days=days), end


def find_gaps(hourly: pd.DataFrame) -> list[Gap]:
    """Runs of consecutive missing hours for each series."""
    gaps = []
    for col in SERIES:
        missing = hourly[col].isna().to_numpy()
        i = 0
        while i < len(missing):
            if missing[i]:
                j = i
                while j < len(missing) and missing[j]:
                    j += 1
                gaps.append(Gap(col, hourly.index[i], j - i))
                i = j
            else:
                i += 1
    return gaps


def build(h: pd.DataFrame, zone: str, tz: str, days: int = 7) -> WeeklyReport:
    """Build the report from mart_hourly rows (ts_hour, load_mw, tso_forecast_mw, ...)."""
    h = h.copy()
    h["ts_hour"] = pd.to_datetime(h["ts_hour"], utc=True)
    start, end = week_window(h, days)
    idx = pd.date_range(start, end, freq="h", inclusive="left", name="ts_hour")
    cols = list(SERIES) + (["load_completeness"] if "load_completeness" in h else [])
    hourly = h.set_index("ts_hour")[cols].reindex(idx)

    both = hourly.dropna(subset=["load_mw", "tso_forecast_mw"])
    both = both[both["load_mw"] > 0]
    err = (both["tso_forecast_mw"] - both["load_mw"]).abs()
    mae = float(err.mean()) if len(both) else float("nan")
    mape = float((err / both["load_mw"]).mean() * 100) if len(both) else float("nan")

    partial = 0
    if "load_completeness" in hourly:
        c = hourly["load_completeness"]
        partial = int(((c < 1) & hourly["load_mw"].notna()).sum())

    price = hourly["price_eur_mwh"].dropna()
    profile = price.groupby(price.index.tz_convert(tz).hour).mean().reindex(range(24))
    profile.index.name = "local_hour"

    return WeeklyReport(
        zone, tz, start, end, hourly, mae, mape, len(both), find_gaps(hourly), partial, profile
    )


# ------------------------------------------------------------------ output


def _fmt(x: float, digits: int = 1) -> str:
    return "n/a" if x is None or np.isnan(x) else f"{x:,.{digits}f}"


def _local(ts: pd.Timestamp, tz: str) -> str:
    return f"{ts.tz_convert(tz):%Y-%m-%d %H:%M}"


def period_text(r: WeeklyReport) -> str:
    last = r.end - pd.Timedelta(hours=1)
    return f"{_local(r.start, r.tz)} to {_local(last, r.tz)} ({r.tz} time)"


def plot(r: WeeklyReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    local = r.hourly.tz_convert(r.tz)
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(9, 6), gridspec_kw={"height_ratios": [3, 2]}, constrained_layout=True
    )
    ax1.plot(local.index, local["load_mw"], color="black", linewidth=1.4, label="Actual load")
    ax1.plot(
        local.index,
        local["tso_forecast_mw"],
        "--",
        color="#2c6e8f",
        linewidth=1.1,
        label="TSO day-ahead forecast",
    )
    ax1.set_ylabel("MW")
    ax1.set_title(
        f"{r.zone}: hourly load vs TSO day-ahead forecast, MAPE {_fmt(r.mape_pct, 2)} %",
        loc="left",
        fontsize=10,
    )
    ax1.legend(frameon=False, fontsize=8, ncol=2, loc="upper right")
    ax1.grid(alpha=0.3)

    p = r.price_profile
    ax2.bar(p.index, p.to_numpy(), color="#c0392b", alpha=0.8)
    ax2.axhline(0, color="black", linewidth=0.6)
    ax2.set_xticks(range(0, 24, 3))
    ax2.set_xlabel(f"Hour of day ({r.tz})")
    ax2.set_ylabel("EUR/MWh")
    ax2.set_title("Average day-ahead price by hour of day, same 7 days", loc="left", fontsize=10)
    ax2.grid(axis="y", alpha=0.3)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def to_markdown(r: WeeklyReport, chart: str = "latest.png", now: pd.Timestamp | None = None) -> str:
    now = now or pd.Timestamp.now(tz="UTC")
    price = r.hourly["price_eur_mwh"]
    lines = [
        f"# {r.zone} weekly report\n",
        f"Period: {period_text(r)}, {r.n_hours} hours. "
        f"Generated {now:%Y-%m-%d %H:%M} UTC by the weekly workflow. "
        "Data: ENTSO-E Transparency Platform.\n",
        f"![Load, forecast and price profile]({chart})\n",
        "## TSO day-ahead load forecast\n",
        "| Metric | Value |",
        "|---|---|",
        f"| MAE | {_fmt(r.mae_mw, 0)} MW |",
        f"| MAPE | {_fmt(r.mape_pct, 2)} % |",
        f"| Hours compared | {r.hours_compared} of {r.n_hours} |",
        "",
        "Error of the TSO's published day-ahead forecast against actual load, "
        "hour by hour. Hours missing either value are left out.\n",
        "## Data gaps\n",
    ]
    if r.gaps:
        lines += ["| Series | First missing hour | Hours |", "|---|---|---:|"]
        lines += [f"| {SERIES[g.series]} | {_local(g.start, r.tz)} | {g.hours} |" for g in r.gaps]
        lines.append("")
    else:
        lines.append("No missing hours in any series.\n")
    lines.append(
        f"Hours with at least one series missing: {r.hours_with_gaps} of {r.n_hours}. "
        f"Hours with incomplete sub-hourly load data: {r.partial_hours}.\n"
    )
    lines += [
        "## Day-ahead price\n",
        f"Average {_fmt(price.mean())} EUR/MWh, lowest hour {_fmt(price.min())}, "
        f"highest hour {_fmt(price.max())}, hours below zero: {int((price < 0).sum())}.\n",
        f"| Hour ({r.tz}) | Average price (EUR/MWh) |",
        "|---:|---:|",
    ]
    lines += [f"| {hr:02d}:00 | {_fmt(v)} |" for hr, v in r.price_profile.items()]
    return "\n".join(lines) + "\n"


def readme_block(r: WeeklyReport, report_dir: str = "reports") -> str:
    avg_price = r.hourly["price_eur_mwh"].mean()
    return "\n".join(
        [
            README_START,
            f"**Last 7 days:** {period_text(r)}. "
            f"Updated weekly; [full report]({report_dir}/latest.md).",
            "",
            "| TSO forecast error (MAPE) | Average day-ahead price | Hours with missing data |",
            "|---|---|---|",
            f"| {_fmt(r.mape_pct, 2)} % (MAE {_fmt(r.mae_mw, 0)} MW) "
            f"| {_fmt(avg_price)} EUR/MWh "
            f"| {r.hours_with_gaps} of {r.n_hours} |",
            "",
            f"![Last 7 days: load, TSO forecast and price profile]({report_dir}/latest.png)",
            README_END,
        ]
    )


def update_readme(text: str, block: str) -> str:
    """Replace the marked block in README text. Raises if the markers are missing."""
    pattern = re.compile(re.escape(README_START) + r".*?" + re.escape(README_END), re.S)
    if not pattern.search(text):
        raise ValueError(f"README has no {README_START} ... {README_END} block")
    return pattern.sub(lambda _: block, text, count=1)


def write(r: WeeklyReport, out: Path, readme: Path | None = None) -> list[Path]:
    """Write latest.md and latest.png to `out`, and refresh the README block if given."""
    out.mkdir(parents=True, exist_ok=True)
    paths = [plot(r, out / "latest.png")]
    md = out / "latest.md"
    md.write_text(to_markdown(r), encoding="utf-8")
    paths.append(md)
    if readme is not None:
        text = readme.read_text(encoding="utf-8")
        readme.write_text(update_readme(text, readme_block(r)), encoding="utf-8")
        paths.append(readme)
    return paths
