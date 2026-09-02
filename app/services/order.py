"""Order-status and fulfillment queries."""

from datetime import date
from uuid import UUID

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.order import (
    OrderStatusHistoryEntry,
    OrderStatusResponse,
    TrackingDetails,
)


class OrderNotFoundError(Exception):
    pass


def get_order_status(settings: Settings, order_id: UUID) -> OrderStatusResponse:
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT o.order_id, o.order_status, p.payment_status,
                       s.courier_name, s.tracking_number, s.shipment_status,
                       s.estimated_delivery_date, s.shipped_at, s.delivered_at,
                       inventory_eta.eta_days
                FROM orders AS o
                LEFT JOIN payments AS p ON p.order_id = o.order_id
                LEFT JOIN LATERAL (
                    SELECT courier_name, tracking_number, shipment_status,
                           estimated_delivery_date, shipped_at, delivered_at
                    FROM shipments WHERE order_id = o.order_id
                    ORDER BY COALESCE(shipped_at, o.created_at) DESC LIMIT 1
                ) AS s ON TRUE
                LEFT JOIN LATERAL (
                    SELECT MAX(i.eta_days)::integer AS eta_days
                    FROM order_items AS oi
                    JOIN inventory AS i ON i.product_id = oi.product_id
                    WHERE oi.order_id = o.order_id
                ) AS inventory_eta ON TRUE
                WHERE o.order_id = %s AND o.merchant_id = %s
                """,
                (order_id, settings.merchant_id),
            )
            order = cursor.fetchone()
            if order is None:
                raise OrderNotFoundError

            cursor.execute(
                """
                SELECT previous_status, new_status, changed_at
                FROM order_status_history
                WHERE order_id = %s ORDER BY sequence_number
                """,
                (order_id,),
            )
            history = [
                OrderStatusHistoryEntry(
                    previous_status=row["previous_status"],
                    status=row["new_status"],
                    changed_at=row["changed_at"],
                )
                for row in cursor.fetchall()
            ]

    estimated = order["estimated_delivery_date"]
    eta_days = max((estimated - date.today()).days, 0) if estimated else order["eta_days"]
    has_tracking = any(
        order[field] is not None
        for field in ("courier_name", "tracking_number", "shipment_status")
    )
    tracking = TrackingDetails(
        courier_name=order["courier_name"],
        tracking_number=order["tracking_number"],
        shipment_status=order["shipment_status"],
        shipped_at=order["shipped_at"],
        delivered_at=order["delivered_at"],
    ) if has_tracking else None
    return OrderStatusResponse(
        order_id=order["order_id"],
        order_status=order["order_status"],
        payment_status=order["payment_status"],
        tracking=tracking,
        estimated_delivery_date=estimated,
        eta_days=eta_days,
        status_history=history,
    )
