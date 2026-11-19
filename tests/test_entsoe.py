from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from energy_pipeline.entsoe import EntsoeClient, EntsoeError, parse, resolution_minutes

FIX = Path(__file__).parent / "fixtures"


def read(name):
    return (FIX / name).read_bytes()


@pytest.mark.parametrize(
    "text,minutes", [("PT15M", 15), ("PT60M", 60), ("PT1H", 60), ("PT30M", 30)]
)
def test_resolution(text, minutes):
    assert resolution_minutes(text) == minutes


def test_load_15min_points():
    df = parse(read("load_a01_pt15m.xml"), "quantity")
    assert len(df) == 4
    assert df["ts_utc"].iloc[0] == pd.Timestamp("2026-01-05T22:00Z")
    assert df["ts_utc"].iloc[-1] == pd.Timestamp("2026-01-05T22:45Z")
    assert (df["resolution_min"] == 15).all()
    assert df["value"].tolist() == [1200, 1180, 1160, 1140]


def test_a03_curve_fills_omitted_positions_forward():
    df = parse(read("price_a03_compressed.xml"), "price.amount")
    assert len(df) == 6
    assert df["value"].tolist() == [85.5, 80.0, 80.0, 80.0, -1.2, -1.2]


def test_mixed_resolution_keeps_finest():
    df = parse(read("price_mixed_resolution.xml"), "price.amount").set_index("ts_utc")
    first_hour = df.loc["2026-01-05T23:00Z":"2026-01-05T23:45Z"]
    assert len(first_hour) == 4 and (first_hour["resolution_min"] == 15).all()
    assert df.loc[pd.Timestamp("2026-01-06T00:00Z"), "value"] == 90
    assert df.loc[pd.Timestamp("2026-01-06T00:00Z"), "resolution_min"] == 60


def test_no_data_acknowledgement_is_empty():
    assert parse(read("ack_no_data.xml"), "price.amount").empty


def test_other_acknowledgement_raises():
    with pytest.raises(EntsoeError, match="Unauthorized"):
        parse(read("ack_bad_token.xml"), "price.amount")


class FakeResponse:
    def __init__(self, content, status=200):
        self.content, self.status_code, self.text = content, status, content.decode()


class FakeSession:
    def __init__(self, content):
        self.content, self.calls = content, []

    def get(self, url, params, timeout):
        self.calls.append(params)
        return FakeResponse(self.content)


def test_client_chunks_long_ranges_and_builds_params():
    s = FakeSession(read("load_a01_pt15m.xml"))
    c = EntsoeClient("token", session=s, max_days_per_request=30, pause_s=0)
    df = c.fetch(
        "load_actual",
        "10YLT-1001A0008Q",
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 3, 1, tzinfo=timezone.utc),
    )
    assert len(s.calls) == 2
    p = s.calls[0]
    assert p["documentType"] == "A65" and p["processType"] == "A16"
    assert p["outBiddingZone_Domain"] == "10YLT-1001A0008Q"
    assert p["periodStart"] == "202601010000" and p["periodEnd"] == "202601310000"
    assert len(df) == 4  # duplicate points across chunks are removed


def test_price_query_uses_in_and_out_domain():
    s = FakeSession(read("ack_no_data.xml"))
    c = EntsoeClient("token", session=s, pause_s=0)
    df = c.fetch(
        "price_day_ahead",
        "X",
        datetime(2026, 1, 1, tzinfo=timezone.utc),
        datetime(2026, 1, 2, tzinfo=timezone.utc),
    )
    assert df.empty
    assert s.calls[0]["in_Domain"] == "X" and s.calls[0]["out_Domain"] == "X"


def test_client_requires_token():
    with pytest.raises(ValueError):
        EntsoeClient("")
