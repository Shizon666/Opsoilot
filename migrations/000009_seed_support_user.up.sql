-- Phase 4: minimal IT_SUPPORT seed for ticket workflow acceptance.
-- Login: username=support@opspilot.local  password=password123

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
    '22222222-2222-2222-2222-222222222203',
    'Demo IT Support',
    'support@opspilot.local',
    '$2b$10$3OvuEbwEhHIs6Y8S5kgbYOnrEVVpNFLnP./dRmHQxuVATg2k8GCVC',
    'IT',
    'IT Support Engineer',
    '11111111-1111-1111-1111-111111111102',
    'ACTIVE'
)
ON CONFLICT (email) DO NOTHING;
