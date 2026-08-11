-- 创建测试用户数据
-- 为权限系统测试创建完整的测试用户和角色分配

-- 插入测试用户（如果不存在）
INSERT OR IGNORE INTO users (username, password_hash, full_name, staff_id) VALUES
('test_operator', 'pbkdf2:sha256:260000$test_salt$test_hash_operator', '测试操作员', 'OP001'),
('test_manager', 'pbkdf2:sha256:260000$test_salt$test_hash_manager', '测试管理者', 'MG001'),
('test_viewer', 'pbkdf2:sha256:260000$test_salt$test_hash_viewer', '测试浏览者', 'VW001');

-- 为测试用户分配角色
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE (u.username = 'test_operator' AND r.name = 'operator')
   OR (u.username = 'test_manager' AND r.name = 'manager') 
   OR (u.username = 'test_viewer' AND r.name = 'viewer');

-- 验证数据插入
SELECT 
    u.username,
    u.full_name,
    u.staff_id,
    GROUP_CONCAT(r.name) as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.username LIKE 'test_%'
GROUP BY u.id, u.username, u.full_name, u.staff_id
ORDER BY u.username;