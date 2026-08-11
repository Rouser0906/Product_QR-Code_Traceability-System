#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限UI辅助工具
根据用户权限动态控制界面元素的显示和启用状态
"""

from PyQt5.QtWidgets import QWidget, QPushButton, QAction, QMenu, QTabWidget
from PyQt5.QtCore import Qt
from utils.permissions import has_permission

class PermissionUIHelper:
    """权限UI辅助类，用于根据权限动态控制UI元素"""
    
    def __init__(self, current_user):
        """
        初始化权限UI辅助器
        
        Args:
            current_user (dict): 当前用户信息，包含username, employee_id等
        """
        self.current_user = current_user
    
    def check_permission(self, permission):
        """检查当前用户是否具有指定权限"""
        return has_permission(self.current_user, permission)
    
    def setup_button_permissions(self, button_permissions_map):
        """
        根据权限配置批量设置按钮状态
        
        Args:
            button_permissions_map (dict): 按钮和权限的映射关系
                格式: {button_widget: permission_string, ...}
        
        Example:
            helper.setup_button_permissions({
                self.btn_create: 'qr.generate',
                self.btn_delete: 'qr.delete',
                self.btn_download: 'qr.download'
            })
        """
        for button, permission in button_permissions_map.items():
            if isinstance(button, (QPushButton, QAction)):
                has_perm = self.check_permission(permission)
                button.setEnabled(has_perm)
                
                # 为按钮添加权限提示
                if hasattr(button, 'setToolTip'):
                    current_tip = button.toolTip()
                    if not has_perm:
                        tip = f"{current_tip}\n⚠️ 需要权限: {permission}" if current_tip else f"⚠️ 需要权限: {permission}"
                        button.setToolTip(tip)
    
    def setup_menu_permissions(self, menu_permissions_map):
        """
        根据权限配置菜单项的可见性
        
        Args:
            menu_permissions_map (dict): 菜单项和权限的映射关系
                格式: {menu_action: permission_string, ...}
        """
        for action, permission in menu_permissions_map.items():
            if isinstance(action, QAction):
                has_perm = self.check_permission(permission)
                action.setVisible(has_perm)
    
    def setup_tab_permissions(self, tab_permissions_map):
        """
        根据权限配置标签页的可见性
        
        Args:
            tab_permissions_map (dict): 标签页和权限的映射关系
                格式: {(tab_widget, tab_index): permission_string, ...}
        """
        for (tab_widget, tab_index), permission in tab_permissions_map.items():
            if isinstance(tab_widget, QTabWidget):
                has_perm = self.check_permission(permission)
                tab_widget.setTabEnabled(tab_index, has_perm)
                
                # 为禁用的标签页添加权限提示
                if not has_perm:
                    current_text = tab_widget.tabText(tab_index)
                    if "🔒" not in current_text:
                        tab_widget.setTabText(tab_index, f"🔒 {current_text}")
                        tab_widget.setTabToolTip(tab_index, f"需要权限: {permission}")
    
    def setup_widget_permissions(self, widget_permissions_map):
        """
        根据权限配置组件的启用状态
        
        Args:
            widget_permissions_map (dict): 组件和权限的映射关系
                格式: {widget: permission_string, ...}
        """
        for widget, permission in widget_permissions_map.items():
            if isinstance(widget, QWidget):
                has_perm = self.check_permission(permission)
                widget.setEnabled(has_perm)
                
                # 为禁用的组件添加样式提示
                if not has_perm:
                    widget.setStyleSheet(widget.styleSheet() + "\nQWidget:disabled { background-color: #f5f5f5; }")
    
    def get_permission_summary(self):
        """
        获取当前用户的权限摘要信息
        
        Returns:
            dict: 权限摘要信息
        """
        from utils.permissions import get_user_permissions, get_user_role_names
        
        try:
            roles = get_user_role_names(self.current_user)
            permissions = get_user_permissions(self.current_user)
            
            # 统计权限类型
            permission_stats = {}
            for perm in permissions:
                if '.' in perm:
                    resource = perm.split('.')[0]
                    permission_stats[resource] = permission_stats.get(resource, 0) + 1
                elif perm == '*':
                    permission_stats['全局权限'] = 1
            
            return {
                'username': self.current_user.get('username', 'Unknown'),
                'roles': roles,
                'total_permissions': len(permissions),
                'permission_breakdown': permission_stats,
                'is_admin': '*' in permissions or 'admin' in roles
            }
        except Exception as e:
            return {
                'username': self.current_user.get('username', 'Unknown'),
                'error': str(e)
            }
    
    def create_permission_status_text(self):
        """
        创建权限状态文本，用于状态栏显示
        
        Returns:
            str: 权限状态文本
        """
        summary = self.get_permission_summary()
        
        if 'error' in summary:
            return f"用户: {summary['username']} | 权限加载失败"
        
        username = summary['username']
        roles = ', '.join(summary['roles']) if summary['roles'] else '无角色'
        total_perms = summary['total_permissions']
        
        if summary['is_admin']:
            return f"用户: {username} | 角色: {roles} | 超级管理员 (全部权限)"
        else:
            return f"用户: {username} | 角色: {roles} | 权限数: {total_perms}"

def create_permission_decorator(permission_required):
    """
    创建权限装饰器，用于装饰需要权限检查的方法
    
    Args:
        permission_required (str): 需要的权限
    
    Returns:
        function: 装饰器函数
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if hasattr(self, 'current_user') and has_permission(self.current_user, permission_required):
                return func(self, *args, **kwargs)
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    getattr(self, 'window', None) or self,
                    "权限不足",
                    f"执行此操作需要权限: {permission_required}\n请联系管理员获取相应权限。"
                )
                return None
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator

# 常用权限常量
class Permissions:
    """权限常量定义"""
    
    # 二维码相关权限
    QR_VIEW = 'qr.view'
    QR_GENERATE = 'qr.generate'
    QR_DELETE = 'qr.delete'
    QR_DOWNLOAD = 'qr.download'
    QR_PRINT = 'qr.print'
    
    # 二维码历史权限
    QR_HISTORY_VIEW = 'qr_history.view'
    QR_HISTORY_DELETE = 'qr_history.delete'
    QR_HISTORY_DOWNLOAD = 'qr_history.download'
    QR_HISTORY_PRINT = 'qr_history.print'
    
    # 公司管理权限
    COMPANY_VIEW = 'company.view'
    COMPANY_CREATE = 'company.create'
    COMPANY_UPDATE = 'company.update'
    COMPANY_DELETE = 'company.delete'
    
    # 员工管理权限
    STAFF_VIEW = 'staff.view'
    STAFF_CREATE = 'staff.create'
    STAFF_UPDATE = 'staff.update'
    STAFF_DELETE = 'staff.delete'
    
    # 物流管理权限
    LOGISTICS_VIEW = 'logistics.view'
    LOGISTICS_CREATE = 'logistics.create'
    LOGISTICS_UPDATE = 'logistics.update'
    LOGISTICS_DELETE = 'logistics.delete'
    
    # 用户管理权限
    USERS_VIEW = 'users.view'
    USERS_CREATE = 'users.create'
    USERS_UPDATE = 'users.update'
    USERS_DELETE = 'users.delete'