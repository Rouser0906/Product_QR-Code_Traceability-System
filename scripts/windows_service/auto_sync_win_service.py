# Windows Service wrapper for AutoSyncService using pywin32
# Requires: pip install pywin32
import win32serviceutil
import win32service
import win32event
import servicemanager
import logging
import os
import sys
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from auto_sync.auto_sync_service import AutoSyncService

class AutoSyncWinService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'QRJsonAutoSync'
    _svc_display_name_ = 'QR JSON Auto Sync Service'
    _svc_description_ = 'Uploads newly generated QR JSON files to the cloud FTP server.'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.svc_run = True
        # Change to project root directory
        os.chdir(project_root)
        os.makedirs('auto_sync/logs', exist_ok=True)
        
        # 配置日志但不立即创建AutoSyncService
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join('auto_sync','logs','auto_sync_win_service.log'), encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('auto_sync.win_service')
        self.service = None  # 延迟初始化

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.svc_run = False
        try:
            self.service.stop_service()
        except Exception:
            pass
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogInfoMsg('QRJsonAutoSync service starting...')
        try:
            # 立即报告服务已启动，避免超时
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            
            self.logger.info('Starting AutoSyncService...')
            # 使用更快的启动方式
            self.service = AutoSyncService()
            
            # 异步启动自动同步服务
            import threading
            def start_service():
                try:
                    if self.service.start_service():
                        self.logger.info('AutoSyncService started successfully.')
                    else:
                        self.logger.error('Failed to start AutoSyncService.')
                except Exception as e:
                    self.logger.exception('Error starting AutoSyncService: %s', e)
            
            # 在后台线程中启动服务
            start_thread = threading.Thread(target=start_service)
            start_thread.daemon = True
            start_thread.start()
            
            self.logger.info('Service main loop started.')
            
            # 主循环
            while self.svc_run:
                # 等待停止事件或超时
                rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    break
                    
                # 健康检查
                try:
                    if hasattr(self.service, 'is_running') and not self.service.is_running:
                        self.logger.warning('AutoSyncService stopped unexpectedly, attempting restart...')
                        start_thread = threading.Thread(target=start_service)
                        start_thread.daemon = True
                        start_thread.start()
                except Exception as e:
                    self.logger.exception('Health check error: %s', e)
                    
        except Exception as e:
            self.logger.exception('Service crashed: %s', e)
            servicemanager.LogErrorMsg('QRJsonAutoSync service crashed: %s' % str(e))
        finally:
            try:
                if hasattr(self, 'service'):
                    self.service.stop_service()
            except Exception as e:
                self.logger.exception('Error stopping service: %s', e)
            self.logger.info('Service stopped.')
            servicemanager.LogInfoMsg('QRJsonAutoSync service stopped.')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        # Allow running in console for debug
        s = AutoSyncWinService(sys.argv)
        s.SvcDoRun()
    else:
        win32serviceutil.HandleCommandLine(AutoSyncWinService)
