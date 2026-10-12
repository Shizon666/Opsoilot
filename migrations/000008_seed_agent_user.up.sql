-- Phase 5: dedicated Agent system account for Backend API auth.
-- Login: username=agent@opspilot.local  password=agentpass123
-- Role: EMPLOYEE (existing roles only; no new permission system).

INSERT INTO users (
    id,
    name,
    email,
    password_hash,
    department,
    job_role,
    role_id,
    status
)
VALUES (
    '22222222-2222-2222-2222-222222222202',
    'OpsPilot Agent',
    'agent@opspilot.local',
    '$2b$10$fytBQDdKaxU6/JEJLfKgqOc5XzV3otGLs1KS8NZ995UNyCQ0GTX3i',
    'Platform',
    'System Agent',
    '11111111-1111-1111-1111-111111111101',
    'ACTIVE'
)
ON CONFLICT (email) DO NOTHING;
