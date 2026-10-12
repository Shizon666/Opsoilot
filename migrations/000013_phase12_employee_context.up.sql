-- Phase 12: Employee Context (minimal).
-- Rename job_role → position; add employee_level.
-- No new profile tables.

ALTER TABLE users RENAME COLUMN job_role TO position;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS employee_level VARCHAR(50);

UPDATE users
SET employee_level = 'STANDARD'
WHERE employee_level IS NULL OR employee_level = '';

ALTER TABLE users
    ALTER COLUMN employee_level SET DEFAULT 'STANDARD',
    ALTER COLUMN employee_level SET NOT NULL;

-- Demo Employee (张明 / 研发部)
UPDATE users
SET
    employee_level = 'P5'
WHERE id = '22222222-2222-2222-2222-222222222201';

-- Support
UPDATE users
SET employee_level = 'P6'
WHERE id = '22222222-2222-2222-2222-222222222203';

-- Agent system account (legacy seed; unused for business JWT path)
UPDATE users
SET employee_level = 'SYSTEM'
WHERE id = '22222222-2222-2222-2222-222222222202';
