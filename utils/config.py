import json
import os
from typing import Any, Dict, Optional
from pathlib import Path
from utils.logger import log_info, log_error
from utils.security import security_manager

class ConfigManager:
    """Mn�h"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            self.config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        else:
            self.config_dir = config_dir
        
        self.config_file = os.path.join(self.config_dir, 'system_config.json')
        self.default_config = self._get_default_config()
        self.ensure_config_dir()
        self.config = self.load_config()
    
    def ensure_config_dir(self):
        """n�Mn�UX("""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """��ؤMn"""
        return {
            "system": {
                "name": "�������L���",
                "version": "2.0.0",
                "company": ":�l�",
                "debug": False,
                "auto_backup": {
                    "enabled": True,
                    "interval_hours": 24,
                    "retention_days": 30
                }
            },
            "database": {
                "backup_enabled": True,
                "backup_interval_hours": 24,
                "max_connections": 20,
                "timeout_seconds": 60,
                "pragma_settings": {
                    "journal_mode": "TRUNCATE",
                    "synchronous": "FULL",
                    "cache_size": 20000,
                    "temp_store": "memory",
                    "busy_timeout": 5000
                }
            },
            "security": {
                "session_timeout_hours": 24,
                "max_login_attempts": 5,
                "password_min_length": 8,
                "require_strong_password": True,
                "enable_audit_log": True
            },
            "qr_code": {
                "default_size": 200,
                "error_correction": "M",
                "border": 4,
                "format": "PNG",
                "quality": 95
            },
            "server": {
                "port": 8080,
                "host": "0.0.0.0",
                "timeout_seconds": 30
            },
            "ui": {
                "theme": "light",
                "language": "zh-CN",
                "font_size": 12,
                "auto_refresh_interval": 30,
                "show_tooltips": True
            },
            "export": {
                "default_format": "excel",
                "include_metadata": True,
                "date_format": "YYYY-MM-DD",
                "encoding": "utf-8-sig"
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 100,
                "max_files": 10,
                "include_debug_info": False
            },
            "notifications": {
                "email_enabled": False,
                "email_server": "",
                "email_port": 587,
                "email_username": "",
                "email_password": "",
                "email_from": ""
            }
        }
    
    def load_config(self) -> Dict[str, Any]:
        """�}Mn"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    
                # vؤMn�(7Mn
                return self._merge_config(self.default_config, user_config)
            else:
                # �ؤMn��
                self.save_config(self.default_config)
                return self.default_config
                
        except Exception as e:
            log_error(f"加载配置失败: {str(e)}")
            return self.default_config
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """vMn"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_config(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """�XMn"""
        try:
            # ��Mn
            validated_config = self._validate_config(config)
            
            # ��Mn
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.config_file, backup_file)
            
            # �X�Mn
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(validated_config, f, indent=2, ensure_ascii=False)
            
            self.config = validated_config
            log_info("Mn��X")
            return True
            
        except Exception as e:
            log_error(f"�XMn1%: {str(e)}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """��Mn"""
        # �,��
        if not isinstance(config, dict):
            return self.default_config
        
        # ��p<�
        if 'security' in config:
            security = config['security']
            if 'session_timeout_hours' in security:
                security['session_timeout_hours'] = max(1, min(168, security['session_timeout_hours']))
            
            if 'max_login_attempts' in security:
                security['max_login_attempts'] = max(3, min(10, security['max_login_attempts']))
            
            if 'password_min_length' in security:
                security['password_min_length'] = max(6, min(32, security['password_min_length']))
        
        if 'database' in config:
            db = config['database']
            if 'max_connections' in db:
                db['max_connections'] = max(1, min(100, db['max_connections']))
            
            if 'timeout_seconds' in db:
                db['timeout_seconds'] = max(5, min(300, db['timeout_seconds']))
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """��Mn<"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except KeyError:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """�nMn<"""
        keys = key.split('.')
        config = self.config
        
        try:
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            return self.save_config(self.config)
            
        except Exception as e:
            log_error(f"�nMn1%: {str(e)}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """y���Mn"""
        try:
            new_config = self.config.copy()
            new_config = self._deep_update(new_config, updates)
            return self.save_config(new_config)
            
        except Exception as e:
            log_error(f"y���Mn1%: {str(e)}")
            return False
    
    def _deep_update(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """���Mn"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_update(base[key], value)
            else:
                base[key] = value
        return base
    
    def reset_to_default(self) -> bool:
        """�n:ؤMn"""
        return self.save_config(self.default_config)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """��MnX�"""
        return {
            'system_name': self.get('system.name'),
            'version': self.get('system.version'),
            'debug_mode': self.get('system.debug'),
            'auto_backup': self.get('system.auto_backup.enabled'),
            'session_timeout': self.get('security.session_timeout_hours'),
            'theme': self.get('ui.theme'),
            'language': self.get('ui.language')
        }
    
    def export_config(self, filepath: str) -> bool:
        """��Mn"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            log_error(f"��Mn1%: {str(e)}")
            return False
    
    def import_config(self, filepath: str) -> bool:
        """�eMn"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
            
            # ��Mn
            validated_config = self._validate_config(new_config)
            return self.save_config(validated_config)
            
        except Exception as e:
            log_error(f"�eMn1%: {str(e)}")
            return False
    
    def get_database_config(self) -> Dict[str, Any]:
        """��pn�Mn"""
        return self.get('database', {})
    
    def get_security_config(self) -> Dict[str, Any]:
        """�։hMn"""
        return self.get('security', {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """��UIMn"""
        return self.get('ui', {})
    
    def get_qr_config(self) -> Dict[str, Any]:
        """�֌�Mn"""
        return self.get('qr_code', {})

# h@Mn�h
config_manager = ConfigManager()