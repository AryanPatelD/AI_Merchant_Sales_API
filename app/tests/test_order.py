"""Order status API tests."""

from datetime import UTC, date, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.order import OrderStatusResponse
from app.schemas.payment import PaymentStatus
from app.services.order import OrderNotFoundError

client = TestClient(app)
ORDER_ID = UUID("e939539f-29c2-4eb8-b796-5a568341ed21")


def test_order_status_route(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.order.get_order_status",
        lambda settings, order_id: OrderStatusResponse(
            order_id=order_id,
            order_status="PROCESSING",
            payment_status=PaymentStatus.CAPTURED,
            tracking=None,
            estimated_delivery_date=date(2026, 9, 4),
            eta_days=2,
            status_history=[{
                "previous_status": "PAID",
                "status": "PROCESSING",
                "changed_at": datetime(2026, 9, 2, tzinfo=UTC),
            }],
        ),
    )
    response = client.get("/api/v1/order-status", params={"order_id": str(ORDER_ID)})
    assert response.status_code == 200
    assert response.json()["payment_status"] == "CAPTURED"
    assert response.json()["eta_days"] == 2


def test_order_status_rejects_invalid_uuid() -> None:
    assert client.get("/api/v1/order-status", params={"order_id": "bad"}).status_code == 422


def test_order_status_returns_404(monkeypatch) -> None:
    def missing(settings, order_id):
        raise OrderNotFoundError
    monkeypatch.setattr("app.api.order.get_order_status", missing)
    response = client.get("/api/v1/order-status", params={"order_id": str(ORDER_ID)})
    assert response.status_code == 404
