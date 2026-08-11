#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统恢复脚本 - 撤销所有权限修改，恢复到原始状态
"""
import os
import shutil

def restore_original_modules():
    """恢复原始模块，移除权限控制"""
    print("=== 恢复原始系统状态 ===")
    
    modules_to_restore = [
        'modules/company_module.py',
        'modules/staff_module.py',
        'modules/department_module.py',
        'modules/user_permission_module.py',
        'modules/logistics_module.py'
    ]
    
    for module_path in modules_to_restore:
        if os.path.exists(module_path):
            print(f"正在恢复: {module_path}")
            
            # 读取文件内容
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 移除权限相关的修改
            lines = content.split('\n')
            cleaned_lines = []
            
            skip_next = False
            for line in lines:
                # 跳过权限相关的导入和代码
                if any(keyword in line for keyword in [
                    'ModulePermissionMixin',
                    'check_permission_before_action',
                    '🔒 权限检查',
                    'init_permissions',
                    'from utils.module_permission_mixin'
                ]):
                    continue
                
                # 跳过权限检查的 if 语句块
                if 'if not self.check_permission_before_action' in line:
                    skip_next = True
                    continue
                
                if skip_next and 'return' in line.strip():
                    skip_next = False
                    continue
                
                if skip_next:
                    continue
                
                # 恢复类继承
                if ', ModulePermissionMixin' in line:
                    line = line.replace(', ModulePermissionMixin', '')
                
                # 恢复初始化
                if 'ModulePermissionMixin.__init__(self)' in line:
                    continue
                
                cleaned_lines.append(line)
            
            # 写回文件
            with open(module_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(cleaned_lines))
            
            print(f"  ✅ {module_path} 已恢复")
    
    # 删除权限混入文件
    permission_mixin_file = 'utils/module_permission_mixin.py'
    if os.path.exists(permission_mixin_file):
        os.remove(permission_mixin_file)
        print(f"  ✅ 已删除 {permission_mixin_file}")
    
    print("\n=== 系统恢复完成 ===")
    print("现在可以尝试运行 python main.py 启动系统")

if __name__ == "__main__":
    restore_original_modules()