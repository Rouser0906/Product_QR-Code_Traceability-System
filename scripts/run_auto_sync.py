# -*- coding: utf-8 -*-
"""
守护运行 AutoSyncService：
- 独立于 pywin32，无需 Windows 服务即可常驻
- 供计划任务（开机触发/系统帐户）后台运行
"""
import os
import sys
import time
import traceback

# 项目根目录：scripts 的上级
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
os.chdir(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

# 确保日志目录存在
os.makedirs(os.path.join('auto_sync', 'logs'), exist_ok=True)

from auto_sync.auto_sync_service import AutoSyncService


def main():
    while True:
        svc = None
        try:
            print('[run_auto_sync] starting AutoSyncService at', time.strftime('%Y-%m-%d %H:%M:%S'))
            svc = AutoSyncService()
            if svc.start_service():
                print('[run_auto_sync] service started, entering keep-alive loop')
                while getattr(svc, 'is_running', False):
                    time.sleep(2)
                print('[run_auto_sync] service stopped (is_running=False), restart in 5s')
                time.sleep(5)
            else:
                print('[run_auto_sync] start_service returned False, retry in 5s')
                time.sleep(5)
        except KeyboardInterrupt:
            if svc:
                try:
                    svc.stop_service()
                except Exception:
                    pass
            break
        except Exception:
            traceback.print_exc()
            # 防止重启风暴
            time.sleep(5)


if __name__ == '__main__':
    main()
