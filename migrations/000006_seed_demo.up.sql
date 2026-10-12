-- Phase 3 Slice A: minimal demo seed (3 roles + 1 ACTIVE user).
-- Login: username=demo@opspilot.local  password=password123

INSERT INTO roles (id, code, name, description)
VALUES
    ('11111111-1111-1111-1111-111111111101', 'EMPLOYEE', 'Employee', 'Regular employee'),
    ('11111111-1111-1111-1111-111111111102', 'IT_SUPPORT', 'IT Support', 'IT support staff'),
    ('11111111-1111-1111-1111-111111111103', 'ADMIN', 'Admin', 'System administrator')
ON CONFLICT (code) DO NOTHING;

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
    '22222222-2222-2222-2222-222222222201',
    'Demo Employee',
    'demo@opspilot.local',
    '$2b$10$3OvuEbwEhHIs6Y8S5kgbYOnrEVVpNFLnP./dRmHQxuVATg2k8GCVC',
    'Engineering',
    'Backend Developer',
    '11111111-1111-1111-1111-111111111101',
    'ACTIVE'
)
ON CONFLICT (email) DO NOTHING;
