import numpy as np
import pandas as pd
import pytest

from energy_pipeline import weekly

TZ = "Europe/Vilnius"


def hourly(days=10, end="2026-11-17 00:00"):
    """Constant 1000 MW load, TSO forecast 5 % high, price equal to the local hour."""
    ts = pd.date_range(
        end=pd.Timestamp(end, tz="UTC"), periods=days * 24, freq="h", inclusive="left"
    )
    return pd.DataFrame(
        {
            "zone": "LT",
            "ts_hour": ts,
            "load_mw": 1000.0,
            "tso_forecast_mw": 1050.0,
            "price_eur_mwh": ts.tz_convert(TZ).hour.astype(float),
            "load_completeness": 1.0,
        }
    )


def test_window_is_168_hours_ending_at_newest_actual_load():
    h = hourly()
    # The TSO forecast and price already exist for tomorrow; actual load does not.
    extra = hourly(days=1, end="2026-11-18 00:00").assign(load_mw=np.nan)
    r = weekly.build(pd.concat([h, extra]), "LT", TZ)
    assert r.n_hours == 168
    assert r.end == pd.Timestamp("2026-11-17 00:00", tz="UTC")
    assert r.start == pd.Timestamp("2026-11-10 00:00", tz="UTC")


def test_mae_and_mape_of_tso_forecast():
    r = weekly.build(hourly(), "LT", TZ)
    assert r.mae_mw == pytest.approx(50)
    assert r.mape_pct == pytest.approx(5)
    assert r.hours_compared == 168


def test_hours_missing_a_value_are_left_out_of_the_error():
    h = hourly()
    h.loc[h.index[-30:-20], "tso_forecast_mw"] = 2000.0
    h.loc[h.index[-30:-20], "load_mw"] = np.nan  # load missing: these hours must not count
    r = weekly.build(h, "LT", TZ)
    assert r.mape_pct == pytest.approx(5)
    assert r.hours_compared == 158


def test_gaps_are_found_per_series_with_run_lengths():
    h = hourly()
    week = h["ts_hour"] >= pd.Timestamp("2026-11-10", tz="UTC")
    first = h.index[week][0]
    h.loc[first + 10 : first + 12, "load_mw"] = np.nan  # 3 hours
    h.loc[first + 50, "price_eur_mwh"] = np.nan  # 1 hour
    h = h.drop(index=range(first + 100, first + 102))  # 2 hours absent from the table
    r = weekly.build(h, "LT", TZ)
    found = {(g.series, g.start, g.hours) for g in r.gaps}
    t0 = pd.Timestamp("2026-11-10", tz="UTC")
    hrs = pd.Timedelta(hours=1)
    assert found == {
        ("load_mw", t0 + 10 * hrs, 3),
        ("price_eur_mwh", t0 + 50 * hrs, 1),
        ("load_mw", t0 + 100 * hrs, 2),
        ("tso_forecast_mw", t0 + 100 * hrs, 2),
        ("price_eur_mwh", t0 + 100 * hrs, 2),
    }
    assert r.hours_with_gaps == 3 + 1 + 2


def test_no_gaps_and_partial_hours():
    h = hourly()
    h.loc[h.index[-3], "load_completeness"] = 0.75  # 3 of 4 quarter hours
    r = weekly.build(h, "LT", TZ)
    assert r.gaps == []
    assert r.partial_hours == 1


def test_price_profile_uses_local_hours():
    r = weekly.build(hourly(), "LT", TZ)
    assert list(r.price_profile.index) == list(range(24))
    np.testing.assert_allclose(r.price_profile.to_numpy(), np.arange(24))


def test_no_actual_load_raises():
    with pytest.raises(ValueError, match="no actual load"):
        weekly.build(hourly().assign(load_mw=np.nan), "LT", TZ)


def test_markdown_reports_metrics_gaps_and_prices():
    h = hourly()
    h.loc[h.index[-20], "load_mw"] = np.nan
    md = weekly.to_markdown(weekly.build(h, "LT", TZ), now=pd.Timestamp("2026-11-17", tz="UTC"))
    assert "| MAE | 50 MW |" in md
    assert "| MAPE | 5.00 % |" in md
    assert "| Hours compared | 167 of 168 |" in md
    assert "| Actual load | 2026-11-16 06:00 | 1 |" in md  # 04:00 UTC in Vilnius time
    assert "Average 11.5 EUR/MWh" in md
    assert "| 23:00 | 23.0 |" in md
    assert "![Load, forecast and price profile](latest.png)" in md


README = """# Title

[![badge](x)](y)

<!-- weekly-report:start -->
old content
<!-- weekly-report:end -->

## Rest of the README
"""


def test_readme_block_replaced_and_rest_kept():
    block = weekly.readme_block(weekly.build(hourly(), "LT", TZ))
    out = weekly.update_readme(README, block)
    assert "old content" not in out
    assert "| 5.00 % (MAE 50 MW) | 11.5 EUR/MWh | 0 of 168 |" in out
    assert "![Last 7 days: load, TSO forecast and price profile](reports/latest.png)" in out
    assert out.startswith("# Title\n\n[![badge](x)](y)\n\n<!-- weekly-report:start -->")
    assert out.endswith("<!-- weekly-report:end -->\n\n## Rest of the README\n")
    assert weekly.update_readme(out, block) == out  # running twice changes nothing


def test_readme_without_markers_raises():
    with pytest.raises(ValueError, match="weekly-report:start"):
        weekly.update_readme("# Title\n", "block")


def test_write_creates_png_markdown_and_updates_readme(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(README, encoding="utf-8")
    paths = weekly.write(weekly.build(hourly(), "LT", TZ), tmp_path / "reports", readme)
    png, md = tmp_path / "reports" / "latest.png", tmp_path / "reports" / "latest.md"
    assert paths == [png, md, readme]
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert md.read_text(encoding="utf-8").startswith("# LT weekly report")
    assert "old content" not in readme.read_text(encoding="utf-8")
