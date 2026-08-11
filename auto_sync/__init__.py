#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动同步模块
提供JSON文件自动同步到FTP服务器的功能
"""

from .auto_sync_service import AutoSyncService
from .file_watcher import FileWatcher
from .event_queue import EventQueueManager, FileEvent
# [DISABLED] Python FTP removed: do not import EnhancedFTPSyncManager
# [DISABLED] Python FTP removed: do not import SyncProcessor

__version__ = "1.0.0"
__author__ = "Auto Sync System"

__all__ = [
    'AutoSyncService',
    'FileWatcher', 
    'EventQueueManager',
    'FileEvent',
    
    
]