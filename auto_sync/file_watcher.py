import os
import time
import logging
import fnmatch
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    _USE_WATCHDOG = True
except Exception:
    _USE_WATCHDOG = False
    # Minimal fallback without external dependency
    class FileSystemEventHandler:
        pass
    class Observer:
        def __init__(self):
            self._entries = []
            self._running = False
        def schedule(self, handler, directory, recursive=False):
            self._entries.append((handler, directory, recursive))
        def start(self):
            import threading, time, os
            self._running = True
            def loop():
                seen = {}
                while self._running:
                    for handler, directory, recursive in list(self._entries):
                        try:
                            for name in os.listdir(directory):
                                path = os.path.join(directory, name)
                                if os.path.isfile(path) and path not in seen:
                                    seen[path] = os.path.getmtime(path)
                                    if hasattr(handler, 'on_created'):
                                        handler.on_created(type('E', (), {'is_directory': False, 'src_path': path}))
                        except Exception:
                            pass
                    time.sleep(1.0)
            self._t = threading.Thread(target=loop, daemon=True)
            self._t.start()
        def stop(self):
            self._running = False
        def join(self):
            t = getattr(self, '_t', None)
            if t: t.join(timeout=1.0)
from typing import Optional

from .event_queue import EventQueueManager

class FileWatcher:
    """文件监控器，用于监控指定目录的文件变化"""
    def __init__(self, watch_directory: str, event_queue: EventQueueManager, file_pattern: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.watch_directory = watch_directory
        self.event_queue = event_queue
        self.file_pattern = file_pattern
        self.observer = Observer()
        self.is_running = False
        
        if not os.path.exists(self.watch_directory):
            self.logger.warning(f"监控目录不存在，将尝试创建: {self.watch_directory}")
            try:
                os.makedirs(self.watch_directory, exist_ok=True)
            except OSError as e:
                self.logger.error(f"创建监控目录失败: {self.watch_directory}, error: {e}")
                raise

    def process_existing_files(self):
        """处理监控目录中已存在的文件"""
        self.logger.info(f"扫描已存在的文件: {self.watch_directory}")
        try:
            # 快速扫描模式：只处理最新的100个文件
            all_files = []
            for filename in os.listdir(self.watch_directory):
                if self.file_pattern:
                    name_chk = filename
                    patt_chk = self.file_pattern
                    # case-insensitive match for cross-platform safety
                    if not (fnmatch.fnmatch(name_chk, patt_chk) or fnmatch.fnmatch(name_chk.lower(), patt_chk.lower())):
                        self.logger.debug(f"skip by pattern: name={filename}, pattern={self.file_pattern}")
                        continue
                
                file_path = os.path.join(self.watch_directory, filename)
                if os.path.isfile(file_path):
                    try:
                        mtime = os.path.getmtime(file_path)
                        all_files.append((file_path, mtime))
                    except OSError:
                        continue
            
            # 按修改时间排序，只处理最新的100个文件
            all_files.sort(key=lambda x: x[1], reverse=True)
            files_to_process = all_files[:100]  # 限制处理数量
            
            self.logger.debug(f"发现 {len(all_files)} 个文件，将处理最新的 {len(files_to_process)} 个")
            
            for file_path, _ in files_to_process:
                pass  # 减少输出
                try:
                    file_size = os.path.getsize(file_path)
                    # 已存在的文件设置为低优先级
                    self.event_queue.add_event(file_path, 'created', file_size, is_new_file=False)
                except OSError as e:
                    self.logger.error(f"无法获取文件大小或添加事件: {file_path}, error: {e}")
            
            # 标记启动扫描完成
            self.event_queue.mark_startup_scan_completed()
            self.logger.info(f"扫描完成: {os.path.basename(self.watch_directory)} ({len(files_to_process)} 个文件)")
        except Exception as e:
            self.logger.error(f"处理已存在文件时出错: {e}")

    def start_monitoring(self) -> None:
        """开始监控"""
        if self.is_running:
            self.logger.warning("文件监控器已在运行中")
            return
        
        event_handler = JSONFileHandler(self.event_queue, self.file_pattern)
        self.observer.schedule(event_handler, self.watch_directory, recursive=False)
        self.observer.start()
        self.is_running = True
        self.logger.info(f"开始监控目录: {self.watch_directory}")

    def stop_monitoring(self) -> None:
        """停止监控"""
        if self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            self.logger.info(f"已停止监控目录: {self.watch_directory}")

    def get_status(self) -> dict:
        """获取监控器状态"""
        return {
            'is_running': self.is_running,
            'watch_directory': self.watch_directory
        }

class JSONFileHandler(FileSystemEventHandler):
    """处理JSON文件系统事件"""
    def __init__(self, event_queue: EventQueueManager, file_pattern: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_queue = event_queue
        self.file_pattern = file_pattern

    def on_created(self, event):
        """文件创建事件处理"""
        if event.is_directory:
            return
        
        file_path = event.src_path
        
        if self.file_pattern:
            name_chk = os.path.basename(file_path)
            patt_chk = self.file_pattern
            # case-insensitive match for cross-platform safety
            if not (fnmatch.fnmatch(name_chk, patt_chk) or fnmatch.fnmatch(name_chk.lower(), patt_chk.lower())):
                self.logger.debug(f"skip by pattern (create): name={name_chk}, pattern={self.file_pattern}")
                return

        # 等待文件写入完成
        self._wait_for_file_complete(file_path)
        
        # 将文件事件加入队列
        try:
            file_size = os.path.getsize(file_path)
            # 新创建的文件设置为高优先级
            self.event_queue.add_event(file_path, 'created', file_size, is_new_file=True)
            self.logger.info(f"检测到新JSON文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"处理文件事件失败 {file_path}: {e}")
    
    def _wait_for_file_complete(self, file_path: str, max_wait: int = 10):
        """等待文件写入完成，防止读取不完整的文件"""
        self.logger.debug(f"等待文件写入完成: {file_path}")
        last_size = -1
        wait_count = 0
        while wait_count < max_wait:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == last_size:
                    self.logger.debug(f"文件大小稳定，写入完成: {file_path}")
                    return
                last_size = current_size
            except OSError:
                # 文件可能暂时不可访问
                pass
            time.sleep(0.5) # 等待0.5秒
            wait_count += 1
        self.logger.warning(f"等待文件写入超时: {file_path}")