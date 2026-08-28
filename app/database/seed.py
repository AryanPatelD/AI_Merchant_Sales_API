"""Seed a development merchant, catalog, inventory, and capabilities.

Run with:
    python -m app.database.seed

The seed is idempotent: stable UUIDs and UPSERT statements make repeated runs
safe without producing duplicate rows.
"""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid5

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEED_NAMESPACE = UUID("f339988c-22c6-4a84-9dfa-e148bf9f90d6")

CAPABILITIES = (
    "catalog",
    "search",
    "availability",
    "quote",
    "checkout",
    "payment",
    "order-status",
)

PRODUCTS = (
    ("TS-MOU-M1", "Wireless Mouse M1", "Ergonomic 2.4 GHz wireless optical mouse", "Computer Accessories", "TechStore", "799.00", 40, 4, 2),
    ("TS-KEY-K2", "Mechanical Keyboard K2", "Compact mechanical keyboard with red switches", "Computer Accessories", "TechStore", "2499.00", 25, 3, 2),
    ("TS-HUB-H7", "USB-C Hub H7", "Seven-port USB-C hub with HDMI and card reader", "Computer Accessories", "TechStore", "1899.00", 30, 2, 3),
    ("TS-WBC-C1", "Full HD Webcam C1", "1080p webcam with dual microphones", "Computer Accessories", "TechStore", "2199.00", 18, 2, 3),
    ("TS-HDP-P1", "Wireless Headphones P1", "Over-ear Bluetooth headphones with noise isolation", "Audio", "TechStore", "3499.00", 22, 3, 3),
    ("TS-SPK-S2", "Bluetooth Speaker S2", "Portable IPX6 Bluetooth speaker", "Audio", "TechStore", "1599.00", 35, 5, 2),
    ("TS-CHG-C65", "65W GaN Charger", "Dual USB-C fast charger with USB-A output", "Power and Charging", "TechStore", "2299.00", 28, 3, 2),
    ("TS-CBL-C2", "USB-C Cable 2m", "Braided 100W USB-C charging and data cable", "Power and Charging", "TechStore", "499.00", 60, 6, 1),
    ("TS-PWB-B10", "Power Bank 10000", "10000 mAh power bank with 20W fast charging", "Power and Charging", "TechStore", "1799.00", 32, 4, 2),
    ("TS-STD-L1", "Aluminium Laptop Stand L1", "Adjustable ventilated stand for 11-17 inch laptops", "Workspace", "TechStore", "1299.00", 20, 2, 3),
    ("TS-LMP-D1", "LED Desk Lamp D1", "Dimmable desk lamp with adjustable colour temperature", "Workspace", "TechStore", "1499.00", 16, 1, 3),
    ("TS-SSD-E1", "Portable SSD 1TB E1", "USB 3.2 portable solid-state drive", "Storage", "TechStore", "6499.00", 12, 2, 4),
)


def load_local_env() -> None:
    """Load simple KEY=VALUE entries from .env without overwriting the shell."""
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def stable_id(entity: str, natural_key: str) -> UUID:
    return uuid5(SEED_NAMESPACE, f"{entity}:{natural_key}")


def database_url() -> str:
    load_local_env()
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is not configured in .env or the environment")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def seed() -> dict[str, int]:
    load_local_env()
    merchant_id = UUID(
        os.getenv("MERCHANT_ID", "00000000-0000-0000-0000-000000000001")
    )
    merchant_name = os.getenv("MERCHANT_NAME", "TechStore")
    currency = os.getenv("MERCHANT_CURRENCY", "INR")
    country = os.getenv("MERCHANT_COUNTRY", "IN")
    api_version = os.getenv("MERCHANT_API_VERSION", "1.0")

    with psycopg.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO merchants (
                    merchant_id, merchant_name, currency, country_code,
                    api_version, status
                )
                VALUES (%s, %s, %s, %s, %s, 'ACTIVE')
                ON CONFLICT (merchant_id) DO UPDATE SET
                    merchant_name = EXCLUDED.merchant_name,
                    currency = EXCLUDED.currency,
                    country_code = EXCLUDED.country_code,
                    api_version = EXCLUDED.api_version,
                    status = 'ACTIVE',
                    updated_at = CURRENT_TIMESTAMP
                """,
                (merchant_id, merchant_name, currency, country, api_version),
            )

            for capability in CAPABILITIES:
                cursor.execute(
                    """
                    INSERT INTO merchant_capabilities (
                        capability_id, merchant_id, capability_name
                    )
                    VALUES (%s, %s, %s)
                    ON CONFLICT (merchant_id, capability_name) DO NOTHING
                    """,
                    (stable_id("capability", capability), merchant_id, capability),
                )

            for (
                sku,
                name,
                description,
                category,
                brand,
                price,
                total_quantity,
                reserved_quantity,
                eta_days,
            ) in PRODUCTS:
                product_id = stable_id("product", sku)
                cursor.execute(
                    """
                    INSERT INTO products (
                        product_id, merchant_id, sku, name, description,
                        category, brand, price, currency, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
                    ON CONFLICT (sku) DO UPDATE SET
                        merchant_id = EXCLUDED.merchant_id,
                        name = EXCLUDED.name,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        brand = EXCLUDED.brand,
                        price = EXCLUDED.price,
                        currency = EXCLUDED.currency,
                        status = 'ACTIVE',
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        product_id,
                        merchant_id,
                        sku,
                        name,
                        description,
                        category,
                        brand,
                        Decimal(price),
                        currency,
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO inventory (
                        inventory_id, product_id, total_quantity,
                        reserved_quantity, eta_days
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (product_id) DO UPDATE SET
                        total_quantity = EXCLUDED.total_quantity,
                        reserved_quantity = EXCLUDED.reserved_quantity,
                        eta_days = EXCLUDED.eta_days,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        stable_id("inventory", sku),
                        product_id,
                        total_quantity,
                        reserved_quantity,
                        eta_days,
                    ),
                )

            cursor.execute(
                "SELECT COUNT(*) FROM merchants WHERE merchant_id = %s",
                (merchant_id,),
            )
            merchant_count = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM merchant_capabilities WHERE merchant_id = %s",
                (merchant_id,),
            )
            capability_count = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM products WHERE merchant_id = %s",
                (merchant_id,),
            )
            product_count = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM inventory i
                JOIN products p ON p.product_id = i.product_id
                WHERE p.merchant_id = %s
                """,
                (merchant_id,),
            )
            inventory_count = cursor.fetchone()[0]

    return {
        "merchants": merchant_count,
        "capabilities": capability_count,
        "products": product_count,
        "inventory": inventory_count,
    }


if __name__ == "__main__":
    counts = seed()
    print("Seed completed successfully")
    for table, count in counts.items():
        print(f"{table}: {count}")
