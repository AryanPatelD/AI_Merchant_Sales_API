BEGIN;

ALTER TABLE merchants
    ADD COLUMN IF NOT EXISTS origin_state VARCHAR(100);

UPDATE merchants
SET origin_state = 'Gujarat'
WHERE origin_state IS NULL;

ALTER TABLE merchants
    ALTER COLUMN origin_state SET NOT NULL;

ALTER TABLE products
    ADD COLUMN IF NOT EXISTS gst_rate DECIMAL(5,2);

UPDATE products
SET gst_rate = CASE
    WHEN LOWER(category) = 'books' THEN 5.00
    WHEN LOWER(category) = 'clothing' THEN 12.00
    ELSE 18.00
END
WHERE gst_rate IS NULL;

ALTER TABLE products
    ALTER COLUMN gst_rate SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'products_gst_rate_check'
    ) THEN
        ALTER TABLE products
            ADD CONSTRAINT products_gst_rate_check
            CHECK (gst_rate >= 0 AND gst_rate <= 100);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS merchant_shipping_rules (
    shipping_rule_id UUID PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id),
    shipping_type VARCHAR(30) NOT NULL,
    free_shipping_threshold DECIMAL(12,2),
    base_charge DECIMAL(12,2) NOT NULL,
    additional_item_charge DECIMAL(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (merchant_id, shipping_type),
    CHECK (shipping_type IN ('SAME_STATE', 'INTER_STATE', 'INTERNATIONAL')),
    CHECK (free_shipping_threshold IS NULL OR free_shipping_threshold >= 0),
    CHECK (base_charge >= 0),
    CHECK (additional_item_charge >= 0)
);

COMMIT;
