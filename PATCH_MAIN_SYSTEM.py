#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修补主系统 - 添加详细错误捕获
"""

def patch_main_system():
    """给主系统添加错误捕获"""
    print("正在修补主系统...")
    
    with open('main_system.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 在 __init__ 方法开头添加 try-catch
    if 'try:' not in content or 'def __init__(self' in content:
        # 找到 __init__ 方法并添加错误捕获
        lines = content.split('\n')
        new_lines = []
        in_init = False
        indent_level = 0
        
        for i, line in enumerate(lines):
            if 'def __init__(self' in line and 'MainSystemWindow' in lines[max(0, i-10):i+1]:
                new_lines.append(line)
                # 添加错误捕获
                new_lines.append('        try:')
                in_init = True
                indent_level = len(line) - len(line.lstrip()) + 4
            elif in_init and line.strip() and not line.startswith(' ' * indent_level) and line.strip() != 'try:':
                # 结束 __init__ 方法，添加 except
                new_lines.append(' ' * (indent_level - 4) + 'except Exception as e:')
                new_lines.append(' ' * (indent_level - 4) + '    print(f"MainSystemWindow初始化失败: {e}")')
                new_lines.append(' ' * (indent_level - 4) + '    import traceback')
                new_lines.append(' ' * (indent_level - 4) + '    traceback.print_exc()')
                new_lines.append(' ' * (indent_level - 4) + '    raise')
                new_lines.append(line)
                in_init = False
            else:
                if in_init and line.strip():
                    # 在 init 方法内，增加缩进
                    new_lines.append('    ' + line)
                else:
                    new_lines.append(line)
        
        # 如果还在 init 中（文件结束），添加 except
        if in_init:
            new_lines.append(' ' * (indent_level - 4) + 'except Exception as e:')
            new_lines.append(' ' * (indent_level - 4) + '    print(f"MainSystemWindow初始化失败: {e}")')
            new_lines.append(' ' * (indent_level - 4) + '    import traceback')
            new_lines.append(' ' * (indent_level - 4) + '    traceback.print_exc()')
            new_lines.append(' ' * (indent_level - 4) + '    raise')
        
        # 保存修补后的文件
        with open('main_system_patched.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ 主系统已修补，保存为 main_system_patched.py")
        return True
    else:
        print("⚠️ 主系统似乎已经有错误捕获")
        return False

if __name__ == "__main__":
    patch_main_system()