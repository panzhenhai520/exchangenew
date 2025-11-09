-- =====================================================
-- AMLO/BOT合规系统 - 权限初始化脚本
-- 版本: v1.0
-- 创建日期: 2025-10-02
-- 说明: 添加AMLO/BOT模块所需的7个新权限
-- =====================================================

-- 1. 插入新权限到permissions表
INSERT INTO permissions (permission_name, description, created_at) VALUES
('amlo_reservation_view', 'AMLO预约查看 - 查看AMLO预约记录列表', NOW()),
('amlo_reservation_audit', 'AMLO预约审核 - 审核和反审核AMLO预约记录', NOW()),
('amlo_report_view', 'AMLO报告查看 - 查看AMLO报告列表', NOW()),
('amlo_report_submit', 'AMLO报告上报 - 批量上报AMLO报告到监管机构', NOW()),
('bot_report_view', 'BOT报告查看 - 查看BOT报表数据', NOW()),
('bot_report_export', 'BOT报告导出 - 导出BOT报表为Excel文件', NOW()),
('compliance_config', '合规配置管理 - 管理报告字段定义和触发规则', NOW());

-- 2. 为admin角色分配所有新权限
-- 假设admin角色的role_id为1（根据实际情况调整）
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT 1, p.id, NOW()
FROM permissions p
WHERE p.permission_name IN (
    'amlo_reservation_view',
    'amlo_reservation_audit',
    'amlo_report_view',
    'amlo_report_submit',
    'bot_report_view',
    'bot_report_export',
    'compliance_config'
)
AND NOT EXISTS (
    SELECT 1 FROM role_permissions rp
    WHERE rp.role_id = 1 AND rp.permission_id = p.id
);

-- 3. 为supervisor角色分配查看和导出权限（假设supervisor角色的role_id为2）
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT 2, p.id, NOW()
FROM permissions p
WHERE p.permission_name IN (
    'amlo_reservation_view',
    'amlo_reservation_audit',
    'amlo_report_view',
    'bot_report_view',
    'bot_report_export'
)
AND NOT EXISTS (
    SELECT 1 FROM role_permissions rp
    WHERE rp.role_id = 2 AND rp.permission_id = p.id
);

-- 4. 为operator角色分配基本查看权限（假设operator角色的role_id为3）
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT 3, p.id, NOW()
FROM permissions p
WHERE p.permission_name IN (
    'amlo_reservation_view',
    'amlo_report_view',
    'bot_report_view'
)
AND NOT EXISTS (
    SELECT 1 FROM role_permissions rp
    WHERE rp.role_id = 3 AND rp.permission_id = p.id
);

-- 5. 验证权限是否正确插入
SELECT '=== 新增权限验证 ===' as message;
SELECT
    p.id,
    p.permission_name,
    p.description,
    COUNT(rp.role_id) as role_count
FROM permissions p
LEFT JOIN role_permissions rp ON p.id = rp.permission_id
WHERE p.permission_name IN (
    'amlo_reservation_view',
    'amlo_reservation_audit',
    'amlo_report_view',
    'amlo_report_submit',
    'bot_report_view',
    'bot_report_export',
    'compliance_config'
)
GROUP BY p.id, p.permission_name, p.description
ORDER BY p.permission_name;

-- 6. 查看角色权限分配情况
SELECT '=== 角色权限分配情况 ===' as message;
SELECT
    r.id as role_id,
    r.role_name,
    COUNT(rp.permission_id) as permission_count,
    GROUP_CONCAT(p.permission_name SEPARATOR ', ') as permissions
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON rp.permission_id = p.id
WHERE p.permission_name IN (
    'amlo_reservation_view',
    'amlo_reservation_audit',
    'amlo_report_view',
    'amlo_report_submit',
    'bot_report_view',
    'bot_report_export',
    'compliance_config'
)
GROUP BY r.id, r.role_name
ORDER BY r.id;
