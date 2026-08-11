#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全启动脚本 - 用于调试和修复登录闪退问题
"""
import sys
import os
import traceback

def safe_start():
    """安全启动系统"""
    print("=== 安全启动模式 ===")
    
    try:
        # 设置路径
        sys.path.insert(0, os.path.abspath('.'))
        
        # 导入必要模块
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        
        # 创建应用程序
        app = QApplication(sys.argv)
        
        try:
            # 测试欢迎窗口
            print("正在加载欢迎窗口...")
            from welcome import WelcomeWindow
            
            # 创建自定义的欢迎窗口，带错误处理
            class SafeWelcomeWindow(WelcomeWindow):
                def loginAndEnterSystem(self):
                    """安全的登录方法"""
                    try:
                        print("开始登录过程...")
                        
                        # 获取输入
                        username = self.usernameEdit.text().strip()
                        employee_id = self.employeeIdEdit.text().strip()
                        password = self.passwordEdit.text()
                        
                        if not username or not password:
                            QMessageBox.warning(self, "登录失败", "请输入用户名和密码")
                            return
                        
                        # 验证登录
                        from utils.auth import auth_manager
                        result = auth_manager.authenticate_user(username, password)
                        
                        if result['success']:
                            print("登录验证成功，准备进入主系统...")
                            
                            self.current_user = {
                                'username': username, 
                                'user_id': result['user_id'], 
                                'employee_id': employee_id or username
                            }
                            
                            # 安全地进入系统
                            self.safe_enter_system()
                        else:
                            QMessageBox.warning(self, "登录失败", result.get('error', '用户名或密码错误'))
                            
                    except Exception as e:
                        print(f"登录过程出错: {e}")
                        traceback.print_exc()
                        QMessageBox.critical(self, "登录错误", f"登录过程中发生错误：{str(e)}")
                
                def safe_enter_system(self):
                    """安全地进入主系统"""
                    try:
                        print("正在创建主系统窗口...")
                        
                        # 导入主系统
                        from main_system import MainSystemWindow
                        
                        # 创建主系统窗口
                        self.mainWin = MainSystemWindow(current_user=self.current_user)
                        
                        print("主系统窗口创建成功，正在显示...")
                        
                        # 显示主窗口
                        self.mainWin.showMaximized()
                        
                        print("正在关闭欢迎窗口...")
                        
                        # 关闭欢迎窗口
                        self.close()
                        
                        print("系统启动完成！")
                        
                    except Exception as e:
                        print(f"进入主系统时出错: {e}")
                        traceback.print_exc()
                        QMessageBox.critical(self, "系统错误", f"进入主系统时发生错误：{str(e)}")
            
            # 创建并显示安全欢迎窗口
            welcome = SafeWelcomeWindow()
            welcome.show()
            
            print("欢迎窗口已显示，等待用户操作...")
            
            # 运行应用程序
            sys.exit(app.exec_())
            
        except Exception as e:
            print(f"启动过程中出错: {e}")
            traceback.print_exc()
            
            # 显示错误对话框
            if 'app' in locals():
                QMessageBox.critical(None, "启动错误", f"系统启动失败：{str(e)}")
            
    except Exception as e:
        print(f"致命错误: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    safe_start()