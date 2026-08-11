#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件队列管理模块
管理文件同步事件的队列处理
"""

import time
import threading
from queue import Queue, Empty, PriorityQueue
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Set
import logging
import os

@dataclass
class FileEvent:
    """文件事件数据模型"""
    file_path: str
    event_type: str  # 'created', 'modified'
    timestamp: float
    file_size: int
    retry_count: int = 0
    status: str = 'pending'  # 'pending', 'processing', 'completed', 'failed'
    error_message: Optional[str] = None
    priority: int = field(default=1)  # 1=高优先级(新文件), 2=低优先级(旧文件)
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.timestamp > other.timestamp  # 新文件优先

class EventQueueManager:
    """事件队列管理器"""
    
    def __init__(self, max_queue_size: int = 1000):
        self.event_queue = PriorityQueue(maxsize=max_queue_size)
        self.processed_files: Set[str] = set()
        self.failed_events: Queue = Queue()
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.startup_scan_completed = False
        
        # 统计信息
        self.stats = {
            'total_events': 0,
            'processed_events': 0,
            'failed_events': 0,
            'duplicate_events': 0
        }
    
    def add_event(self, file_path: str, event_type: str, file_size: int, is_new_file: bool = False) -> bool:
        """添加文件事件到队列"""
        try:
            # 检查是否为重复事件
            if self._is_duplicate_event(file_path):
                self.stats['duplicate_events'] += 1
                self.logger.debug(f"跳过重复事件: {file_path}")
                return False
            
            # 创建文件事件
            # 设置优先级：新文件或启动扫描完成后的文件为高优先级
            priority = 1 if (is_new_file or self.startup_scan_completed) else 2
            
            event = FileEvent(
                file_path=file_path,
                event_type=event_type,
                timestamp=time.time(),
                file_size=file_size,
                priority=priority
            )
            
            # 添加到队列
            self.event_queue.put(event, timeout=5)
            
            with self.lock:
                self.stats['total_events'] += 1
            
            self.logger.info(f"添加事件到队列: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加事件失败 {file_path}: {e}")
            return False
    
    def get_next_event(self, timeout: float = 1.0) -> Optional[FileEvent]:
        """获取下一个待处理事件"""
        try:
            event = self.event_queue.get(timeout=timeout)
            event.status = 'processing'
            return event
            
        except Empty:
            return None
        except Exception as e:
            self.logger.error(f"获取事件失败: {e}")
            return None
    
    def mark_event_completed(self, event: FileEvent) -> None:
        """标记事件处理完成"""
        event.status = 'completed'
        
        with self.lock:
            self.processed_files.add(event.file_path)
            self.stats['processed_events'] += 1
        
        self.logger.info(f"事件处理完成: {event.file_path}")
    
    def mark_event_failed(self, event: FileEvent, error_message: str) -> None:
        """标记事件处理失败"""
        event.status = 'failed'
        event.error_message = error_message
        event.retry_count += 1
        
        with self.lock:
            self.stats['failed_events'] += 1
        
        # 如果重试次数未达到上限，重新加入队列
        if event.retry_count < 3:
            try:
                self.event_queue.put(event, timeout=1)
                self.logger.warning(f"事件重试 ({event.retry_count}/3): {event.file_path}")
            except:
                self.failed_events.put(event)
                self.logger.error(f"事件重试失败，加入失败队列: {event.file_path}")
        else:
            # 达到重试上限，加入失败队列
            self.failed_events.put(event)
            self.logger.error(f"事件处理最终失败: {event.file_path} - {error_message}")
    
    def _is_duplicate_event(self, file_path: str) -> bool:
        """检查是否为重复事件"""
        with self.lock:
            return file_path in self.processed_files
    
    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.event_queue.qsize()
    
    def get_failed_events_count(self) -> int:
        """获取失败事件数量"""
        return self.failed_events.qsize()
    
    def get_statistics(self) -> dict:
        """获取统计信息"""
        with self.lock:
            return {
                **self.stats,
                'queue_size': self.get_queue_size(),
                'failed_queue_size': self.get_failed_events_count(),
                'processed_files_count': len(self.processed_files)
            }
    
    def clear_processed_files(self, older_than_hours: int = 24) -> None:
        """清理已处理文件记录（避免内存泄漏）"""
        # 这里可以根据时间戳清理旧记录
        # 简化实现：当记录数超过10000时清理一半
        with self.lock:
            if len(self.processed_files) > 10000:
                # 保留最近的5000个记录
                files_list = list(self.processed_files)
                self.processed_files = set(files_list[-5000:])
                self.logger.info("清理已处理文件记录，保留最近5000个")
    
    def retry_failed_events(self) -> int:
        """重试失败的事件"""
        retry_count = 0
        
        while not self.failed_events.empty():
            try:
                failed_event = self.failed_events.get_nowait()
                failed_event.retry_count = 0  # 重置重试计数
                failed_event.status = 'pending'
                failed_event.error_message = None
                
                self.event_queue.put(failed_event, timeout=1)
                retry_count += 1
                
            except Empty:
                break
            except Exception as e:
                self.logger.error(f"重试失败事件时出错: {e}")
                break
        
        if retry_count > 0:
            self.logger.info(f"重新加入 {retry_count} 个失败事件到队列")
        
        return retry_count

    def mark_startup_scan_completed(self) -> None:
        """标记启动扫描完成"""
        self.startup_scan_completed = True
        self.logger.info("启动扫描已完成，新文件将获得高优先级")
    
    def get_status(self) -> dict:
        """获取队列状态信息"""
        return {
            'queue_size': self.get_queue_size(),
            'failed_events_count': self.get_failed_events_count(),
            'startup_scan_completed': self.startup_scan_completed,
            'statistics': self.get_statistics()
        }