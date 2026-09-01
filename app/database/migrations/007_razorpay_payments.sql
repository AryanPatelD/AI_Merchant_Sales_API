BEGIN;

ALTER TABLE payments
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ADD COLUMN IF NOT EXISTS refund_status VARCHAR(30);

ALTER TABLE payments
    ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE current_setting('TIMEZONE'),
    ALTER COLUMN paid_at TYPE TIMESTAMPTZ
        USING paid_at AT TIME ZONE current_setting('TIMEZONE');

ALTER TABLE payment_webhook_events
    ALTER COLUMN received_at TYPE TIMESTAMPTZ
        USING received_at AT TIME ZONE current_setting('TIMEZONE'),
    ALTER COLUMN processed_at TYPE TIMESTAMPTZ
        USING processed_at AT TIME ZONE current_setting('TIMEZONE');

CREATE UNIQUE INDEX IF NOT EXISTS payments_order_gateway_unique
    ON payments (order_id, payment_gateway);

CREATE UNIQUE INDEX IF NOT EXISTS payments_gateway_order_unique
    ON payments (gateway_order_id)
    WHERE gateway_order_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS payments_gateway_payment_unique
    ON payments (gateway_payment_id)
    WHERE gateway_payment_id IS NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'payments_status_check'
    ) THEN
        ALTER TABLE payments ADD CONSTRAINT payments_status_check
            CHECK (payment_status IN (
                'CREATED', 'PENDING', 'AUTHORIZED', 'CAPTURED', 'FAILED', 'REFUNDED'
            ));
    END IF;
END $$;

COMMIT;
