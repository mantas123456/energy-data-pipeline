"""PostgreSQL storage: raw observations, run log, and SQL transforms."""

from __future__ import annotations

import os
from importlib import resources

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine

DEFAULT_URL = "postgresql+psycopg://pipeline:pipeline@localhost:5432/energy"

metadata = MetaData()

observations = Table(
    "raw_observations",
    metadata,
    Column("zone", String(8), primary_key=True),
    Column("series", String(32), primary_key=True),
    Column("ts_utc", DateTime(timezone=True), primary_key=True),
    Column("resolution_min", Integer, nullable=False),
    Column("value", Float, nullable=False),
    Column("ingested_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
)

runs = Table(
    "ingest_runs",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("started_at", DateTime(timezone=True), server_default=func.now()),
    Column("zone", String(8)),
    Column("series", String(32)),
    Column("period_start", DateTime(timezone=True)),
    Column("period_end", DateTime(timezone=True)),
    Column("rows", Integer),
    Column("status", String(16)),
    Column("message", Text),
)


def engine(url: str | None = None) -> Engine:
    return create_engine(url or os.environ.get("DATABASE_URL", DEFAULT_URL), future=True)


def init(eng: Engine) -> None:
    metadata.create_all(eng)


def upsert_observations(eng: Engine, zone: str, series: str, df: pd.DataFrame) -> int:
    """Insert or update points. Re-running the same load is safe (idempotent).

    A point is only overwritten by data of equal or finer resolution, so an
    hourly series never replaces 15-minute values already stored.
    """
    if df.empty:
        return 0
    records = [
        {
            "zone": zone,
            "series": series,
            "ts_utc": r.ts_utc.to_pydatetime(),
            "resolution_min": int(r.resolution_min),
            "value": float(r.value),
        }
        for r in df.itertuples(index=False)
    ]
    stmt = insert(observations)
    stmt = stmt.on_conflict_do_update(
        index_elements=["zone", "series", "ts_utc"],
        set_={
            "value": stmt.excluded.value,
            "resolution_min": stmt.excluded.resolution_min,
            "ingested_at": func.now(),
        },
        where=stmt.excluded.resolution_min <= observations.c.resolution_min,
    )
    with eng.begin() as conn:
        for i in range(0, len(records), 5000):
            conn.execute(stmt, records[i : i + 5000])
    return len(records)


def log_run(eng: Engine, **fields) -> None:
    with eng.begin() as conn:
        conn.execute(runs.insert().values(**fields))


def sql_files() -> list[tuple[str, str]]:
    folder = resources.files("energy_pipeline") / "sql"
    files = sorted(f for f in folder.iterdir() if f.name.endswith(".sql"))
    return [(f.name, f.read_text(encoding="utf-8")) for f in files]


def transform(eng: Engine) -> list[str]:
    """Run the SQL models in file-name order. Returns the files executed."""
    done = []
    with eng.begin() as conn:
        for name, sql in sql_files():
            conn.exec_driver_sql(sql)
            done.append(name)
    return done


def read_sql(eng: Engine, query: str, **params) -> pd.DataFrame:
    with eng.connect() as conn:
        return pd.read_sql(text(query), conn, params=params)
