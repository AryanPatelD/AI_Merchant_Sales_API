BEGIN;

ALTER TABLE customers
    ADD COLUMN IF NOT EXISTS merchant_id UUID REFERENCES merchants(merchant_id);

CREATE UNIQUE INDEX IF NOT EXISTS customers_merchant_email_unique
    ON customers (merchant_id, LOWER(email))
    WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS customers_merchant_phone_index
    ON customers (merchant_id, phone)
    WHERE phone IS NOT NULL;

ALTER TABLE order_items
    ADD COLUMN IF NOT EXISTS line_subtotal NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS gst_rate_snapshot NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS tax_amount NUMERIC(12,2);

ALTER TABLE orders
    ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE current_setting('TIMEZONE'),
    ALTER COLUMN updated_at TYPE TIMESTAMPTZ
        USING updated_at AT TIME ZONE current_setting('TIMEZONE');

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'orders_status_check'
    ) THEN
        ALTER TABLE orders ADD CONSTRAINT orders_status_check
            CHECK (order_status IN (
                'PENDING_PAYMENT', 'PAID', 'PROCESSING', 'SHIPPED',
                'DELIVERED', 'CANCELLED', 'PAYMENT_FAILED'
            ));
    END IF;
END $$;

COMMIT;
