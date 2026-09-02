"""Razorpay payment and webhook routes."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.schemas.discovery import ErrorResponse
from app.schemas.payment import PaymentRequest, PaymentResponse, WebhookResponse
from app.services.idempotency import IdempotencyConflictError, run_idempotent
from app.services.payment import (
    MerchantOrderNotFoundError,
    MerchantOrderStatusError,
    PaymentConfigurationError,
    RazorpayGatewayError,
    WebhookPayloadError,
    WebhookSignatureError,
    create_payment,
    process_webhook,
)

router = APIRouter(prefix="/payment", tags=["Payments"])
webhook_router = APIRouter(prefix="/webhooks", tags=["Payment Webhooks"])


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_502_BAD_GATEWAY: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Create a Razorpay payment order",
)
def payment_order(
    request: PaymentRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key", min_length=1, max_length=255),
    settings: Settings = Depends(get_settings),
) -> PaymentResponse:
    try:
        return run_idempotent(
            idempotency_key,
            "/api/v1/payment",
            PaymentResponse,
            lambda: create_payment(settings, request.order_id),
        )
    except IdempotencyConflictError as error:
        raise HTTPException(409, "Idempotency key is already in use") from error
    except PaymentConfigurationError as error:
        raise HTTPException(503, "Razorpay credentials are not configured") from error
    except MerchantOrderNotFoundError as error:
        raise HTTPException(404, "Merchant order was not found") from error
    except MerchantOrderStatusError as error:
        raise HTTPException(
            409, f"Payment cannot be created for order status {error.status}"
        ) from error
    except RazorpayGatewayError as error:
        raise HTTPException(502, "Razorpay order creation failed") from error


@webhook_router.post(
    "/razorpay",
    response_model=WebhookResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
    summary="Receive a verified Razorpay webhook",
)
async def razorpay_webhook(
    request: Request,
    signature: str = Header(..., alias="X-Razorpay-Signature", min_length=1),
    event_id: str = Header(
        ..., alias="X-Razorpay-Event-Id", min_length=1, max_length=150
    ),
    settings: Settings = Depends(get_settings),
) -> WebhookResponse:
    raw_body = await request.body()
    try:
        return process_webhook(settings, raw_body, signature, event_id)
    except PaymentConfigurationError as error:
        raise HTTPException(503, "Razorpay webhook secret is not configured") from error
    except WebhookSignatureError as error:
        raise HTTPException(401, "Invalid Razorpay webhook signature") from error
    except WebhookPayloadError as error:
        raise HTTPException(400, "Invalid Razorpay webhook payload") from error
