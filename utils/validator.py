import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import os
from utils.security import security_manager
from utils.logger import log_warning, log_error

class DataValidator:
    """数据验证器：提供全面的数据验证功能"""
    
    def __init__(self):
        self.validation_rules = self._load_validation_rules()
    
    def _load_validation_rules(self) -> Dict[str, Dict]:
        """加载验证规则"""
        return {
            'company': {
                'name': {'required': True, 'max_length': 100, 'type': 'string'},
                'english_name': {'required': False, 'max_length': 100, 'type': 'string'},
                'address': {'required': False, 'max_length': 200, 'type': 'string'},
                'website': {'required': False, 'max_length': 100, 'type': 'url'},
                'front_phone': {'required': False, 'max_length': 20, 'type': 'phone'},
                'service_phone': {'required': False, 'max_length': 20, 'type': 'phone'},
            },
            'department': {
                'name': {'required': True, 'max_length': 50, 'type': 'string'},
            },
            'staff': {
                'name': {'required': True, 'max_length': 50, 'type': 'string'},
                'employee_id': {'required': True, 'max_length': 20, 'type': 'alphanumeric'},
                'phone': {'required': False, 'max_length': 20, 'type': 'phone'},
                'position': {'required': False, 'max_length': 50, 'type': 'string'},
            },
            'product_type': {
                'name': {'required': True, 'max_length': 50, 'type': 'string'},
                'remark': {'required': False, 'max_length': 200, 'type': 'string'},
            },
            'product_spec': {
                'name': {'required': True, 'max_length': 50, 'type': 'string'},
                'remark': {'required': False, 'max_length': 200, 'type': 'string'},
            },
            'product_color': {
                'name': {'required': True, 'max_length': 30, 'type': 'string'},
                'remark': {'required': False, 'max_length': 200, 'type': 'string'},
            },
            'product_feature': {
                'name': {'required': True, 'max_length': 50, 'type': 'string'},
                'remark': {'required': False, 'max_length': 200, 'type': 'string'},
            },
            'distributor': {
                'name': {'required': True, 'max_length': 100, 'type': 'string'},
                'contact_person': {'required': False, 'max_length': 50, 'type': 'string'},
                'phone': {'required': False, 'max_length': 20, 'type': 'phone'},
                'address': {'required': False, 'max_length': 200, 'type': 'string'},
                'cooperation_date': {'required': False, 'type': 'date'},
                'status': {'required': False, 'max_length': 20, 'type': 'string'},
                'remark': {'required': False, 'max_length': 500, 'type': 'string'},
            },
            'logistics_vehicle': {
                'plate_number': {'required': True, 'max_length': 20, 'type': 'string'},
                'driver_name': {'required': False, 'max_length': 50, 'type': 'string'},
                'phone': {'required': False, 'max_length': 20, 'type': 'phone'},
                'vehicle_type': {'required': False, 'max_length': 30, 'type': 'string'},
                'load_capacity': {'required': False, 'max_length': 20, 'type': 'string'},
                'status': {'required': False, 'max_length': 20, 'type': 'string'},
                'remark': {'required': False, 'max_length': 200, 'type': 'string'},
            },
            'qr_record': {
                'company_id': {'required': True, 'type': 'integer'},
                'department_id': {'required': True, 'type': 'integer'},
                'issuer_id': {'required': True, 'type': 'integer'},
                'product_id': {'required': True, 'type': 'integer'},
                'distributor_id': {'required': True, 'type': 'integer'},
                'salesperson_id': {'required': True, 'type': 'integer'},
                'quantity': {'required': True, 'type': 'integer', 'min': 1, 'max': 1000000},
                'unit': {'required': True, 'max_length': 10, 'type': 'string'},
                'batch_number': {'required': True, 'max_length': 50, 'type': 'string'},
                'plate_number': {'required': False, 'max_length': 20, 'type': 'string'},
                'phone': {'required': False, 'max_length': 20, 'type': 'phone'},
                'qr_sequence': {'required': True, 'max_length': 100, 'type': 'string'},
                'production_date': {'required': True, 'type': 'date'},
                'remark': {'required': False, 'max_length': 500, 'type': 'string'},
            },
        }
    
    def validate_data(self, data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """验证数据"""
        errors = {}
        warnings = {}
        
        if entity_type not in self.validation_rules:
            errors['entity_type'] = f"未知的实体类型: {entity_type}"
            return {'valid': False, 'errors': errors, 'warnings': warnings, 'cleaned_data': {}}
        
        rules = self.validation_rules[entity_type]
        cleaned_data = {}
        
        for field_name, rules_config in rules.items():
            value = data.get(field_name)
            
            # 检查必填字段
            if rules_config.get('required', False) and (value is None or str(value).strip() == ''):
                errors[field_name] = f"{field_name} 是必填字段"
                continue
            
            # 如果字段为空但不是必填，跳过验证
            if value is None or str(value).strip() == '':
                continue
            
            # 转换为字符串进行验证
            str_value = str(value).strip()
            
            try:
                # 应用安全清理
                if rules_config.get('type') == 'phone':
                    str_value = security_manager.sanitize_input(str_value, 'phone')
                elif rules_config.get('type') == 'email':
                    str_value = security_manager.sanitize_input(str_value, 'email')
                elif rules_config.get('type') == 'url':
                    str_value = security_manager.sanitize_input(str_value, 'url')
                elif rules_config.get('type') == 'number':
                    str_value = security_manager.sanitize_input(str_value, 'number')
                elif rules_config.get('type') == 'alphanumeric':
                    str_value = security_manager.sanitize_input(str_value, 'alphanumeric')
                else:
                    str_value = security_manager.sanitize_input(str_value)
                
                # 长度验证
                max_length = rules_config.get('max_length')
                if max_length and len(str_value) > max_length:
                    errors[field_name] = f"{field_name} 长度不能超过 {max_length} 个字符"
                    continue
                
                # 类型特定的验证
                field_type = rules_config.get('type')
                if field_type == 'integer':
                    try:
                        int_value = int(str_value)
                        min_val = rules_config.get('min')
                        max_val = rules_config.get('max')
                        if min_val is not None and int_value < min_val:
                            errors[field_name] = f"{field_name} 不能小于 {min_val}"
                            continue
                        if max_val is not None and int_value > max_val:
                            errors[field_name] = f"{field_name} 不能大于 {max_val}"
                            continue
                        cleaned_data[field_name] = int_value
                    except ValueError:
                        errors[field_name] = f"{field_name} 必须是整数"
                        continue
                
                elif field_type == 'date':
                    try:
                        if isinstance(value, (datetime, date)):
                            cleaned_data[field_name] = value
                        else:
                            # 尝试解析日期字符串
                            parsed_date = datetime.strptime(str_value, '%Y-%m-%d').date()
                            cleaned_data[field_name] = parsed_date
                    except ValueError:
                        errors[field_name] = f"{field_name} 日期格式无效，应为 YYYY-MM-DD"
                        continue
                
                elif field_type == 'phone':
                    if not security_manager.validate_phone(str_value):
                        warnings[field_name] = f"{field_name} 格式可能不正确，建议检查"
                    cleaned_data[field_name] = str_value
                
                elif field_type == 'email':
                    if not security_manager.validate_email(str_value):
                        warnings[field_name] = f"{field_name} 邮箱格式可能不正确"
                    cleaned_data[field_name] = str_value
                
                elif field_type == 'url':
                    if not security_manager.validate_url(str_value):
                        warnings[field_name] = f"{field_name} 网址格式可能不正确"
                    cleaned_data[field_name] = str_value
                
                else:
                    cleaned_data[field_name] = str_value
            
            except ValueError as e:
                errors[field_name] = str(e)
                continue
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'cleaned_data': cleaned_data
        }
    
    def validate_batch_data(self, data_list: List[Dict[str, Any]], entity_type: str) -> Dict[str, Any]:
        """批量验证数据"""
        results = []
        all_valid = True
        
        for index, data in enumerate(data_list):
            result = self.validate_data(data, entity_type)
            result['index'] = index
            results.append(result)
            
            if not result['valid']:
                all_valid = False
        
        return {
            'valid': all_valid,
            'results': results
        }
    
    def validate_file_path(self, file_path: str, allowed_extensions: List[str] = None) -> Dict[str, Any]:
        """验证文件路径"""
        errors = []
        warnings = []
        
        if not file_path:
            errors.append("文件路径不能为空")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            errors.append("文件不存在")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # 检查文件扩展名
        if allowed_extensions:
            _, ext = os.path.splitext(file_path)
            if ext.lower() not in [ext.lower() for ext in allowed_extensions]:
                errors.append(f"不支持的文件类型，支持的类型: {', '.join(allowed_extensions)}")
        
        # 检查文件大小
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                warnings.append("文件较大，可能影响性能")
        except OSError:
            errors.append("无法获取文件信息")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def validate_phone_number(self, phone: str) -> Dict[str, Any]:
        """验证电话号码 - 支持任何格式，无限制"""
        errors = []
        warnings = []
        
        if not phone:
            # 允许为空，不强制要求填写
            return {'valid': True, 'errors': errors, 'warnings': warnings, 'cleaned_phone': phone}
        
        # 清理输入 - 移除多余空格但保留原有格式
        phone = str(phone).strip()
        if not phone:
            return {'valid': True, 'errors': errors, 'warnings': warnings, 'cleaned_phone': phone}
        
        # 不再验证格式，允许任何格式的电话号码
        return {
            'valid': True,
            'errors': errors,
            'warnings': warnings,
            'cleaned_phone': phone
        }
    
    def validate_batch_number(self, batch_number: str) -> Dict[str, Any]:
        """验证批次号"""
        errors = []
        warnings = []
        
        if not batch_number:
            errors.append("批次号不能为空")
            return {'valid': False, 'errors': errors, 'warnings': warnings}
        
        # 清理输入
        batch_number = str(batch_number).strip().upper()
        
        # 验证格式：只允许字母、数字、连字符和下划线
        if not re.match(r'^[A-Z0-9-_]+$', batch_number):
            errors.append("批次号只能包含字母、数字、连字符和下划线")
        
        if len(batch_number) < 3 or len(batch_number) > 20:
            errors.append("批次号长度必须在3-20个字符之间")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'cleaned_batch_number': batch_number
        }

# 全局验证器实例
data_validator = DataValidator()