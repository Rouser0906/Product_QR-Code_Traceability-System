-- 权限管理系统数据库结构
-- 根据需求文档创建完整的权限管理表结构

-- 创建permissions表
CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource TEXT NOT NULL COMMENT '资源名：company, department, staff, logistics, qr, qr_history, users',
    action TEXT NOT NULL COMMENT '操作名：view, create, update, delete, download, print, generate',
    description TEXT COMMENT '权限描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resource, action)
);

-- 创建role_permissions关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE,
    UNIQUE(role_id, permission_id)
);

-- 插入权限数据
INSERT OR IGNORE INTO permissions (resource, action, description) VALUES
-- 公司管理权限
('company', 'view', '查看公司信息'),
('company', 'create', '创建公司'),
('company', 'update', '编辑公司信息'),
('company', 'delete', '删除公司'),

-- 部门管理权限
('department', 'view', '查看部门信息'),
('department', 'create', '创建部门'),
('department', 'update', '编辑部门信息'),
('department', 'delete', '删除部门'),

-- 员工管理权限
('staff', 'view', '查看员工信息'),
('staff', 'create', '创建员工'),
('staff', 'update', '编辑员工信息'),
('staff', 'delete', '删除员工'),

-- 物流管理权限
('logistics', 'view', '查看物流信息'),
('logistics', 'create', '创建物流记录'),
('logistics', 'update', '编辑物流信息'),
('logistics', 'delete', '删除物流记录'),

-- 二维码权限
('qr', 'view', '查看二维码'),
('qr', 'generate', '生成二维码'),
('qr', 'delete', '删除二维码'),
('qr', 'download', '下载二维码'),
('qr', 'print', '打印二维码'),

-- 二维码历史权限
('qr_history', 'view', '查看二维码历史'),
('qr_history', 'delete', '删除二维码历史'),
('qr_history', 'download', '下载二维码历史'),
('qr_history', 'print', '打印二维码历史'),

-- 用户管理权限
('users', 'view', '查看用户信息'),
('users', 'create', '创建用户'),
('users', 'update', '编辑用户信息'),
('users', 'delete', '删除用户');

-- 清空现有角色的权限配置，重新按照需求配置
DELETE FROM role_permissions;

-- 更新roles表，清空旧的permissions字段，使用新的关联表
UPDATE roles SET permissions = NULL;

-- 重新插入角色（如果不存在）
INSERT OR IGNORE INTO roles (name, description) VALUES
('admin', '超级管理员（admin / 工号 admin），权限：系统全部权限（"*"），即任何资源任何操作'),
('operator', '系统操作员，拥有：新增(create)、编辑(update)、查询(view)、下载(download)、打印(print)；禁止：删除(delete)'),
('manager', '管理者（包括部门经理/总监/副总/总/董事/董事长），只能浏览(view) + 对生产数据的删除/下载/打印'),
('viewer', '系统浏览者，仅浏览(view)，无其他任何操作');

-- 配置admin角色权限（超级管理员拥有所有权限）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'admin';

-- 配置operator角色权限（除删除外的所有操作）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'operator'
AND p.action IN ('view', 'create', 'update', 'download', 'print', 'generate');

-- 配置manager角色权限（浏览 + 对生产数据的删除/下载/打印）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'manager'
AND (
    p.action = 'view'  -- 所有模块的浏览权限
    OR (p.resource IN ('qr', 'qr_history') AND p.action IN ('delete', 'download', 'print'))  -- 生产数据的删除/下载/打印
);

-- 配置viewer角色权限（仅浏览）
INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'viewer'
AND p.action = 'view';

-- 确保admin用户拥有admin角色
INSERT OR IGNORE INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.username = 'admin' AND r.name = 'admin';