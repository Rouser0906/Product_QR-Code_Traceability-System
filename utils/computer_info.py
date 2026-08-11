#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电脑信息获取模块
用于识别打印二维码的电脑
"""

import socket
import platform
import os
import hashlib
import subprocess
import re
from datetime import datetime

class ComputerIdentifier:
    """电脑标识器"""
    
    def __init__(self):
        self._computer_info = None
        self._computer_id = None
    
    def get_computer_name(self):
        """获取电脑名称"""
        try:
            return socket.gethostname()
        except Exception:
            return "Unknown-Computer"
    
    def get_user_name(self):
        """获取当前用户名"""
        try:
            return os.getenv('USERNAME') or os.getenv('USER') or "Unknown-User"
        except Exception:
            return "Unknown-User"
    
    def get_ip_address(self):
        """获取本机IP地址"""
        try:
            # 创建一个UDP socket来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # 连接到一个外部地址来获取本地IP
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            except Exception:
                ip = 'localhost'
            finally:
                s.close()
            return ip
        except Exception:
            return 'localhost'
    
    def get_mac_address(self):
        """获取MAC地址"""
        try:
            import uuid
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            return mac
        except Exception:
            return "Unknown-MAC"
    
    def get_system_info(self):
        """获取系统信息"""
        try:
            return {
                'system': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            }
        except Exception:
            return {
                'system': 'Unknown',
                'version': 'Unknown',
                'machine': 'Unknown',
                'processor': 'Unknown'
            }
    
    def get_computer_id(self):
        """生成唯一的电脑ID"""
        if self._computer_id is None:
            try:
                # 使用电脑名称、MAC地址和系统信息生成唯一ID
                computer_name = self.get_computer_name()
                mac_address = self.get_mac_address()
                system_info = platform.machine()
                
                # 生成唯一标识
                unique_string = f"{computer_name}_{mac_address}_{system_info}"
                computer_id = hashlib.md5(unique_string.encode()).hexdigest()[:12].upper()
                self._computer_id = f"PC-{computer_id}"
            except Exception:
                # 如果无法生成唯一ID，使用时间戳
                timestamp = datetime.now().strftime('%Y%m%d%H%M')
                self._computer_id = f"PC-{timestamp}"
        
        return self._computer_id
    
    def get_computer_description(self):
        """获取电脑描述信息"""
        computer_name = self.get_computer_name()
        user_name = self.get_user_name()
        ip_address = self.get_ip_address()
        
        return f"{computer_name} ({user_name}@{ip_address})"
    
    def get_full_computer_info(self):
        """获取完整的电脑信息"""
        if self._computer_info is None:
            self._computer_info = {
                'computer_id': self.get_computer_id(),
                'computer_name': self.get_computer_name(),
                'user_name': self.get_user_name(),
                'ip_address': self.get_ip_address(),
                'mac_address': self.get_mac_address(),
                'description': self.get_computer_description(),
                'system_info': self.get_system_info(),
                'timestamp': datetime.now().isoformat()
            }
        
        return self._computer_info
    
    def get_print_source_info(self):
        """获取打印来源信息（用于QR码数据）"""
        info = self.get_full_computer_info()
        return {
            'print_computer_id': info['computer_id'],
            'print_computer_name': info['computer_name'], 
            'print_user': info['user_name'],
            'print_ip': info['ip_address'],
            'print_source': info['description'],
            'print_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

# 全局实例
computer_identifier = ComputerIdentifier()

def get_computer_info():
    """快捷方法：获取电脑信息"""
    return computer_identifier.get_full_computer_info()

def get_print_source():
    """快捷方法：获取打印来源信息"""
    return computer_identifier.get_print_source_info()

def get_computer_id():
    """快捷方法：获取电脑ID"""
    return computer_identifier.get_computer_id()

if __name__ == "__main__":
    # 测试电脑信息获取
    print("=== 电脑信息测试 ===")
    
    info = get_computer_info()
    print("\n完整电脑信息：")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print(f"\n电脑ID: {get_computer_id()}")
    print(f"打印来源描述: {computer_identifier.get_computer_description()}")
    
    print("\n打印来源信息：")
    print_info = get_print_source()
    for key, value in print_info.items():
        print(f"  {key}: {value}")