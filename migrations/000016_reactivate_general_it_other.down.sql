-- Revert GENERAL_IT to INACTIVE (V1 catalog catch-all disabled).
UPDATE services
SET
    status = 'INACTIVE',
    name = 'General IT Support',
    description = 'Default IT service for MVP ticket creation',
    category = 'IT',
    health_status = 'HEALTHY',
    health_summary = '目录停用，禁止作为建单默认',
    last_checked_at = TIMESTAMPTZ '2026-10-03 12:00:00+00',
    updated_at = NOW()
WHERE id = '33333333-3333-3333-3333-333333333301'
   OR code = 'GENERAL_IT';
