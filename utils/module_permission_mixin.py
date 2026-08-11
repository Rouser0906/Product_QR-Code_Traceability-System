#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块权限控制混入类
为所有模块提供统一的权限检查功能
"""
import sqlite3
import os
from PyQt5.QtWidgets import QMessageBox

class ModulePermissionMixin:
    """模块权限控制混入类"""
    
    def __init__(self):
        # 初始化权限相关属性
        self.current_user = None
        self.current_user_roles = ['viewer']  # 默认为浏览者
        self.module_permission_prefix = ""  # 子类需要设置，如 "company", "staff", "department"
        
    def set_current_user(self, user_info):
        """设置当前用户信息（由主系统调用）"""
        self.current_user = user_info
        
    def apply_permissions(self, user_info):
        """应用权限设置（由主系统调用）"""
        self.current_user = user_info
        self._load_user_roles()
        self._apply_ui_permissions()
        
    def _load_user_roles(self):
        """加载用户角色"""
        if not self.current_user:
            self.current_user_roles = ['viewer']
            return
            
        try:
            from utils.permissions import get_user_role_names
            self.current_user_roles = get_user_role_names(self.current_user)
            if not self.current_user_roles:
                self.current_user_roles = ['viewer']
        except Exception as e:
            print(f"加载用户角色失败: {e}")
            self.current_user_roles = ['viewer']
    
    def _apply_ui_permissions(self):
        """根据权限设置UI控件状态"""
        if not hasattr(self, 'module_permission_prefix') or not self.module_permission_prefix:
            return
            
        # 检查各种权限
        can_create = self._has_permission(f'{self.module_permission_prefix}.create')
        can_update = self._has_permission(f'{self.module_permission_prefix}.update') 
        can_delete = self._has_permission(f'{self.module_permission_prefix}.delete')
        
        # 设置按钮状态
        if hasattr(self, 'addBtn'):
            self.addBtn.setEnabled(can_create)
            if not can_create:
                self.addBtn.setToolTip(f"您没有{self.module_permission_prefix}模块的新增权限")
                self.addBtn.setStyleSheet(self.addBtn.styleSheet() + "; color: gray;")
                
        if hasattr(self, 'delBtn'):
            self.delBtn.setEnabled(can_delete)
            if not can_delete:
                self.delBtn.setToolTip(f"您没有{self.module_permission_prefix}模块的删除权限")
                self.delBtn.setStyleSheet(self.delBtn.styleSheet() + "; color: gray;")
                
        if hasattr(self, 'editBtn'):
            self.editBtn.setEnabled(can_update)
            if not can_update:
                self.editBtn.setToolTip(f"您没有{self.module_permission_prefix}模块的编辑权限")
                self.editBtn.setStyleSheet(self.editBtn.styleSheet() + "; color: gray;")
    
    def _has_permission(self, permission):
        """检查当前用户是否有指定权限"""
        if not self.current_user_roles:
            return False
            
        # admin角色拥有所有权限
        if 'admin' in self.current_user_roles:
            return True
            
        try:
            # 尝试多个可能的数据库路径
            possible_paths = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'),
                os.path.join(os.path.dirname(__file__), '..', 'qr_system.db'),
                'qr_system.db'
            ]
            
            conn = None
            for db_path in possible_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    break
            
            if not conn:
                print(f"无法找到数据库文件，尝试的路径: {possible_paths}")
                return False
            cursor = conn.cursor()
            
            # 查询用户角色是否有指定权限
            for role in self.current_user_roles:
                cursor.execute("""
                    SELECT COUNT(*) FROM roles r
                    JOIN role_permissions rp ON r.id = rp.role_id
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE r.name = ? AND (p.resource || '.' || p.action) = ?
                """, (role, permission))
                
                result = cursor.fetchone()
                if result and result[0] > 0:
                    conn.close()
                    return True
            
            conn.close()
            return False
            
        except Exception as e:
            print(f"权限查询失败: {e}")
            return False
    
    def check_permission_before_action(self, permission, action_name="执行此操作"):
        """在执行操作前检查权限"""
        if not self._has_permission(permission):
            QMessageBox.critical(
                self, 
                "权限不足", 
                f"您当前的角色 ({', '.join(self.current_user_roles)}) 没有{action_name}的权限！\n\n"
                f"需要权限: {permission}"
            )
            return False
        return True
    
    def init_permissions(self, permission_prefix):
        """初始化权限前缀（子类调用）"""
        self.module_permission_prefix = permission_prefix
        # 如果有父窗口，尝试获取用户信息
        if hasattr(self, 'parent') and self.parent():
            parent = self.parent()
            while parent:
                if hasattr(parent, 'current_user') and hasattr(parent, 'current_user_roles'):
                    self.current_user = parent.current_user
                    self.current_user_roles = parent.current_user_roles
                    break
                parent = parent.parent() if hasattr(parent, 'parent') else None
        
        self._apply_ui_permissions()