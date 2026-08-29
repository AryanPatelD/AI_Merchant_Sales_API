"""PostgreSQL connection helpers."""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from app.config import get_settings


def psycopg_database_url() -> str:
    """Convert SQLAlchemy's psycopg URL form to a native psycopg DSN."""
    return get_settings().database_url.replace(
        "postgresql+psycopg://", "postgresql://", 1
    )


@contextmanager
def database_connection() -> Iterator[Connection]:
    """Provide a short-lived database connection with dictionary rows."""
    with psycopg.connect(psycopg_database_url(), row_factory=dict_row) as connection:
        yield connection

