import json
import os
import sqlite3
from functools import lru_cache
from typing import Dict, List

# 数据库路径 - 兼容EXE环境
from utils.database_config import get_verified_database_path
DB_PATH = get_verified_database_path()

def get_user_permissions(user: Dict) -> List[str]:
    """从数据库获取用户的所有权限"""
    if not user:
        return []
    
    # admin用户拥有所有权限
    if user.get("username") == "admin" or user.get("employee_id") == "admin":
        return ["*"]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 查询用户的所有权限
        cursor.execute("""
            SELECT DISTINCT p.resource, p.action
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE u.username = ? OR (u.staff_id IN (
                SELECT id FROM staff WHERE employee_id = ?
            ))
        """, (user.get("username", ""), user.get("employee_id", "")))
        
        permissions = cursor.fetchall()
        conn.close()
        
        # 转换为 "resource.action" 格式
        return [f"{perm[0]}.{perm[1]}" for perm in permissions]
        
    except Exception as e:
        print(f"获取用户权限失败: {e}")
        return []

def get_role_permissions(role: str) -> List[str]:
    """从数据库获取角色权限（向后兼容）"""
    if role == "admin":
        return ["*"]
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.resource, p.action
            FROM roles r
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = ?
        """, (role,))
        
        permissions = cursor.fetchall()
        conn.close()
        
        return [f"{perm[0]}.{perm[1]}" for perm in permissions]
        
    except Exception as e:
        print(f"获取角色权限失败: {e}")
        return []

def match_permission(granted: str, required: str) -> bool:
    if granted == "*" or required == "*":
        return True
    if granted == required:
        return True
    # 通配符支持：资源或操作的星号
    if "*" in granted:
        g_parts = granted.split(".")
        r_parts = required.split(".")
        # 资源级别通配符
        if len(g_parts) == 2 and g_parts[1] == "*" and len(r_parts) == 2:
            return g_parts[0] == r_parts[0]
        # 完全星号
        if granted == "*":
            return True
    return False

def has_permission(user: Dict, permission: str) -> bool:
    """
    检查用户是否拥有指定权限
    user: { 'username': str, 'employee_id': str, 'user_id': int }
    permission: 'resource.action' (如: 'qr.generate', 'company.view')
    - admin 用户名或工号为 'admin' 时，直接放行
    """
    if not user:
        return False
    
    # admin用户拥有所有权限
    if (user.get("username") == "admin") or (user.get("employee_id") == "admin"):
        return True
    
    # 从数据库获取用户的实际权限
    user_permissions = get_user_permissions(user)
    
    # 检查权限匹配
    for granted_perm in user_permissions:
        if match_permission(granted_perm, permission):
            return True
    
    return False

def check_permission_with_message(user: Dict, permission: str, action_name: str = "执行此操作") -> bool:
    """
    检查权限并显示友好的错误消息
    返回True表示有权限，False表示无权限
    """
    if has_permission(user, permission):
        return True
    
    # 显示权限不足的消息
    from PyQt5.QtWidgets import QMessageBox
    QMessageBox.warning(None, "权限不足", f"您没有{action_name}的权限。\n需要权限: {permission}")
    return False

def get_user_role_names(user: Dict) -> List[str]:
    """获取用户的角色名称列表"""
    if not user:
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT r.name
            FROM users u
            JOIN user_roles ur ON u.id = ur.user_id
            JOIN roles r ON ur.role_id = r.id
            WHERE u.username = ? OR (u.staff_id IN (
                SELECT id FROM staff WHERE employee_id = ?
            ))
        """, (user.get("username", ""), user.get("employee_id", "")))
        
        roles = cursor.fetchall()
        conn.close()
        
        return [role[0] for role in roles]
        
    except Exception as e:
        print(f"获取用户角色失败: {e}")
        return []