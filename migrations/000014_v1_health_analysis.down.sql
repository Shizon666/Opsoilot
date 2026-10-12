ALTER TABLE tickets DROP COLUMN IF EXISTS analysis;

ALTER TABLE services
    DROP COLUMN IF EXISTS last_checked_at,
    DROP COLUMN IF EXISTS health_summary,
    DROP COLUMN IF EXISTS health_status;
