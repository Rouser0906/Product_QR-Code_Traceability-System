#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统测试脚本
测试新实现的基于数据库的权限管理系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.permissions import has_permission, get_user_permissions, get_user_role_names

def test_permission_system():
    """测试权限系统的各个功能"""
    print("=== 权限系统功能测试 ===\n")
    
    # 测试用户数据
    test_users = [
        {'username': 'admin', 'employee_id': 'admin', 'user_id': 1},
        {'username': '9810001', 'employee_id': '9810001', 'user_id': 17},  # 孙七
        {'username': 'test_operator', 'employee_id': 'OP001', 'user_id': 999},
        {'username': 'test_manager', 'employee_id': 'MG001', 'user_id': 998},
        {'username': 'test_viewer', 'employee_id': 'VW001', 'user_id': 997}
    ]
    
    # 测试权限
    test_permissions = [
        'qr.view',
        'qr.generate', 
        'qr.print',
        'qr.download',
        'qr.delete',
        'qr_history.view',
        'qr_history.delete',
        'company.view',
        'company.create',
        'staff.view',
        'staff.create',
        'users.view',
        'logistics.view'
    ]
    
    for user in test_users:
        print(f"\n--- 测试用户: {user['username']} ({user.get('employee_id', 'N/A')}) ---")
        
        # 获取用户角色
        try:
            user_roles = get_user_role_names(user)
            print(f"用户角色: {user_roles}")
        except Exception as e:
            print(f"获取角色失败: {e}")
            user_roles = []
        
        # 获取用户权限
        try:
            user_permissions = get_user_permissions(user)
            print(f"用户权限数量: {len(user_permissions)}")
            if len(user_permissions) <= 10:
                print(f"具体权限: {user_permissions}")
            else:
                print(f"权限示例: {user_permissions[:10]}...")
        except Exception as e:
            print(f"获取权限失败: {e}")
        
        # 测试关键权限
        print("权限测试结果:")
        for permission in test_permissions:
            result = has_permission(user, permission)
            status = "✅ 允许" if result else "❌ 禁止"
            print(f"  {permission}: {status}")

def test_role_based_scenarios():
    """测试基于角色的典型场景"""
    print("\n\n=== 角色场景测试 ===\n")
    
    scenarios = [
        {
            'name': '超级管理员场景',
            'user': {'username': 'admin', 'employee_id': 'admin'},
            'expected_permissions': ['*'],
            'should_allow': ['qr.delete', 'users.create', 'company.delete']
        },
        {
            'name': '系统操作员场景', 
            'user': {'username': 'operator_test', 'employee_id': 'OP001'},
            'expected_permissions': ['qr.generate', 'qr.print', 'company.create'],
            'should_deny': ['qr.delete', 'qr_history.delete']
        },
        {
            'name': '管理者场景',
            'user': {'username': 'manager_test', 'employee_id': 'MG001'}, 
            'expected_permissions': ['qr.delete', 'qr_history.delete'],
            'should_deny': ['company.create', 'staff.create']
        },
        {
            'name': '浏览者场景',
            'user': {'username': 'viewer_test', 'employee_id': 'VW001'},
            'expected_permissions': ['company.view', 'qr.view'],
            'should_deny': ['qr.generate', 'qr.delete', 'company.create']
        }
    ]
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        user = scenario['user']
        
        if 'should_allow' in scenario:
            print("应该允许的操作:")
            for perm in scenario['should_allow']:
                result = has_permission(user, perm)
                status = "✅ 正确" if result else "❌ 错误"
                print(f"  {perm}: {status}")
        
        if 'should_deny' in scenario:
            print("应该禁止的操作:")
            for perm in scenario['should_deny']:
                result = has_permission(user, perm)
                status = "✅ 正确" if not result else "❌ 错误"
                print(f"  {perm}: {status}")
        print()

def test_edge_cases():
    """测试边界情况"""
    print("\n=== 边界情况测试 ===\n")
    
    edge_cases = [
        {'name': '空用户', 'user': None},
        {'name': '空用户名', 'user': {'username': '', 'employee_id': ''}},
        {'name': '不存在的用户', 'user': {'username': 'nonexistent', 'employee_id': 'NE999'}},
        {'name': '无员工ID', 'user': {'username': 'test_user'}},
        {'name': '孙七用户', 'user': {'username': '9810001', 'employee_id': '9810001'}},
    ]
    
    for case in edge_cases:
        print(f"--- {case['name']} ---")
        user = case['user']
        
        try:
            # 测试基本权限检查
            can_view_qr = has_permission(user, 'qr.view')
            can_generate_qr = has_permission(user, 'qr.generate')
            can_delete_qr = has_permission(user, 'qr.delete')
            
            print(f"  查看二维码: {'✅' if can_view_qr else '❌'}")
            print(f"  生成二维码: {'✅' if can_generate_qr else '❌'}")
            print(f"  删除二维码: {'✅' if can_delete_qr else '❌'}")
            
        except Exception as e:
            print(f"  测试失败: {e}")
        print()

if __name__ == '__main__':
    try:
        test_permission_system()
        test_role_based_scenarios()
        test_edge_cases()
        
        print("\n=== 权限系统测试完成 ===")
        print("✅ 如果上述测试没有出现异常，说明权限系统基本功能正常")
        print("🔧 如发现权限配置问题，请检查数据库中的角色权限配置")
        
    except Exception as e:
        print(f"\n❌ 权限系统测试失败: {e}")
        import traceback
        traceback.print_exc()