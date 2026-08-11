#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置工具 - 兼容EXE和源码环境
解决打包后数据库路径问题
"""

import os
import sys
from utils.logger import log_info, log_warning, log_error

def get_database_path():
    """
    获取数据库文件路径，兼容EXE和源码环境
    
    Returns:
        str: 数据库文件的完整路径
    """
    try:
        if getattr(sys, 'frozen', False):
            # EXE环境：数据库应该在可执行文件同目录或临时解压目录
            if hasattr(sys, '_MEIPASS'):
                # PyInstaller临时目录中的数据库
                db_path = os.path.join(sys._MEIPASS, 'qr_system.db')
                log_info(f"EXE环境 - 尝试临时目录数据库: {db_path}", module="数据库配置")
                if os.path.exists(db_path):
                    log_info(f"找到临时目录数据库: {db_path}", module="数据库配置")
                    return db_path
            
            # EXE文件同目录中的数据库
            exe_dir = os.path.dirname(sys.executable)
            db_path = os.path.join(exe_dir, 'qr_system.db')
            log_info(f"EXE环境 - 尝试可执行文件目录: {db_path}", module="数据库配置")
            if os.path.exists(db_path):
                log_info(f"找到可执行文件目录数据库: {db_path}", module="数据库配置")
                return db_path
                
            # 当前工作目录中的数据库
            cwd_db = os.path.join(os.getcwd(), 'qr_system.db')
            log_info(f"EXE环境 - 尝试当前工作目录: {cwd_db}", module="数据库配置")
            if os.path.exists(cwd_db):
                log_info(f"找到工作目录数据库: {cwd_db}", module="数据库配置")
                return cwd_db
        else:
            # 源码环境：数据库在项目根目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            db_path = os.path.join(project_root, 'qr_system.db')
            log_info(f"源码环境 - 项目根目录: {db_path}", module="数据库配置")
            if os.path.exists(db_path):
                log_info(f"找到项目数据库: {db_path}", module="数据库配置")
                return db_path
        
        # 最后尝试：查找所有可能的位置
        possible_paths = [
            os.path.join(os.getcwd(), 'qr_system.db'),
            os.path.join(os.path.dirname(sys.argv[0]), 'qr_system.db'),
            'qr_system.db'  # 相对路径
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                log_info(f"在备选位置找到数据库: {path}", module="数据库配置")
                return os.path.abspath(path)
        
        # 如果都找不到，返回默认路径并记录警告
        default_path = os.path.join(os.getcwd(), 'qr_system.db')
        log_warning(f"未找到数据库文件，使用默认路径: {default_path}", module="数据库配置")
        return default_path
        
    except Exception as e:
        log_error(f"获取数据库路径时发生异常: {e}", module="数据库配置")
        # 异常情况下返回默认路径
        return os.path.join(os.getcwd(), 'qr_system.db')

def verify_database_connection(db_path):
    """
    验证数据库连接和表结构
    
    Args:
        db_path (str): 数据库文件路径
        
    Returns:
        bool: 数据库是否可用
    """
    try:
        import sqlite3
        
        if not os.path.exists(db_path):
            log_error(f"数据库文件不存在: {db_path}", module="数据库验证")
            return False
        
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor = conn.cursor()
            
            # 检查关键表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='companies';")
            if not cursor.fetchone():
                log_error("数据库中缺少companies表", module="数据库验证")
                return False
            
            # 检查公司数据
            cursor.execute("SELECT COUNT(*) FROM companies")
            company_count = cursor.fetchone()[0]
            log_info(f"数据库验证成功，公司数据: {company_count} 条", module="数据库验证")
            
            return True
            
    except Exception as e:
        log_error(f"数据库验证失败: {e}", module="数据库验证")
        return False

# 全局变量缓存数据库路径
_cached_db_path = None

def get_verified_database_path():
    """
    获取经过验证的数据库路径（带缓存）
    
    Returns:
        str: 验证可用的数据库路径
    """
    global _cached_db_path
    
    if _cached_db_path is None:
        db_path = get_database_path()
        if verify_database_connection(db_path):
            _cached_db_path = db_path
            log_info(f"数据库路径已验证并缓存: {_cached_db_path}", module="数据库配置")
        else:
            log_error(f"数据库验证失败: {db_path}", module="数据库配置")
            _cached_db_path = db_path  # 即使验证失败也缓存，避免重复检查
    
    return _cached_db_path

# 向后兼容的别名
DB_PATH = None

def get_db_path():
    """向后兼容的函数名"""
    return get_verified_database_path()

# 延迟初始化DB_PATH
def _init_db_path():
    global DB_PATH
    if DB_PATH is None:
        DB_PATH = get_verified_database_path()
    return DB_PATH

# 为了向后兼容，提供一个属性访问器
class _DBPathProxy:
    def __str__(self):
        return _init_db_path()
    
    def __repr__(self):
        return f"DB_PATH('{_init_db_path()}')"

# 创建代理对象
db_path_proxy = _DBPathProxy()