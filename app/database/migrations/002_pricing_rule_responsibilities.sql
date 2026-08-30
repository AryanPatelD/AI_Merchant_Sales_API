BEGIN;

CREATE TABLE IF NOT EXISTS tax_rules (
    tax_rule_id UUID PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id),
    category VARCHAR(150) NOT NULL,
    tax_name VARCHAR(50) NOT NULL DEFAULT 'GST',
    tax_rate NUMERIC(5,2) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'IN',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (merchant_id, category, tax_name, country),
    CHECK (tax_rate >= 0 AND tax_rate <= 100)
);

CREATE TABLE IF NOT EXISTS discount_rules (
    discount_rule_id UUID PRIMARY KEY,
    merchant_id UUID NOT NULL REFERENCES merchants(merchant_id),
    rule_name VARCHAR(100) NOT NULL,
    min_subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
    max_subtotal NUMERIC(12,2),
    discount_type VARCHAR(20) NOT NULL,
    discount_value NUMERIC(12,2) NOT NULL,
    max_discount_amount NUMERIC(12,2),
    priority INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (merchant_id, rule_name),
    CHECK (discount_type IN ('PERCENTAGE', 'FIXED')),
    CHECK (discount_value >= 0),
    CHECK (max_discount_amount IS NULL OR max_discount_amount >= 0),
    CHECK (max_subtotal IS NULL OR max_subtotal >= min_subtotal)
);

-- GST ownership now belongs to category rules rather than product rows.
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_gst_rate_check;
ALTER TABLE products DROP COLUMN IF EXISTS gst_rate;

COMMIT;
