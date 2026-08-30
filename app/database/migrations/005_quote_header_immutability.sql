BEGIN;

CREATE OR REPLACE FUNCTION protect_quote_snapshot()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'quote snapshots cannot be deleted';
    END IF;

    IF OLD.merchant_id IS DISTINCT FROM NEW.merchant_id
       OR OLD.subtotal IS DISTINCT FROM NEW.subtotal
       OR OLD.discount_amount IS DISTINCT FROM NEW.discount_amount
       OR OLD.taxable_amount IS DISTINCT FROM NEW.taxable_amount
       OR OLD.tax_amount IS DISTINCT FROM NEW.tax_amount
       OR OLD.shipping_amount IS DISTINCT FROM NEW.shipping_amount
       OR OLD.total_amount IS DISTINCT FROM NEW.total_amount
       OR OLD.currency IS DISTINCT FROM NEW.currency
       OR OLD.shipping_state IS DISTINCT FROM NEW.shipping_state
       OR OLD.shipping_country IS DISTINCT FROM NEW.shipping_country
       OR OLD.shipping_type IS DISTINCT FROM NEW.shipping_type
       OR OLD.created_at IS DISTINCT FROM NEW.created_at
       OR OLD.expires_at IS DISTINCT FROM NEW.expires_at
       OR OLD.pricing_explanation IS DISTINCT FROM NEW.pricing_explanation THEN
        RAISE EXCEPTION 'quote financial snapshots are immutable';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS quotes_snapshot_immutable ON quotes;
CREATE TRIGGER quotes_snapshot_immutable
BEFORE UPDATE OR DELETE ON quotes
FOR EACH ROW EXECUTE FUNCTION protect_quote_snapshot();

COMMIT;
