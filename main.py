#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口
启动欢迎窗口和自动同步服务
"""

import sys
import os
import threading
import logging
# 运行时路径修复，确保 EXE/源码环境均可稳定导入
try:
    from utils.runtime_paths import ensure_runtime_paths
    ensure_runtime_paths(chdir=False)  # EXE环境不要改变工作目录
except Exception as e:
    # 如果utils导入失败，手动添加路径
    import sys
    import os
    if getattr(sys, 'frozen', False):
        # PyInstaller环境，添加_MEIPASS路径
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        for subdir in ['modules', 'utils', '']:
            path = os.path.join(base_dir, subdir)
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
# 延迟导入qrcode/PIL到实际使用的模块，减少启动开销
# 显式导入打印支持以确保PyInstaller收集该子模块（轻量，保留）
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPageSetupDialog
# 延迟导入二维码依赖，由业务模块自行导入，降低启动耗时
from PIL import Image
from welcome import WelcomeWindow

# 🔧 修复：恢复自动同步服务功能
AUTO_SYNC_AVAILABLE = True

# 自动同步服务相关变量
auto_sync_service = None
auto_sync_thread = None
ps_uploader_proc = None


def _resolve_path_in_bundle(*parts):
    """在EXE与源码环境下统一解析资源路径"""
    base = None
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base, *parts)


def start_ps_uploader(interval_seconds: int = 15):
    """启动后台PowerShell JSON自动上传器（HS/ZY）"""
    global ps_uploader_proc
    try:
        script_rel = os.path.join('scripts', 'windows_ftp_json_uploader.ps1')
        # 在可执行环境中，脚本位于 _MEIPASS/scripts；在源码环境中为项目根的 scripts
        if getattr(sys, 'frozen', False):
            script_path = _resolve_path_in_bundle('scripts', 'windows_ftp_json_uploader.ps1')
            # 运行时工作目录切换到可执行所在目录，使本地cloud路径可用
            work_dir = os.path.dirname(sys.executable)
        else:
            # 源码模式：scripts 相对项目根
            project_root = os.path.abspath(os.path.dirname(__file__))
            script_path = os.path.join(os.path.dirname(project_root), script_rel) if not os.path.exists(script_rel) else script_rel
            work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
        if not os.path.exists(script_path):
            print(f"⚠️ 未找到上传脚本: {script_path}")
            return
        # 隐藏窗口启动PowerShell
        creationflags = 0
        try:
            import subprocess
            CREATE_NO_WINDOW = 0x08000000
            creationflags = CREATE_NO_WINDOW
        except Exception:
            pass
        cmd = [
            'powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass',
            '-File', script_path,
            '-IntervalSeconds', str(interval_seconds)
        ]
        ps_uploader_proc = subprocess.Popen(
            cmd,
            cwd=work_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )
        print(f"🚀 已启动后台上传器(PowerShell)，PID={ps_uploader_proc.pid}, 每{interval_seconds}s扫描一次")
    except Exception as e:
        print(f"⚠️ 启动后台上传器失败: {e}")


def stop_ps_uploader():
    """停止后台PowerShell上传器"""
    global ps_uploader_proc
    try:
        if ps_uploader_proc and ps_uploader_proc.poll() is None:
            ps_uploader_proc.terminate()
            # 给一点时间结束
            try:
                ps_uploader_proc.wait(timeout=3)
            except Exception:
                pass
            print("✅ 已停止后台上传器")
        ps_uploader_proc = None
    except Exception as e:
        print(f"⚠️ 停止后台上传器失败: {e}")

def start_auto_sync_service():
    """启动自动同步服务（监控cloud/demo_json_a与cloud/demo_json_b），并启用后台上传器"""
    global auto_sync_service, auto_sync_thread
    try:
        from auto_sync.auto_sync_service import AutoSyncService
        auto_sync_service = AutoSyncService()
        
        def run_sync_service():
            try:
                print("🚀 正在启动自动同步服务...")
                if auto_sync_service.start_service():
                    print("✅ 自动同步服务启动成功")
                    print("📁 监控目录: cloud/demo_json_a/ 和 cloud/demo_json_b/")
                    print("📤 目标服务器: C:\\inetpub\\qr-system\\companies\\")
                else:
                    print("❌ 自动同步服务启动失败")
            except Exception as e:
                print(f"❌ 自动同步服务启动异常: {e}")
        
        auto_sync_thread = threading.Thread(target=run_sync_service, daemon=True)
        auto_sync_thread.start()
        
        # 优先使用 Python 内置直传（AutoSyncService），仅当需要时再启用PowerShell上传器
        # start_ps_uploader(interval_seconds=10)
        
    except ImportError as e:
        print(f"⚠️ 自动同步模块未找到: {e}")
        print("💡 将使用计划任务模式进行文件同步")
        start_ps_uploader(interval_seconds=10)
    except Exception as e:
        print(f"⚠️ 自动同步服务启动异常: {e}")
        start_ps_uploader(interval_seconds=10)

def stop_auto_sync_service():
    """停止自动同步服务，并停止后台上传器"""
    global auto_sync_service
    try:
        if auto_sync_service:
            print("🛑 正在停止自动同步服务...")
            auto_sync_service.stop_service()
            auto_sync_service = None
            print("✅ 自动同步服务已停止")
    except Exception as e:
        print(f"⚠️ 停止自动同步服务时出错: {e}")
    finally:
        stop_ps_uploader()

def main():
    # 创建应用程序
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("二维码管理系统")
    app.setApplicationVersion("1.0")
    
    # 设置高DPI支持
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 🔧 修复：启动自动同步服务
    if AUTO_SYNC_AVAILABLE:
        # 延迟启动同步服务，优先展示UI，减少冷启动时间
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(200, start_auto_sync_service)
    
    # 创建并显示欢迎窗口
    welcome = WelcomeWindow()
    welcome.show()
    
    try:
        # 运行应用程序
        result = app.exec_()
    finally:
        # 应用程序退出时停止自动同步服务
        stop_auto_sync_service()
    
    sys.exit(result)

if __name__ == "__main__":
    main()