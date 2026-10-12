-- Phase 12 down: restore job_role; drop employee_level.

ALTER TABLE users
    ALTER COLUMN employee_level DROP NOT NULL,
    ALTER COLUMN employee_level DROP DEFAULT;

ALTER TABLE users DROP COLUMN IF EXISTS employee_level;

ALTER TABLE users RENAME COLUMN position TO job_role;
