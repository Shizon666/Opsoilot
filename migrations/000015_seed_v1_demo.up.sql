-- Phase B V1 demo seed (does not rewrite 000001–000013).
-- Login passwords remain password123 (same bcrypt as 000006 / 000009).

UPDATE users
SET
    name = '张明',
    department = '研发部',
    position = '后端开发工程师',
    updated_at = NOW()
WHERE id = '22222222-2222-2222-2222-222222222201';

UPDATE users
SET
    name = '王运维',
    department = '运维部',
    position = 'IT Support Engineer',
    updated_at = NOW()
WHERE id = '22222222-2222-2222-2222-222222222203';

INSERT INTO users (
    id,
    name,
    email,
    password_hash,
    department,
    position,
    employee_level,
    role_id,
    status
)
VALUES (
    '22222222-2222-2222-2222-222222222204',
    '李华',
    'lihua@opspilot.local',
    '$2b$10$3OvuEbwEhHIs6Y8S5kgbYOnrEVVpNFLnP./dRmHQxuVATg2k8GCVC',
    '研发部',
    '后端开发工程师',
    'P5',
    '11111111-1111-1111-1111-111111111101',
    'ACTIVE'
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO services (
    id,
    code,
    name,
    description,
    category,
    status,
    health_status,
    health_summary,
    last_checked_at
)
VALUES
    (
        '33333333-3333-3333-3333-333333333401',
        'CHECKOUT_API',
        'Checkout API',
        '下单与支付接口',
        'PAYMENTS',
        'ACTIVE',
        'DEGRADED',
        '近 15 分钟 5xx 升高，支付超时增多',
        TIMESTAMPTZ '2026-10-03 12:00:00+00'
    ),
    (
        '33333333-3333-3333-3333-333333333402',
        'AUTH_SERVICE',
        'Auth Service',
        '登录与会话服务',
        'IDENTITY',
        'ACTIVE',
        'HEALTHY',
        '登录成功率正常',
        TIMESTAMPTZ '2026-10-03 12:00:00+00'
    ),
    (
        '33333333-3333-3333-3333-333333333403',
        'ORDER_WORKER',
        'Order Worker',
        '订单异步消费 Worker',
        'ORDERS',
        'ACTIVE',
        'DOWN',
        '消费积压，队列不再下降',
        TIMESTAMPTZ '2026-10-03 12:00:00+00'
    )
ON CONFLICT (code) DO NOTHING;

UPDATE services
SET
    status = 'INACTIVE',
    health_status = 'HEALTHY',
    health_summary = '目录停用，禁止作为建单默认',
    last_checked_at = TIMESTAMPTZ '2026-10-03 12:00:00+00',
    updated_at = NOW()
WHERE id = '33333333-3333-3333-3333-333333333301';

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
    analysis,
    resolution,
    resolved_at,
    closed_at,
    created_at,
    updated_at
)
VALUES
    (
        '44444444-4444-4444-4444-444444444501',
        'OPS-V1-2001',
        '22222222-2222-2222-2222-222222222201',
        '22222222-2222-2222-2222-222222222203',
        '33333333-3333-3333-3333-333333333401',
        'Checkout 下单间歇 502',
        '收银台提交订单 502，与支付超时同时出现。',
        'HIGH',
        'RESOLVED',
        '上游超时导致 5xx；扩容 Checkout 依赖后恢复',
        '扩容上游依赖后恢复',
        NOW() - INTERVAL '1 day',
        NULL,
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '1 day'
    ),
    (
        '44444444-4444-4444-4444-444444444502',
        'OPS-V1-2002',
        '22222222-2222-2222-2222-222222222201',
        '22222222-2222-2222-2222-222222222203',
        '33333333-3333-3333-3333-333333333402',
        '登录偶发失败',
        '部分账号登录失败，与 checkout 无关。',
        'LOW',
        'CLOSED',
        '密码重置后恢复（噪声单）',
        '引导重置密码后关闭',
        NOW() - INTERVAL '10 days',
        NOW() - INTERVAL '9 days',
        NOW() - INTERVAL '12 days',
        NOW() - INTERVAL '9 days'
    ),
    (
        '44444444-4444-4444-4444-444444444503',
        'OPS-V1-2003',
        '22222222-2222-2222-2222-222222222204',
        '22222222-2222-2222-2222-222222222203',
        '33333333-3333-3333-3333-333333333401',
        'Checkout 支付超时',
        '李华侧支付网关超时，收银台长时间无响应。',
        'HIGH',
        'RESOLVED',
        '支付网关超时；切备用通道后恢复',
        '切换支付备用通道后恢复',
        NOW() - INTERVAL '2 days',
        NULL,
        NOW() - INTERVAL '4 days',
        NOW() - INTERVAL '2 days'
    )
ON CONFLICT (ticket_no) DO NOTHING;
