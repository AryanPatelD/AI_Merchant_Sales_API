"""API authentication, request IDs, rate limiting, and audit persistence."""

import hashlib
import hmac
import time
from collections import defaultdict, deque
from threading import Lock
from uuid import UUID, uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import Settings
from app.database.connection import database_connection

PUBLIC_PATHS = {"/health", "/.well-known/ai-commerce", "/webhooks/razorpay"}


def hash_api_key(api_key: str, pepper: str) -> str:
    return hmac.new(pepper.encode(), api_key.encode(), hashlib.sha256).hexdigest()


def authenticate_api_key(settings: Settings, api_key: str | None) -> UUID | None:
    if not settings.api_auth_enabled:
        return None
    if not api_key or settings.api_key_pepper is None:
        return None
    digest = hash_api_key(api_key, settings.api_key_pepper.get_secret_value())
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT client_id FROM api_clients
                WHERE merchant_id = %s AND api_key_hash = %s AND status = 'ACTIVE'
                """,
                (settings.merchant_id, digest),
            )
            row = cursor.fetchone()
    return row["client_id"] if row else None


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, client: str, endpoint: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        cutoff = now - window
        key = (client, endpoint)
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False
            events.append(now)
            return True


rate_limiter = InMemoryRateLimiter()


def write_audit_log(
    settings: Settings,
    request: Request,
    request_id: str,
    client_id: UUID | None,
    response_status: int,
) -> None:
    if not settings.audit_log_enabled or request.url.path in PUBLIC_PATHS:
        return
    action = f"{request.method} {request.url.path}"
    entity_id = request.query_params.get("order_id")
    try:
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO audit_logs (
                        audit_id, client_id, endpoint, http_method,
                        entity_type, entity_id, action, request_id, response_status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(), client_id, request.url.path, request.method,
                        "order" if entity_id else None, entity_id, action,
                        request_id, response_status,
                    ),
                )
    except Exception:
        # Observability must not turn a successful commerce operation into a 500.
        return


async def security_middleware(request: Request, call_next, settings: Settings):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    client_id = None
    protected = request.url.path.startswith("/api/v1")
    if protected and settings.api_auth_enabled:
        client_id = authenticate_api_key(settings, request.headers.get("X-API-Key"))
        if client_id is None:
            return JSONResponse(
                {"detail": "Invalid or missing API key"},
                status_code=401,
                headers={"X-Request-ID": request_id},
            )

    client_key = str(client_id) if client_id else request.client.host if request.client else "unknown"
    if protected and settings.rate_limit_enabled and not rate_limiter.allow(
        client_key, request.url.path, settings.rate_limit_requests,
        settings.rate_limit_window_seconds,
    ):
        return JSONResponse(
            {"detail": "Rate limit exceeded"},
            status_code=429,
            headers={"X-Request-ID": request_id, "Retry-After": str(settings.rate_limit_window_seconds)},
        )

    request.state.request_id = request_id
    request.state.client_id = client_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    write_audit_log(settings, request, request_id, client_id, response.status_code)
    return response
