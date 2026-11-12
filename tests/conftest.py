import os

import pytest
from sqlalchemy import text

from energy_pipeline import db


@pytest.fixture()
def eng():
    """A clean PostgreSQL database. Tests using it are skipped without DATABASE_URL."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set")
    e = db.engine(url)
    with e.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    yield e
    e.dispose()
