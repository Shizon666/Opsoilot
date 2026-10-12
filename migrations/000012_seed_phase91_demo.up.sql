-- Phase 9.1: Demo scenario seed (tickets + permission requests for Employee).
-- Reuses existing users/service from 000006–000009; does not recreate accounts.
-- Employee: demo@opspilot.local / password123 (department polished below).

UPDATE users
SET
    name = '张明',
    department = '研发部',
    job_role = '后端开发工程师'
WHERE id = '22222222-2222-2222-2222-222222222201';

INSERT INTO tickets (
    id,
    ticket_no,
    requester_id,
    assignee_id,
    service_id,
    title,
    description,
    priority,
    status,
    created_at,
    updated_at
)
VALUES
    (
        '44444444-4444-4444-4444-444444444401',
        'OPS-DEMO-1001',
        '22222222-2222-2222-2222-222222222201',
        '22222222-2222-2222-2222-222222222203',
        '33333333-3333-3333-3333-333333333301',
        'VPN 故障',
        '办公网无法连接公司 VPN，提示认证失败，影响远程办公。',
        'HIGH',
        'IN_PROGRESS',
        NOW() - INTERVAL '2 days',
        NOW() - INTERVAL '1 day'
    ),
    (
        '44444444-4444-4444-4444-444444444402',
        'OPS-DEMO-1002',
        '22222222-2222-2222-2222-222222222201',
        NULL,
        '33333333-3333-3333-3333-333333333301',
        '直播/会议设备故障',
        '3 号会议室投屏与麦克风无法使用，影响线上直播与周会。',
        'MEDIUM',
        'OPEN',
        NOW() - INTERVAL '6 hours',
        NOW() - INTERVAL '6 hours'
    )
ON CONFLICT (ticket_no) DO NOTHING;

INSERT INTO access_requests (
    id,
    requester_id,
    service_id,
    resource_type,
    resource_name,
    permission_level,
    reason,
    status,
    created_at,
    updated_at
)
VALUES
    (
        '55555555-5555-5555-5555-555555555501',
        '22222222-2222-2222-2222-222222222201',
        '33333333-3333-3333-3333-333333333301',
        'GITLAB',
        'OpsPilot',
        'DEVELOPER',
        '参与 OpsPilot 仓库开发，需要 GitLab Developer 权限。',
        'PENDING',
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '3 days'
    ),
    (
        '55555555-5555-5555-5555-555555555502',
        '22222222-2222-2222-2222-222222222201',
        '33333333-3333-3333-3333-333333333301',
        'DATABASE',
        'analytics-readonly',
        'READ',
        '查询业务报表只读库，用于周报数据分析。',
        'PENDING',
        NOW() - INTERVAL '1 day',
        NOW() - INTERVAL '1 day'
    )
ON CONFLICT (id) DO NOTHING;

INSERT INTO approvals (
    id,
    access_request_id,
    approver_id,
    status,
    comment,
    decided_at,
    created_at,
    updated_at
)
VALUES
    (
        '66666666-6666-6666-6666-666666666601',
        '55555555-5555-5555-5555-555555555501',
        NULL,
        'PENDING',
        NULL,
        NULL,
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '3 days'
    ),
    (
        '66666666-6666-6666-6666-666666666602',
        '55555555-5555-5555-5555-555555555502',
        NULL,
        'PENDING',
        NULL,
        NULL,
        NOW() - INTERVAL '1 day',
        NOW() - INTERVAL '1 day'
    )
ON CONFLICT (id) DO NOTHING;
