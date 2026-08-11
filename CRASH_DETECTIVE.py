#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闪退侦探 - 找出真正的闪退原因
"""
import sys
import os
import traceback

def crash_detective():
    print("🕵️ 闪退侦探开始工作...")
    print("=" * 50)
    
    # 检查基础环境
    print(f"Python版本: {sys.version}")
    print(f"当前目录: {os.getcwd()}")
    print(f"Python路径: {sys.executable}")
    
    # 检查必需文件
    required_files = [
        'main.py',
        'welcome.py', 
        'main_system.py',
        'qr_system.db',
        'utils/auth.py',
        'utils/permissions.py'
    ]
    
    print("\n📁 检查必需文件:")
    for file in required_files:
        exists = os.path.exists(file)
        print(f"  {'✅' if exists else '❌'} {file}")
        if not exists:
            print(f"    ⚠️ 缺失关键文件!")
    
    # 测试每个导入
    imports_to_test = [
        ('PyQt5.QtWidgets', 'QApplication'),
        ('PyQt5.QtCore', 'Qt'),
        ('PyQt5.QtGui', 'QFont'),
        ('sqlite3', None),
        ('utils.auth', 'auth_manager'),
        ('utils.permissions', 'get_user_role_names'),
        ('welcome', 'WelcomeWindow'),
        ('main_system', 'MainSystemWindow')
    ]
    
    print("\n📦 测试模块导入:")
    failed_imports = []
    
    for module_name, class_name in imports_to_test:
        try:
            if class_name:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                print(f"  ✅ {module_name}.{class_name}")
            else:
                __import__(module_name)
                print(f"  ✅ {module_name}")
        except Exception as e:
            print(f"  ❌ {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    # 测试数据库
    print("\n🗄️ 测试数据库:")
    try:
        import sqlite3
        conn = sqlite3.connect('qr_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        print(f"  ✅ 数据库连接成功，表数量: {len(tables)}")
    except Exception as e:
        print(f"  ❌ 数据库错误: {e}")
        failed_imports.append(('database', str(e)))
    
    # 测试创建应用程序
    print("\n🖥️ 测试 PyQt 应用创建:")
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        print("  ✅ QApplication 创建成功")
        app.quit()
    except Exception as e:
        print(f"  ❌ QApplication 创建失败: {e}")
        failed_imports.append(('QApplication', str(e)))
    
    # 尝试最小启动
    print("\n🚀 尝试最小启动测试:")
    try:
        from PyQt5.QtWidgets import QApplication, QWidget, QLabel
        app = QApplication([])
        
        window = QWidget()
        window.setWindowTitle("测试窗口")
        label = QLabel("如果您看到这个窗口，说明 PyQt 工作正常")
        
        print("  ✅ 测试窗口创建成功")
        print("  📝 将显示测试窗口 3 秒...")
        
        window.show()
        
        # 显示 3 秒后自动关闭
        from PyQt5.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(3000)  # 3秒
        
        app.exec_()
        print("  ✅ 测试窗口运行成功")
        
    except Exception as e:
        print(f"  ❌ 测试窗口失败: {e}")
        traceback.print_exc()
        failed_imports.append(('test_window', str(e)))
    
    # 总结
    print("\n" + "=" * 50)
    print("🔍 诊断结果:")
    
    if failed_imports:
        print("❌ 发现以下问题:")
        for module, error in failed_imports:
            print(f"  • {module}: {error}")
    else:
        print("✅ 所有基础组件工作正常")
        print("🤔 问题可能在登录逻辑或窗口切换过程中")
    
    print("\n请将此诊断结果发送给技术支持!")

if __name__ == "__main__":
    crash_detective()