#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧急启动脚本 - 绕过所有可能的问题
"""
import sys
import os
import traceback

def emergency_start():
    print("=== 紧急启动模式 ===")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        
        print("PyQt5 启动成功")
        
        # 直接导入并运行原始的欢迎窗口，不做任何修改
        try:
            # 备份原始的模块
            import welcome
            import main_system
            
            print("模块导入成功")
            
            # 创建欢迎窗口
            welcome_window = welcome.WelcomeWindow()
            welcome_window.show()
            
            print("欢迎窗口显示成功")
            
            # 运行应用
            sys.exit(app.exec_())
            
        except Exception as e:
            print(f"启动失败: {e}")
            traceback.print_exc()
            
            # 显示错误对话框
            error_msg = f"启动失败:\n{str(e)}\n\n详细错误:\n{traceback.format_exc()}"
            QMessageBox.critical(None, "启动错误", error_msg)
            
    except Exception as e:
        print(f"致命错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    emergency_start()