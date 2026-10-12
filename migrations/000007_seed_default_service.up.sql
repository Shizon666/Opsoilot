-- Phase 4: default IT service so ticket create can satisfy service_id NOT NULL.
INSERT INTO services (id, code, name, description, category, status)
VALUES (
    '33333333-3333-3333-3333-333333333301',
    'GENERAL_IT',
    'General IT Support',
    'Default IT service for MVP ticket creation',
    'IT',
    'ACTIVE'
)
ON CONFLICT (code) DO NOTHING;
