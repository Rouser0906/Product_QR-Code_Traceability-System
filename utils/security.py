import re
import sqlite3
import os
from typing import Any, Dict, List, Union
import hashlib
import secrets

class SecurityManager:
    """安全管理器：提供输入验证、SQL注入防护、数据加密等功能"""
    
    def __init__(self):
        self.sql_injection_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b|--|\/\*|\*\/|;)",
            r"(\b(OR|AND)\b\s*\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\b\s*['\"][^'\"]*['\"]\s*=\s*['\"][^'\"]*['\"])",
            r"(\bXP_\w+|SP_\w+|SYS\.\w+)",
            r"(0x[0-9a-fA-F]+)",
            r"(\b(CHAR|NCHAR|VARCHAR|NVARCHAR|CAST|CONVERT)\s*\()",
        ]
        
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>.*?</iframe>",
            r"<object[^>]*>.*?</object>",
            r"<embed[^>]*>.*?</embed>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>.*?</style>",
        ]
        
        self.phone_pattern = re.compile(r"^(\d{3,4}-?\s*\d{7,8}(-\d{1,4})?|\d{11}|1[3-9]\d{9})$")
        self.email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        self.url_pattern = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")
    
    def sanitize_input(self, value: str, input_type: str = "text") -> str:
        """清理和验证输入数据"""
        if not isinstance(value, str):
            return str(value)
        
        # 基础清理
        value = value.strip()
        
        # 防止SQL注入
        if self.detect_sql_injection(value):
            raise ValueError("输入包含潜在的SQL注入风险")
        
        # 防止XSS攻击
        if self.detect_xss(value):
            raise ValueError("输入包含潜在的XSS攻击风险")
        
        # 根据输入类型进行特定验证
        if input_type == "phone":
            if not self.validate_phone(value):
                raise ValueError("无效的手机号码格式")
        elif input_type == "email":
            if not self.validate_email(value):
                raise ValueError("无效的邮箱格式")
        elif input_type == "url":
            if not self.validate_url(value):
                raise ValueError("无效的网址格式")
        elif input_type == "number":
            if not value.isdigit():
                raise ValueError("请输入有效的数字")
        elif input_type == "alphanumeric":
            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", value):
                raise ValueError("只能包含字母、数字、空格、连字符和下划线")
        
        # 转义特殊字符
        value = self.escape_special_chars(value)
        
        return value
    
    def detect_sql_injection(self, value: str) -> bool:
        """检测SQL注入攻击"""
        value_upper = value.upper()
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    def detect_xss(self, value: str) -> bool:
        """检测XSS攻击"""
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def validate_phone(self, phone: str) -> bool:
        """验证手机号码格式"""
        return bool(self.phone_pattern.match(phone))
    
    def validate_email(self, email: str) -> bool:
        """验证邮箱格式"""
        return bool(self.email_pattern.match(email))
    
    def validate_url(self, url: str) -> bool:
        """验证网址格式"""
        return bool(self.url_pattern.match(url))
    
    def escape_special_chars(self, value: str) -> str:
        """转义特殊字符"""
        # 转义SQL特殊字符
        sql_special_chars = ["'", '"', ';', "--", "/*", "*/", "xp_", "sp_"]
        for char in sql_special_chars:
            value = value.replace(char, f"\\{char}")
        
        return value
    
    def parameterize_query(self, query: str, params: Dict[str, Any]) -> tuple:
        """将查询参数化以防止SQL注入"""
        if not isinstance(params, dict):
            raise ValueError("参数必须是字典类型")
        
        # 验证参数名
        for key in params.keys():
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", key):
                raise ValueError(f"无效的参数名: {key}")
        
        # 清理参数值
        clean_params = {}
        for key, value in params.items():
            if isinstance(value, str):
                clean_params[key] = self.sanitize_input(value)
            else:
                clean_params[key] = value
        
        return query, clean_params
    
    def hash_password(self, password: str) -> str:
        """安全地哈希密码"""
        if not isinstance(password, str):
            raise ValueError("密码必须是字符串")
        
        # 使用SHA-256 + 盐值
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return salt + password_hash.hex()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        if not isinstance(password, str) or not isinstance(hashed_password, str):
            return False
        
        if len(hashed_password) < 64:
            return False
        
        salt = hashed_password[:64]
        stored_hash = hashed_password[64:]
        
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return password_hash.hex() == stored_hash
    
    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)
    
    def limit_string_length(self, value: str, max_length: int) -> str:
        """限制字符串长度"""
        if not isinstance(value, str):
            return str(value)[:max_length]
        return value[:max_length]
    
    def validate_batch_size(self, size: int, max_size: int = 1000) -> int:
        """验证批量操作大小"""
        if not isinstance(size, int) or size <= 0:
            return 1
        return min(size, max_size)

class DatabaseSecurity:
    """数据库安全工具类"""
    
    @staticmethod
    def get_secure_connection(db_path: str) -> sqlite3.Connection:
        """获取安全的数据库连接"""
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = memory")
        return conn
    
    @staticmethod
    def validate_table_name(table_name: str) -> bool:
        """验证表名是否合法"""
        if not isinstance(table_name, str):
            return False
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name) is not None
    
    @staticmethod
    def validate_column_name(column_name: str) -> bool:
        """验证列名是否合法"""
        if not isinstance(column_name, str):
            return False
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name) is not None

# 全局安全管理器实例
security_manager = SecurityManager()