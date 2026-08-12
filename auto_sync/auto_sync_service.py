#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动同步服务主类
集成文件监控、事件队列和同步处理
"""

import os
import json
import time
import logging
import threading
from typing import Dict, Optional, List
from pathlib import Path

# Python FTP is disabled. Only FileWatcher/EventQueue can be used if needed.
try:
    from .file_watcher import FileWatcher
    from .event_queue import EventQueueManager
except ImportError:
    from auto_sync.file_watcher import FileWatcher
    from auto_sync.event_queue import EventQueueManager

import ftplib
from dataclasses import dataclass

class EnhancedFTPSyncManager:
    def __init__(self, host: str, port: int = 21, username: str = '', password: str = '', use_tls: bool = False, timeout: int = 15):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.timeout = timeout
        self.ftp = None
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self):
        self.close()
        if self.use_tls:
            self.ftp = ftplib.FTP_TLS()
            self.ftp.connect(self.host, self.port, timeout=self.timeout)
            self.ftp.login(self.username, self.password)
            try:
                self.ftp.prot_p()
            except Exception:
                pass
        else:
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port, timeout=self.timeout)
            self.ftp.login(self.username, self.password)
        self.ftp.set_pasv(True)
        self.logger.info(f"FTP connected: {self.host}:{self.port}")

    def close(self):
        try:
            if self.ftp:
                try:
                    self.ftp.quit()
                except Exception:
                    self.ftp.close()
        finally:
            self.ftp = None

    def ensure_dir(self, remote_dir: str):
        # remote_dir like /companies/demo_json_a/
        segments = [seg for seg in remote_dir.replace('\\','/').split('/') if seg]
        path = ''
        for seg in segments:
            path += '/' + seg
            try:
                self.ftp.mkd(path)
            except Exception:
                # exists
                pass

    def upload_single_file(self, local_path: str, remote_dir: str) -> bool:
        if not self.ftp:
            self.connect()
        self.ensure_dir(remote_dir)
        remote_path = remote_dir.rstrip('/') + '/' + os.path.basename(local_path)
        with open(local_path, 'rb') as f:
            self.ftp.storbinary(f'STOR {remote_path}', f)
        self.logger.info(f"Uploaded: {local_path} -> {remote_path}")
        return True

@dataclass
class SyncTaskConfig:
    monitor_directory: str
    file_pattern: str
    remote_directory: str

class SyncProcessor(threading.Thread):
    def __init__(self, event_queue: EventQueueManager, ftp_manager: EnhancedFTPSyncManager, task_cfg: SyncTaskConfig, daemon: bool = True):
        super().__init__(daemon=daemon)
        self.event_queue = event_queue
        self.ftp_manager = ftp_manager
        self.task_cfg = task_cfg
        self._running = True
        self.logger = logging.getLogger(self.__class__.__name__)

    def stop_processing(self):
        self._running = False

    def run(self):
        # lazy connect
        while self._running:
            try:
                ev = self.event_queue.get_next_event(timeout=0.5)
                if not ev:
                    continue
                try:
                    # double-check file exists and non-empty
                    if not os.path.exists(ev.file_path) or os.path.getsize(ev.file_path) == 0:
                        raise Exception('file missing or empty')
                    self.ftp_manager.upload_single_file(ev.file_path, self.task_cfg.remote_directory)
                    self.event_queue.mark_event_completed(ev)
                except Exception as ex:
                    self.logger.error(f"upload failed: {ev.file_path} -> {self.task_cfg.remote_directory}: {ex}")
                    self.event_queue.mark_event_failed(ev, str(ex))
                    # reconnect next time
                    try:
                        self.ftp_manager.close()
                    except Exception:
                        pass
            except Exception:
                # swallow loop errors
                pass

class AutoSyncService:
    """自动同步服务主类"""
    
    def __init__(self, tasks_config_path: str = "auto_sync/config.json", ftp_config_path: str = "config/ftp_config.json"):
        # 支持拆分配置：任务配置 + FTP配置
        self.tasks_config_path = tasks_config_path
        self.ftp_config_path = ftp_config_path
        self.config = {}
        self.is_running = False
        
        # 核心组件
        self.file_watchers: List[FileWatcher] = []
        self.event_queue_manager: Optional[EventQueueManager] = None
        self.ftp_manager: Optional[object] = None  # [DISABLED] Python FTP removed
        self.sync_processors: List[object] = []  # [DISABLED] Removed Python FTP processors
        
        # 监控线程
        self.monitor_thread: Optional[threading.Thread] = None
        
        # 日志设置
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 加载配置
        self.load_config()
    
    def setup_logging(self) -> None:
        """设置日志系统 - 优化版本"""
        # Use a unified log directory so service and console runs write to the same place
        # frozen-safe: 冻结版取 exe 同级目录，源码版取项目根；建父目录
        import sys as _sys
        if getattr(_sys, "frozen", False):
            _base = Path(_sys.executable).parent
        else:
            _base = Path(__file__).resolve().parent.parent
        log_dir = _base / "auto_sync" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置文件日志 - 保留详细信息
        file_handler = logging.FileHandler(log_dir / 'auto_sync.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # 配置控制台日志 - 只显示摘要信息
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)  # 只显示错误到控制台
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器并添加新的
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    def load_config(self) -> bool:
        """加载配置文件（拆分：auto_sync/config.json + config/ftp_config.json）"""
        try:
            if not os.path.exists(self.tasks_config_path):
                self.logger.error(f"任务配置文件不存在: {self.tasks_config_path}")
                return False
            if not os.path.exists(self.ftp_config_path):
                self.logger.error(f"FTP配置文件不存在: {self.ftp_config_path}")
                return False
            
            with open(self.tasks_config_path, 'r', encoding='utf-8') as f:
                tasks_config = json.load(f)
            with open(self.ftp_config_path, 'r', encoding='utf-8') as f:
                ftp_servers = json.load(f)
            
            # 兼容 ftp_config.json 的结构，将其映射到通用结构
            # 期望结构：{'ftp_server': {host, port, username, password, use_tls}, 'sync_tasks': [...], 'auto_sync': {...}}
            ftp_server = {
                'host': next(iter(ftp_servers.values())).get('host'),
                'port': next(iter(ftp_servers.values())).get('port', 21),
                'username': next(iter(ftp_servers.values())).get('user') or next(iter(ftp_servers.values())).get('username'),
                'password': next(iter(ftp_servers.values())).get('pass') or next(iter(ftp_servers.values())).get('password'),
                'use_tls': next(iter(ftp_servers.values())).get('tls', False)
            }
            
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            def resolve_local_dir(t):
                raw = t.get('local_path') or t.get('monitor_directory')
                # 支持 ${APP_ROOT} 占位符，用于绿色便携部署
                app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                if raw and isinstance(raw, str):
                    raw = raw.replace('${APP_ROOT}', app_root)
                if raw and os.path.isabs(raw) and os.path.exists(raw):
                    return raw
                company = (t.get('company') or '').lower()
                # 新目录规范：cloud/demo_json_a 与 cloud/demo_json_b
                if company in ('company_a','a'):
                    cand = os.path.join(app_root, 'cloud', 'demo_json_a')
                    if os.path.exists(cand):
                        return cand
                if company in ('company_b','b'):
                    cand = os.path.join(app_root, 'cloud', 'demo_json_b')
                    if os.path.exists(cand):
                        return cand
                if raw:
                    cand = raw
                    if not os.path.isabs(cand):
                        cand = os.path.join(app_root, cand)
                    return cand
                return os.path.join(app_root, 'cloud')

            def resolve_remote_dir(t):
                # 读取任务配置中的 remote_path；如缺失，按照公司归属回退到生产规范路径（/companies/...）
                rp = t.get('remote_path') or ''
                if isinstance(rp, str) and rp.strip():
                    rp = rp.replace('\\', '/')
                    if not rp.startswith('/'):
                        rp = '/' + rp
                    if not rp.endswith('/'):
                        rp += '/'
                    return rp
                company = (t.get('company') or '').lower()
                if company in ('company_a','a'):
                    return '/companies/demo_json_a/'
                if company in ('company_b','b'):
                    return '/companies/demo_json_b/'
                # 默认安全回退到 A 目录
                return '/companies/demo_json_a/'

            self.config = {
                'ftp_server': ftp_server,
                'sync_tasks': [
                    {
                        'monitor_directory': resolve_local_dir(t),
                        'file_pattern': t.get('file_pattern', '*.json'),
                        'remote_directory': resolve_remote_dir(t),
                        'enabled': t.get('enabled', True)
                    }
                    for t in tasks_config.get('sync_tasks', []) if t.get('enabled', True)
                ],
                'auto_sync': tasks_config.get('auto_sync', {'enabled': True})
            }
            
            # 校验
            required_sections = ['ftp_server', 'sync_tasks', 'auto_sync']
            for section in required_sections:
                if section not in self.config:
                    self.logger.error(f"配置文件缺少必要部分: {section}")
                    return False
            
            self.logger.info("配置文件加载成功（拆分配置模式）")
            return True
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return False
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        self.logger.info("重新加载配置文件...")
        
        if self.load_config():
            if self.is_running:
                self.logger.info("配置已更新，重启服务以应用新配置")
                self.stop_service()
                time.sleep(2)
                self.start_service()
            return True
        
        return False
    
    def start_service(self) -> bool:
        """启动同步服务"""
        if self.is_running:
            self.logger.warning("服务已经在运行中")
            return True

        if not self.config:
            self.logger.error("配置未加载，无法启动服务")
            return False

        self.logger.info("正在启动自动同步服务...")

        try:
            self.event_queue_manager = EventQueueManager()

            # 初始化 Python 直传 FTP 管理器
            ftp_cfg = self.config.get('ftp_server', {})
            self.ftp_manager = EnhancedFTPSyncManager(
                host=ftp_cfg.get('host'),
                port=int(ftp_cfg.get('port', 21) or 21),
                username=ftp_cfg.get('username') or ftp_cfg.get('user') or '',
                password=ftp_cfg.get('password') or ftp_cfg.get('pass') or '',
                use_tls=bool(ftp_cfg.get('use_tls') or ftp_cfg.get('tls') or False)
            )

            sync_tasks = self.config.get('sync_tasks', [])
            if not sync_tasks:
                self.logger.warning("配置文件中没有找到 'sync_tasks' 或任务列表为空，服务将启动但无任何监控任务。")
                self.is_running = True
                return True

            for task in sync_tasks:
                monitor_dir = task['monitor_directory']
                file_pattern = task.get('file_pattern', '*.json')
                remote_dir = task['remote_directory']

                # 独立事件队列 + 文件监控 + 处理线程
                task_event_queue = EventQueueManager()
                watcher = FileWatcher(monitor_dir, task_event_queue, file_pattern)
                self.file_watchers.append(watcher)

                processor = SyncProcessor(
                    event_queue=task_event_queue,
                    ftp_manager=self.ftp_manager,
                    task_cfg=SyncTaskConfig(monitor_directory=monitor_dir, file_pattern=file_pattern, remote_directory=remote_dir)
                )
                self.sync_processors.append(processor)

            # 启动处理线程
            for processor in self.sync_processors:
                processor.start()

            for watcher in self.file_watchers:
                watcher.start_monitoring()
            
            # 处理已存在的文件
            for watcher in self.file_watchers:
                watcher.process_existing_files()
            
            # 启动即全量扫描补传：将历史文件入队并异步处理
            self.logger.info("启动即全量扫描补传：已将历史文件入队，稍后将自动补传未在服务器上的文件。")
            
            self.is_running = True
            self.logger.info("自动同步服务已成功启动")
            return True

        except Exception as e:
            self.logger.critical(f"服务启动过程中发生严重错误: {e}", exc_info=True)
            # 在启动失败时，确保能正确清理资源
            self.stop_service() 
            # 将is_running明确设置为False
            self.is_running = False 
            return False

    def stop_service(self) -> None:
        """停止同步服务"""
        self.logger.info("正在停止自动同步服务...")
        self.is_running = False
        
        if self.file_watchers:
            for watcher in self.file_watchers:
                try:
                    watcher.stop_monitoring()
                except Exception as e:
                    self.logger.error(f"停止文件观察器 {watcher.watch_directory} 时出错: {e}")
            self.file_watchers = []
        
        if self.sync_processors:
            for processor in self.sync_processors:
                try:
                    processor.stop_processing()
                except Exception as e:
                    self.logger.error(f"停止同步处理器时出错: {e}")
            self.sync_processors = []

        # [DISABLED] No FTP manager to disconnect
        
        self.event_queue_manager = None
        self.logger.info("自动同步服务已停止")

    def get_service_status(self) -> Dict:
        """获取服务状态"""
        if not self.is_running:
            return {'status': 'stopped', 'reason': 'Service is not running.'}

        try:
            status = {'status': 'running'}

            status['ftp_manager'] = {'status': 'disabled'}
            
            if self.event_queue_manager:
                status['event_queue'] = self.event_queue_manager.get_status()

            status['sync_processors'] = [
                p.get_status() for p in self.sync_processors
            ]
            status['file_watchers'] = [
                w.get_status() for w in self.file_watchers
            ]

            return status
        except Exception as e:
            self.logger.error(f"获取服务状态时出错: {e}")
            return {'status': 'error', 'reason': str(e)}

    def trigger_full_rescan(self) -> int:
        """启动后可手动触发一次全量扫描补传，将监控目录内历史 *.json 入队。
        返回估算的入队文件数（若无法统计则返回 -1）。"""
        try:
            if not self.file_watchers:
                self.logger.warning("trigger_full_rescan: 当前无文件观察器可供扫描。")
                return 0
            enqueued = 0
            for watcher in self.file_watchers:
                try:
                    # 尝试让 watcher 自行处理现有文件
                    if hasattr(watcher, 'process_existing_files'):
                        r = watcher.process_existing_files()
                        if isinstance(r, int):
                            enqueued += r
                except Exception as ex:
                    self.logger.error(f"trigger_full_rescan: 处理 {getattr(watcher,'watch_directory', '?')} 失败: {ex}")
            self.logger.info(f"启动即全量扫描补传已执行（手动触发），估算入队 {enqueued if enqueued>0 else 'N/A'} 个文件")
            return enqueued if enqueued>0 else -1
        except Exception as e:
            self.logger.error(f"trigger_full_rescan 执行失败: {e}")
            return -1