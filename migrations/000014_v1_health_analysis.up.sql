-- Phase B: simulate service health on services; ticket analysis text.
-- No metrics table, no related_ticket_id, no ticket_comments.

ALTER TABLE services
    ADD COLUMN IF NOT EXISTS health_status VARCHAR(20) NOT NULL DEFAULT 'HEALTHY',
    ADD COLUMN IF NOT EXISTS health_summary TEXT NULL,
    ADD COLUMN IF NOT EXISTS last_checked_at TIMESTAMPTZ NULL;

ALTER TABLE tickets
    ADD COLUMN IF NOT EXISTS analysis TEXT NULL;
