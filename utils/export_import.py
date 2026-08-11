import pandas as pd
import sqlite3
import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import openpyxl
from utils.logger import log_info, log_error
from utils.security import security_manager
from utils.validator import data_validator

class ExportImportManager:
    """数据导出导入管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.export_dir = os.path.join(os.path.dirname(db_path), 'exports')
        self.import_dir = os.path.join(os.path.dirname(db_path), 'imports')
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保导出导入目录存在"""
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.import_dir, exist_ok=True)
    
    def export_to_excel(self, table_name: str, filters: Dict[str, Any] = None) -> str:
        """导出到Excel"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            df = pd.read_sql_query(query, conn, params=params if params else None)
            conn.close()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.xlsx"
            filepath = os.path.join(self.export_dir, filename)
            
            # 创建Excel文件
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=table_name, index=False)
                
                # 添加元数据工作表
                metadata = pd.DataFrame([
                    {'字段': '导出时间', '值': datetime.now().isoformat()},
                    {'字段': '记录数', '值': len(df)},
                    {'字段': '表名', '值': table_name}
                ])
                metadata.to_excel(writer, sheet_name='元数据', index=False)
            
            log_info(f"成功导出 {table_name} 到 Excel: {filename}")
            return filepath
            
        except Exception as e:
            log_error(f"导出到Excel失败: {str(e)}", table_name=table_name)
            raise
    
    def export_to_csv(self, table_name: str, filters: Dict[str, Any] = None) -> str:
        """导出到CSV"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(f"{key} = ?")
                    params.append(value)
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            df = pd.read_sql_query(query, conn, params=params if params else None)
            conn.close()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_{timestamp}.csv"
            filepath = os.path.join(self.export_dir, filename)
            
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            log_info(f"成功导出 {table_name} 到 CSV: {filename}")
            return filepath
            
        except Exception as e:
            log_error(f"导出到CSV失败: {str(e)}", table_name=table_name)
            raise
    
    def export_all_tables(self, format_type: str = 'excel') -> str:
        """导出所有表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"all_tables_{timestamp}.{format_type}"
            filepath = os.path.join(self.export_dir, filename)
            
            if format_type == 'excel':
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    for table in tables:
                        try:
                            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                            df.to_excel(writer, sheet_name=table, index=False)
                        except Exception as e:
                            log_error(f"导出表 {table} 失败: {str(e)}")
            
            elif format_type == 'csv':
                # 创建压缩包包含所有CSV文件
                import zipfile
                zip_path = os.path.join(self.export_dir, f"all_tables_{timestamp}.zip")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for table in tables:
                        try:
                            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                            csv_path = os.path.join(self.export_dir, f"{table}.csv")
                            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                            zipf.write(csv_path, f"{table}.csv")
                            os.remove(csv_path)  # 清理临时文件
                        except Exception as e:
                            log_error(f"导出表 {table} 失败: {str(e)}")
                filepath = zip_path
            
            conn.close()
            log_info(f"成功导出所有表到 {format_type}: {filename}")
            return filepath
            
        except Exception as e:
            log_error(f"导出所有表失败: {str(e)}")
            raise
    
    def import_from_excel(self, filepath: str, table_name: str, 
                         update_existing: bool = False) -> Dict[str, Any]:
        """从Excel导入"""
        try:
            # 验证文件
            validation = data_validator.validate_file_path(filepath, ['.xlsx', '.xls'])
            if not validation['valid']:
                return {'success': False, 'errors': validation['errors']}
            
            # 读取Excel文件
            df = pd.read_excel(filepath, sheet_name=table_name)
            
            # 验证数据
            validation_result = self._validate_import_data(df, table_name)
            if not validation_result['valid']:
                return {'success': False, 'errors': validation_result['errors']}
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 检查是否已存在
                    if 'id' in row and not pd.isna(row['id']):
                        cursor.execute(f"SELECT 1 FROM {table_name} WHERE id = ?", (row['id'],))
                        exists = cursor.fetchone() is not None
                        
                        if exists and not update_existing:
                            continue
                    
                    # 构建插入/更新语句
                    columns = [col for col in df.columns if not pd.isna(row[col])]
                    values = [row[col] for col in columns]
                    
                    if 'id' in row and not pd.isna(row['id']) and update_existing:
                        # 更新现有记录
                        set_clause = ", ".join([f"{col} = ?" for col in columns if col != 'id'])
                        query = f"UPDATE {table_name} SET {set_clause} WHERE id = ?"
                        params = [row[col] for col in columns if col != 'id'] + [row['id']]
                    else:
                        # 插入新记录
                        placeholders = ", ".join(["?" for _ in columns])
                        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                        params = values
                    
                    cursor.execute(query, params)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{index + 2}行: {str(e)}")
            
            conn.commit()
            conn.close()
            
            result = {
                'success': True,
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
            
            log_info(f"成功导入 {table_name}: {success_count} 条记录")
            return result
            
        except Exception as e:
            log_error(f"导入Excel失败: {str(e)}", filepath=filepath)
            return {'success': False, 'error': str(e)}
    
    def import_from_csv(self, filepath: str, table_name: str, 
                       update_existing: bool = False) -> Dict[str, Any]:
        """从CSV导入"""
        try:
            # 验证文件
            validation = data_validator.validate_file_path(filepath, ['.csv'])
            if not validation['valid']:
                return {'success': False, 'errors': validation['errors']}
            
            # 读取CSV文件
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            
            # 验证数据
            validation_result = self._validate_import_data(df, table_name)
            if not validation_result['valid']:
                return {'success': False, 'errors': validation_result['errors']}
            
            return self.import_from_dataframe(df, table_name, update_existing)
            
        except Exception as e:
            log_error(f"导入CSV失败: {str(e)}", filepath=filepath)
            return {'success': False, 'error': str(e)}
    
    def import_from_dataframe(self, df: pd.DataFrame, table_name: str, 
                             update_existing: bool = False) -> Dict[str, Any]:
        """从DataFrame导入数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            success_count = 0
            error_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # 清理数据
                    cleaned_row = {}
                    for col, val in row.items():
                        if pd.isna(val):
                            cleaned_row[col] = None
                        else:
                            cleaned_row[col] = str(val).strip()
                    
                    # 验证数据
                    validation_result = data_validator.validate_data(cleaned_row, table_name)
                    if not validation_result['valid']:
                        error_count += 1
                        errors.append(f"第{index + 2}行: {validation_result['errors']}")
                        continue
                    
                    # 执行插入/更新
                    columns = list(validation_result['cleaned_data'].keys())
                    values = list(validation_result['cleaned_data'].values())
                    
                    placeholders = ", ".join(["?" for _ in columns])
                    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    cursor.execute(query, values)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"第{index + 2}行: {str(e)}")
            
            conn.commit()
            conn.close()
            
            result = {
                'success': True,
                'success_count': success_count,
                'error_count': error_count,
                'errors': errors
            }
            
            log_info(f"成功导入 {table_name}: {success_count} 条记录")
            return result
            
        except Exception as e:
            log_error(f"导入数据失败: {str(e)}", table_name=table_name)
            return {'success': False, 'error': str(e)}
    
    def _validate_import_data(self, df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
        """验证导入数据"""
        errors = []
        
        if df.empty:
            errors.append("数据文件为空")
            return {'valid': False, 'errors': errors}
        
        # 检查必需字段
        required_fields = {
            'companies': ['name'],
            'departments': ['name'],
            'staff': ['name', 'employee_id'],
            'product_types': ['name'],
            'product_specs': ['name'],
            'product_colors': ['name'],
            'product_features': ['name'],
            'distributors': ['name'],
            'logistics_vehicles': ['plate_number']
        }
        
        if table_name in required_fields:
            missing_fields = []
            for field in required_fields[table_name]:
                if field not in df.columns:
                    missing_fields.append(field)
            
            if missing_fields:
                errors.append(f"缺少必需字段: {', '.join(missing_fields)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def generate_template(self, table_name: str, format_type: str = 'excel') -> str:
        """生成导入模板"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # 创建模板数据
            template_data = []
            headers = [col[1] for col in columns]
            
            # 添加示例数据
            sample_data = {
                'companies': {
                    'name': '示例公司',
                    'english_name': 'Sample Company',
                    'address': '示例地址',
                    'website': 'http://example.com',
                    'front_phone': '010-12345678',
                    'service_phone': '400-1234567'
                },
                'departments': {
                    'name': '示例部门'
                },
                'staff': {
                    'name': '示例用户A',
                    'employee_id': 'EMP001',
                    'phone': '138XXXXXXXX',  # 示例电话号码
                    'position': '经理'
                },
                'product_types': {
                    'name': '示例产品类型',
                    'remark': '备注信息'
                },
                'product_specs': {
                    'name': '示例规格',
                    'remark': '备注信息'
                },
                'product_colors': {
                    'name': '红色',
                    'remark': '备注信息'
                },
                'product_features': {
                    'name': '示例特性',
                    'remark': '备注信息'
                },
                'distributors': {
                    'name': '示例经销商',
                    'contact_person': '示例用户B',
                    'phone': '139XXXXXXXX',  # 示例电话号码
                    'address': '示例地址',
                    'cooperation_date': '2024-01-01',
                    'status': '活跃'
                },
                'logistics_vehicles': {
                    'plate_number': '京A12345',
                    'driver_name': '王五',
                    'phone': '137XXXXXXXX',  # 示例电话号码
                    'vehicle_type': '货车',
                    'load_capacity': '10吨',
                    'status': '可用'
                }
            }
            
            # 创建DataFrame
            if table_name in sample_data:
                template_data.append(sample_data[table_name])
            else:
                # 通用模板
                template_data.append({col: f'示例{col}' for col in headers})
            
            df = pd.DataFrame(template_data)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_template_{timestamp}.{format_type}"
            filepath = os.path.join(self.export_dir, filename)
            
            if format_type == 'excel':
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='模板', index=False)
                    
                    # 添加说明
                    instructions = pd.DataFrame([
                        {'说明': '这是一个导入模板文件'},
                        {'说明': '请按照示例格式填写数据'},
                        {'说明': '带*的字段为必填项'},
                        {'说明': '日期格式请使用 YYYY-MM-DD'},
                        {'说明': '电话号码请使用标准格式'}
                    ])
                    instructions.to_excel(writer, sheet_name='使用说明', index=False)
            else:
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            conn.close()
            log_info(f"成功生成模板: {filename}")
            return filepath
            
        except Exception as e:
            log_error(f"生成模板失败: {str(e)}", table_name=table_name)
            raise

# 全局导出导入管理器
export_manager = ExportImportManager(os.path.join(os.path.dirname(__file__), 'qr_system.db'))