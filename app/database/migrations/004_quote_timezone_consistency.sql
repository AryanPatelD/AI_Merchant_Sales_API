BEGIN;

ALTER TABLE quotes
    ALTER COLUMN created_at TYPE TIMESTAMPTZ
        USING created_at AT TIME ZONE current_setting('TIMEZONE'),
    ALTER COLUMN expires_at TYPE TIMESTAMPTZ
        USING expires_at AT TIME ZONE current_setting('TIMEZONE');

COMMIT;
