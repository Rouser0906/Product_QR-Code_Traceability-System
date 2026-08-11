import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import json
import traceback
from typing import Dict, Any, List

class SystemLogger:
    """系统日志管理器"""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        
        self.log_dir = log_dir
        self.ensure_log_directory()
        
        # 创建日志记录器
        self.logger = logging.getLogger('QRSystem')
        self.logger.setLevel(logging.DEBUG)
        
        # 清除现有的处理器
        self.logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # 文件处理器（按日期分割）
        log_file = os.path.join(self.log_dir, f'qr_system_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # 错误日志处理器
        error_file = os.path.join(self.log_dir, f'errors_{datetime.now().strftime("%Y%m%d")}.log')
        error_handler = logging.FileHandler(error_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # 安全日志处理器
        security_file = os.path.join(self.log_dir, f'security_{datetime.now().strftime("%Y%m%d")}.log')
        security_handler = logging.FileHandler(security_file, encoding='utf-8')
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(security_handler)
        
        # 业务操作日志
        self.business_logger = logging.getLogger('QRSystem.Business')
        business_file = os.path.join(self.log_dir, f'business_{datetime.now().strftime("%Y%m%d")}.log')
        business_handler = logging.FileHandler(business_file, encoding='utf-8')
        business_handler.setLevel(logging.INFO)
        business_handler.setFormatter(formatter)
        self.business_logger.addHandler(business_handler)
        
        # 数据库操作日志
        self.db_logger = logging.getLogger('QRSystem.Database')
        db_file = os.path.join(self.log_dir, f'database_{datetime.now().strftime("%Y%m%d")}.log')
        db_handler = logging.FileHandler(db_file, encoding='utf-8')
        db_handler.setLevel(logging.DEBUG)
        db_handler.setFormatter(formatter)
        self.db_logger.addHandler(db_handler)
    
    def ensure_log_directory(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def log_info(self, message: str, module: str = None, **kwargs):
        """记录信息日志"""
        context = self._build_context(module, **kwargs)
        self.logger.info(f"{message} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_warning(self, message: str, module: str = None, **kwargs):
        """记录警告日志"""
        context = self._build_context(module, **kwargs)
        self.logger.warning(f"{message} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_error(self, message: str, module: str = None, exception: Exception = None, **kwargs):
        """记录错误日志"""
        context = self._build_context(module, **kwargs)
        if exception:
            context['exception'] = str(exception)
            context['traceback'] = traceback.format_exc()
        self.logger.error(f"{message} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_debug(self, message: str, module: str = None, **kwargs):
        """记录调试日志"""
        context = self._build_context(module, **kwargs)
        self.logger.debug(f"{message} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_security(self, message: str, user: str = None, action: str = None, **kwargs):
        """记录安全相关日志"""
        context = self._build_context(module="SECURITY", user=user, action=action, **kwargs)
        self.logger.warning(f"SECURITY: {message} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_business(self, action: str, user: str = None, details: Dict[str, Any] = None, **kwargs):
        """记录业务操作日志"""
        context = self._build_context(module="BUSINESS", user=user, action=action, details=details, **kwargs)
        self.business_logger.info(f"BUSINESS: {action} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_database(self, operation: str, table: str = None, query: str = None, params: Dict = None, **kwargs):
        """记录数据库操作日志"""
        context = self._build_context(module="DATABASE", operation=operation, table=table, **kwargs)
        if query:
            context['query'] = query
        if params:
            context['params'] = str(params)  # 避免敏感信息泄露
        self.db_logger.debug(f"DATABASE: {operation} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_user_action(self, user: str, action: str, resource: str = None, result: str = None, **kwargs):
        """记录用户操作日志"""
        context = self._build_context(module="USER_ACTION", user=user, action=action, resource=resource, result=result, **kwargs)
        self.business_logger.info(f"USER_ACTION: {user} - {action} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def log_qr_operation(self, operation: str, qr_code: str = None, user: str = None, details: Dict[str, Any] = None, **kwargs):
        """记录二维码相关操作日志"""
        context = self._build_context(module="QR_OPERATION", operation=operation, user=user, qr_code=qr_code, details=details, **kwargs)
        self.business_logger.info(f"QR_OPERATION: {operation} | Context: {json.dumps(context, ensure_ascii=True)}")
    
    def _build_context(self, module: str = None, **kwargs) -> Dict[str, Any]:
        """构建上下文信息"""
        context = {
            'timestamp': datetime.now().isoformat(),
            'module': module or 'SYSTEM',
        }
        
        # 添加额外上下文
        for key, value in kwargs.items():
            if value is not None:
                context[key] = value
        
        return context
    
    def get_logs(self, date: datetime = None, level: str = None, module: str = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取日志记录"""
        if date is None:
            date = datetime.now()
        
        log_file = os.path.join(self.log_dir, f'qr_system_{date.strftime("%Y%m%d")}.log')
        
        if not os.path.exists(log_file):
            return []
        
        logs = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    # 简单的日志解析
                    parts = line.strip().split(' - ', 4)
                    if len(parts) >= 5:
                        log_entry = {
                            'timestamp': parts[0],
                            'name': parts[1],
                            'level': parts[2],
                            'function': parts[3],
                            'message': parts[4]
                        }
                        
                        # 过滤条件
                        if level and log_entry['level'] != level.upper():
                            continue
                        if module and module not in log_entry.get('message', ''):
                            continue
                        
                        logs.append(log_entry)
        except Exception as e:
            self.log_error(f"读取日志文件失败: {e}")
        
        return logs
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """清理旧日志文件"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(self.log_dir, filename)
                    if os.path.getmtime(file_path) < cutoff_date:
                        os.remove(file_path)
                        self.log_info(f"清理旧日志文件: {filename}")
        except Exception as e:
            self.log_error(f"清理日志文件失败: {e}")

# 全局日志实例
system_logger = SystemLogger()

# 快捷函数
def log_info(message: str, module: str = None, **kwargs):
    system_logger.log_info(message, module, **kwargs)

def log_warning(message: str, module: str = None, **kwargs):
    system_logger.log_warning(message, module, **kwargs)

def log_error(message: str, module: str = None, exception: Exception = None, **kwargs):
    system_logger.log_error(message, module, exception, **kwargs)

def log_debug(message: str, module: str = None, **kwargs):
    system_logger.log_debug(message, module, **kwargs)

def log_security(message: str, **kwargs):
    system_logger.log_security(message, **kwargs)

def log_business(action: str, **kwargs):
    system_logger.log_business(action, **kwargs)

def log_database(operation: str, **kwargs):
    system_logger.log_database(operation, **kwargs)

def log_user_action(user: str, action: str, **kwargs):
    system_logger.log_user_action(user, action, **kwargs)

def log_qr_operation(operation: str, **kwargs):
    system_logger.log_qr_operation(operation, **kwargs)