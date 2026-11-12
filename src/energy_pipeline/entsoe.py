"""Client and XML parser for the ENTSO-E Transparency Platform REST API.

API guide: https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html

Two details the parser has to handle:
- Curve type A03: points whose value equals the previous point are omitted, so
  missing positions inside a period are filled forward.
- Mixed resolutions: since the move to 15-minute day-ahead products in
  October 2025 a response can contain PT15M and PT60M series for the same
  hours. The finest resolution available for each timestamp is kept.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from lxml import etree

log = logging.getLogger(__name__)

API_URL = "https://web-api.tp.entsoe.eu/api"


@dataclass(frozen=True)
class SeriesSpec:
    name: str
    params: dict[str, str]  # extra query params; "{eic}" is replaced by the zone code
    value_tag: str
    unit: str


SERIES: dict[str, SeriesSpec] = {
    "load_actual": SeriesSpec(
        "load_actual",
        {"documentType": "A65", "processType": "A16", "outBiddingZone_Domain": "{eic}"},
        "quantity",
        "MW",
    ),
    "load_forecast_tso": SeriesSpec(
        "load_forecast_tso",
        {"documentType": "A65", "processType": "A01", "outBiddingZone_Domain": "{eic}"},
        "quantity",
        "MW",
    ),
    "price_day_ahead": SeriesSpec(
        "price_day_ahead",
        {
            "documentType": "A44",
            "in_Domain": "{eic}",
            "out_Domain": "{eic}",
            "contract_MarketAgreement.type": "A01",
        },
        "price.amount",
        "EUR/MWh",
    ),
}

_DURATION = re.compile(r"^PT(?:(\d+)H)?(?:(\d+)M)?$")


COLUMNS = ["ts_utc", "resolution_min", "value"]


def empty() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts_utc": pd.Series(dtype="datetime64[ns, UTC]"),
            "resolution_min": pd.Series(dtype="int64"),
            "value": pd.Series(dtype="float64"),
        }
    )


class EntsoeError(RuntimeError):
    pass


def resolution_minutes(text: str) -> int:
    m = _DURATION.match(text.strip())
    if not m or not any(m.groups()):
        raise ValueError(f"unsupported resolution {text!r}")
    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)


def _local(tag) -> str:
    return etree.QName(tag).localname


def _children(el, name):
    return [c for c in el if isinstance(c.tag, str) and _local(c.tag) == name]


def _child(el, name):
    found = _children(el, name)
    return found[0] if found else None


def _parse_time(text: str) -> datetime:
    return datetime.strptime(text.strip(), "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)


def parse(xml: bytes, value_tag: str) -> pd.DataFrame:
    """Parse a market document into columns ts_utc, resolution_min, value.

    Returns an empty frame for an acknowledgement saying no data matched.
    Raises EntsoeError for any other acknowledgement (bad token, bad query).
    """
    root = etree.fromstring(xml)
    if _local(root.tag) == "Acknowledgement_MarketDocument":
        reason = root.xpath("string(//*[local-name()='Reason']/*[local-name()='text'])")
        if "No matching data found" in reason:
            return empty()
        raise EntsoeError(reason or "acknowledgement without reason")

    rows = []
    for ts in root.iter("{*}TimeSeries"):
        curve = _child(ts, "curveType")
        compressed = curve is not None and curve.text.strip() == "A03"
        for period in _children(ts, "Period"):
            interval = _child(period, "timeInterval")
            start = _parse_time(_child(interval, "start").text)
            end = _parse_time(_child(interval, "end").text)
            res = resolution_minutes(_child(period, "resolution").text)
            n = int((end - start) / timedelta(minutes=res))
            points = {}
            for p in _children(period, "Point"):
                pos = int(_child(p, "position").text)
                val = _child(p, value_tag)
                if val is not None:
                    points[pos] = float(val.text)
            if not points:
                continue
            last = None
            for pos in range(1, n + 1):
                if pos in points:
                    last = points[pos]
                elif not compressed:
                    continue  # A01 curves list every point; a gap means missing data
                if last is None:
                    continue
                rows.append((start + timedelta(minutes=res * (pos - 1)), res, last))

    if not rows:
        return empty()
    df = pd.DataFrame(rows, columns=COLUMNS)
    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    # Keep the finest resolution for each timestamp.
    df = df.sort_values(["ts_utc", "resolution_min"]).drop_duplicates("ts_utc", keep="first")
    return df.reset_index(drop=True)


class EntsoeClient:
    """Fetches one series for one zone, splitting long ranges into chunks."""

    def __init__(
        self,
        token: str,
        session: requests.Session | None = None,
        max_days_per_request: int = 90,
        retries: int = 4,
        pause_s: float = 0.2,
    ):
        if not token:
            raise ValueError("an ENTSO-E API token is required")
        self.token = token
        self.session = session or requests.Session()
        self.max_days = max_days_per_request
        self.retries = retries
        self.pause_s = pause_s

    def _request(self, params: dict[str, str]) -> bytes:
        for attempt in range(1, self.retries + 1):
            r = self.session.get(
                API_URL, params={"securityToken": self.token, **params}, timeout=60
            )
            if r.status_code == 200 or (r.status_code == 400 and b"Acknowledgement" in r.content):
                return r.content
            if r.status_code in (429, 500, 502, 503, 504) and attempt < self.retries:
                wait = 2**attempt
                log.warning("ENTSO-E returned %s, retrying in %ss", r.status_code, wait)
                time.sleep(wait)
                continue
            raise EntsoeError(f"HTTP {r.status_code}: {r.text[:300]}")
        raise EntsoeError("no response")

    def fetch(self, series: str, eic: str, start: datetime, end: datetime) -> pd.DataFrame:
        spec = SERIES[series]
        frames = []
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=self.max_days), end)
            params = {k: v.format(eic=eic) for k, v in spec.params.items()}
            params["periodStart"] = chunk_start.strftime("%Y%m%d%H%M")
            params["periodEnd"] = chunk_end.strftime("%Y%m%d%H%M")
            df = parse(self._request(params), spec.value_tag)
            log.info(
                "%s %s %s..%s: %d points",
                series,
                eic,
                chunk_start.date(),
                chunk_end.date(),
                len(df),
            )
            frames.append(df)
            chunk_start = chunk_end
            time.sleep(self.pause_s)
        frames = [f for f in frames if not f.empty]
        out = pd.concat(frames, ignore_index=True) if frames else empty()
        out = out[(out["ts_utc"] >= pd.Timestamp(start)) & (out["ts_utc"] < pd.Timestamp(end))]
        return out.sort_values(["ts_utc", "resolution_min"]).drop_duplicates("ts_utc")
