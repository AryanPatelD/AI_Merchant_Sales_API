"""Merchant discovery business logic."""

from dataclasses import dataclass
from uuid import UUID

from app.config import Settings
from app.database.connection import database_connection
from app.schemas.discovery import MerchantDiscoveryManifest
from app.services.capabilities import IMPLEMENTED_CAPABILITIES


class MerchantNotFoundError(Exception):
    """Raised when the configured merchant does not exist."""


class MerchantInactiveError(Exception):
    """Raised when the configured merchant is not active."""


class MerchantVersionMismatchError(Exception):
    """Raised when database and application API versions do not match."""


@dataclass(frozen=True)
class MerchantRecord:
    merchant_id: UUID
    merchant_name: str
    currency: str
    country_code: str
    api_version: str
    status: str


def get_merchant_manifest(settings: Settings) -> MerchantDiscoveryManifest:
    """Load and validate the configured merchant, then build its manifest."""
    with database_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT merchant_id, merchant_name, currency, country_code,
                       api_version, status
                FROM merchants
                WHERE merchant_id = %s
                """,
                (settings.merchant_id,),
            )
            row = cursor.fetchone()
            if row is None:
                raise MerchantNotFoundError

            merchant = MerchantRecord(**row)
            if merchant.status.upper() != "ACTIVE":
                raise MerchantInactiveError
            if merchant.api_version != settings.merchant_api_version:
                raise MerchantVersionMismatchError

            cursor.execute(
                """
                SELECT capability_name
                FROM merchant_capabilities
                WHERE merchant_id = %s
                ORDER BY capability_name
                """,
                (merchant.merchant_id,),
            )
            configured_capabilities = {
                capability["capability_name"] for capability in cursor.fetchall()
            }

    active_capabilities = sorted(
        configured_capabilities.intersection(IMPLEMENTED_CAPABILITIES)
    )
    payment_gateways = (
        sorted(settings.enabled_payment_gateways)
        if "payment" in active_capabilities
        else []
    )

    return MerchantDiscoveryManifest(
        merchant_id=merchant.merchant_id,
        merchant=merchant.merchant_name,
        api_version=merchant.api_version,
        currency=merchant.currency,
        country=merchant.country_code,
        capabilities=active_capabilities,
        payment_gateways=payment_gateways,
        api_base_url=settings.api_v1_prefix,
    )

