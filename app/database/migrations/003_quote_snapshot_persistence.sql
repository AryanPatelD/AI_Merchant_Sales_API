BEGIN;

ALTER TABLE quotes
    ADD COLUMN IF NOT EXISTS taxable_amount DECIMAL(12,2),
    ADD COLUMN IF NOT EXISTS shipping_state VARCHAR(100),
    ADD COLUMN IF NOT EXISTS shipping_country VARCHAR(100),
    ADD COLUMN IF NOT EXISTS shipping_type VARCHAR(30),
    ADD COLUMN IF NOT EXISTS pricing_explanation JSONB NOT NULL DEFAULT '[]'::jsonb;

UPDATE quotes
SET taxable_amount = subtotal - discount_amount
WHERE taxable_amount IS NULL;

ALTER TABLE quotes ALTER COLUMN taxable_amount SET NOT NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'quote_items'
          AND column_name = 'unit_price'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'quote_items'
          AND column_name = 'unit_price_snapshot'
    ) THEN
        ALTER TABLE quote_items RENAME COLUMN unit_price TO unit_price_snapshot;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'quote_items'
          AND column_name = 'subtotal'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'quote_items'
          AND column_name = 'line_subtotal'
    ) THEN
        ALTER TABLE quote_items RENAME COLUMN subtotal TO line_subtotal;
    END IF;
END $$;

ALTER TABLE quote_items
    ADD COLUMN IF NOT EXISTS sku VARCHAR(100),
    ADD COLUMN IF NOT EXISTS product_name VARCHAR(255),
    ADD COLUMN IF NOT EXISTS gst_rate_snapshot NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS discount_type_snapshot VARCHAR(20),
    ADD COLUMN IF NOT EXISTS discount_value_snapshot NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS discount_rate_snapshot NUMERIC(5,2),
    ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS tax_amount NUMERIC(12,2),
    ADD COLUMN IF NOT EXISTS line_total NUMERIC(12,2);

UPDATE quote_items AS qi
SET sku = p.sku,
    product_name = p.name,
    gst_rate_snapshot = COALESCE(qi.gst_rate_snapshot, 0),
    discount_type_snapshot = COALESCE(qi.discount_type_snapshot, 'PERCENTAGE'),
    discount_value_snapshot = COALESCE(qi.discount_value_snapshot, 0),
    discount_amount = COALESCE(qi.discount_amount, 0),
    tax_amount = COALESCE(qi.tax_amount, 0),
    line_total = COALESCE(qi.line_total, qi.line_subtotal)
FROM products AS p
WHERE p.product_id = qi.product_id;

ALTER TABLE quote_items
    ALTER COLUMN sku SET NOT NULL,
    ALTER COLUMN product_name SET NOT NULL,
    ALTER COLUMN gst_rate_snapshot SET NOT NULL,
    ALTER COLUMN discount_type_snapshot SET NOT NULL,
    ALTER COLUMN discount_value_snapshot SET NOT NULL,
    ALTER COLUMN discount_amount SET NOT NULL,
    ALTER COLUMN tax_amount SET NOT NULL,
    ALTER COLUMN line_total SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'quotes_status_check'
    ) THEN
        ALTER TABLE quotes ADD CONSTRAINT quotes_status_check
            CHECK (status IN ('ACTIVE', 'EXPIRED', 'CONSUMED', 'CANCELLED'));
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'quotes_shipping_type_check'
    ) THEN
        ALTER TABLE quotes ADD CONSTRAINT quotes_shipping_type_check
            CHECK (shipping_type IN ('SAME_STATE', 'INTER_STATE', 'INTERNATIONAL'));
    END IF;
END $$;

CREATE OR REPLACE FUNCTION prevent_quote_item_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'quote item snapshots are immutable';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS quote_items_immutable ON quote_items;
CREATE TRIGGER quote_items_immutable
BEFORE UPDATE OR DELETE ON quote_items
FOR EACH ROW EXECUTE FUNCTION prevent_quote_item_mutation();

COMMIT;
