-- Allow employees to pick "其他类型" when the issue is not one of the three ACTIVE business services.
-- GENERAL_IT remains available for explicit selection; it must not be the create-form default.
UPDATE services
SET
    status = 'ACTIVE',
    name = '其他类型',
    description = '无法归入收银台 / 登录认证 / 订单处理时的综合 IT 与办公问题（VPN、设备、软件安装等）',
    category = 'IT',
    health_status = 'HEALTHY',
    health_summary = '综合入口；非业务系统故障面',
    last_checked_at = TIMESTAMPTZ '2026-10-03 12:00:00+00',
    updated_at = NOW()
WHERE id = '33333333-3333-3333-3333-333333333301'
   OR code = 'GENERAL_IT';
