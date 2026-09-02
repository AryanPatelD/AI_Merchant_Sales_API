"""Reusable PostgreSQL-backed idempotency for transactional endpoints."""

from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel
from psycopg.types.json import Jsonb

from app.database.connection import database_connection

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class IdempotencyConflictError(Exception):
    pass


def run_idempotent(
    key: str,
    endpoint: str,
    response_type: type[ResponseT],
    operation: Callable[[], ResponseT],
) -> ResponseT:
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO idempotency_keys (
                    idempotency_key, endpoint, created_at, expires_at
                ) VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '24 hours')
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING idempotency_key
                """,
                (key, endpoint),
            )
            owns_key = cursor.fetchone() is not None
            if not owns_key:
                cursor.execute(
                    """
                    SELECT endpoint, response_body FROM idempotency_keys
                    WHERE idempotency_key = %s
                    """,
                    (key,),
                )
                existing = cursor.fetchone()
                if (
                    existing is None
                    or existing["endpoint"] != endpoint
                    or existing["response_body"] is None
                ):
                    raise IdempotencyConflictError
                return response_type.model_validate(existing["response_body"])

    try:
        response = operation()
    except Exception:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM idempotency_keys WHERE idempotency_key = %s AND endpoint = %s",
                    (key, endpoint),
                )
        raise

    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE idempotency_keys SET response_status = 201, response_body = %s
                WHERE idempotency_key = %s AND endpoint = %s
                """,
                (Jsonb(response.model_dump(mode="json")), key, endpoint),
            )
    return response
