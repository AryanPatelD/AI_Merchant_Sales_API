BEGIN;

ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_status_check CHECK (order_status IN (
    'PENDING_PAYMENT', 'PAYMENT_FAILED', 'PAID', 'CONFIRMED', 'PROCESSING',
    'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED',
    'RETURN_REQUESTED', 'RETURNED', 'REFUND_PENDING', 'REFUNDED'
));

ALTER TABLE order_status_history
    ADD COLUMN IF NOT EXISTS sequence_number BIGSERIAL;

ALTER TABLE order_status_history
    ALTER COLUMN changed_at TYPE TIMESTAMPTZ
        USING changed_at AT TIME ZONE current_setting('TIMEZONE');

ALTER TABLE shipments
    ALTER COLUMN shipped_at TYPE TIMESTAMPTZ
        USING shipped_at AT TIME ZONE current_setting('TIMEZONE'),
    ALTER COLUMN delivered_at TYPE TIMESTAMPTZ
        USING delivered_at AT TIME ZONE current_setting('TIMEZONE');

CREATE INDEX IF NOT EXISTS order_status_history_order_changed_idx
    ON order_status_history (order_id, sequence_number);
CREATE INDEX IF NOT EXISTS shipments_order_idx ON shipments (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS api_clients_api_key_hash_unique
    ON api_clients (api_key_hash);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS response_status SMALLINT;
CREATE INDEX IF NOT EXISTS audit_logs_request_id_idx ON audit_logs (request_id);

CREATE OR REPLACE FUNCTION record_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR NEW.order_status IS DISTINCT FROM OLD.order_status THEN
        INSERT INTO order_status_history (
            history_id, order_id, previous_status, new_status, changed_at
        ) VALUES (
            gen_random_uuid(), NEW.order_id,
            CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE OLD.order_status END,
            NEW.order_status, CURRENT_TIMESTAMP
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS orders_status_history_trigger ON orders;
CREATE TRIGGER orders_status_history_trigger
AFTER INSERT OR UPDATE OF order_status ON orders
FOR EACH ROW EXECUTE FUNCTION record_order_status_change();

INSERT INTO order_status_history (
    history_id, order_id, previous_status, new_status, changed_at
)
SELECT gen_random_uuid(), o.order_id, NULL, o.order_status, o.created_at
FROM orders AS o
WHERE NOT EXISTS (
    SELECT 1 FROM order_status_history AS h WHERE h.order_id = o.order_id
);

COMMIT;
