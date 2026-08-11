import sqlite3
import os
import csv
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# 尝试导入pandas，如果失败则提供降级支持
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("警告: pandas模块未安装，Excel功能将使用CSV替代")

class BaseManager:
    def __init__(self, title: str, columns: List[str], table_name: str, entity_type: str):
        self.title = title
        self.columns = columns
        self.table_name = table_name
        self.entity_type = entity_type
        self._instance = None
        
        # 数据库连接
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')
        
        # 安全连接
        self._connection = None
    
    @property
    def connection(self):
        """获取数据库连接"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
        return self._connection
    
    def close_connection(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def get_all_data(self) -> List[Dict[str, Any]]:
        """获取所有数据"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY id")
            
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            print(f"获取 {self.entity_type} 数据失败: {e}")
            return []
    
    def export_to_excel(self, filename: str = None, query: str = None, params: tuple = None) -> str:
        """导出数据到Excel文件(.xlsx) - 降级到CSV"""
        if not HAS_PANDAS:
            # 降级到CSV导出
            return self.export_to_csv(filename.replace('.xlsx', '.csv') if filename else None, query, params)
        
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.table_name}_{timestamp}.xlsx"
            
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            # 获取数据
            cursor = self.connection.cursor()
            if query:
                cursor.execute(query, params or ())
            else:
                cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY id")
            
            # 获取列名和数据
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            if not rows:
                raise Exception("没有可导出的数据")
            
            # 创建DataFrame
            df = pd.DataFrame(rows, columns=columns)
            
            # 导出到Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            return filepath
            
        except Exception as e:
            raise Exception(f"导出失败: {str(e)}")
    
    def import_from_excel(self, filepath: str, sheet_name: str = None) -> Dict[str, Any]:
        """从Excel文件导入数据(.xlsx/.xls)"""
        if not HAS_PANDAS:
            return {'success': False, 'error': 'pandas模块未安装，无法导入Excel文件。请使用CSV格式文件。'}
        
        try:
            success_count = 0
            errors = []
            
            # 读取Excel文件
            df = pd.read_excel(filepath, sheet_name=sheet_name, engine='openpyxl')
            
            # 清理空值
            df = df.dropna(how='all')
            
            # 获取表结构信息
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            table_info = cursor.fetchall()
            table_columns = {col[1].lower(): col[1] for col in table_info if col[1].lower() != 'id'}
            
            # 映射Excel列名到数据库列名
            excel_columns = list(df.columns)
            column_mapping = {}
            
            for excel_col in excel_columns:
                excel_col_lower = str(excel_col).strip().lower()
                if excel_col_lower in table_columns:
                    column_mapping[excel_col] = table_columns[excel_col_lower]
            
            if not column_mapping:
                return {
                    'success': False,
                    'error': f"Excel列名与数据库表结构不匹配。\n预期列名: {', '.join(table_columns.values())}"
                }
            
            # 导入数据
            for index, row in df.iterrows():
                try:
                    row_num = index + 2  # Excel行号从1开始，加上表头
                    
                    # 清理数据：移除空值和ID字段
                    cleaned_data = {}
                    for excel_col, db_col in column_mapping.items():
                        value = row[excel_col]
                        if pd.notna(value):
                            cleaned_data[db_col] = str(value).strip()
                    
                    if not cleaned_data:
                        continue
                    
                    # 验证数据
                    valid = True
                    for key, value in cleaned_data.items():
                        if not value or value == '':
                            valid = False
                            errors.append(f"第{row_num}行: {key}不能为空")
                            break
                    
                    if valid:
                        # 构建插入语句
                        columns_str = ', '.join(cleaned_data.keys())
                        placeholders = ', '.join(['?' for _ in cleaned_data])
                        query = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                        
                        cursor.execute(query, tuple(cleaned_data.values()))
                        success_count += 1
                
                except Exception as e:
                    errors.append(f"第{row_num}行: {str(e)}")
            
            self.connection.commit()
            
            result = {
                'success': True,
                'success_count': success_count,
                'total_rows': len(df),
                'error_count': len(errors)
            }
            
            if errors:
                result['errors'] = errors
            
            return result
            
        except Exception as e:
            self.connection.rollback()
            return {'success': False, 'error': str(e)}
    
    def generate_template_excel(self) -> str:
        """生成Excel导入模板(.xlsx)"""
        if not HAS_PANDAS:
            return self.generate_template_csv()
        
        try:
            # 获取表结构
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns_info = cursor.fetchall()
            
            # 排除ID字段，生成模板列
            template_columns = [col[1] for col in columns_info if col[1].lower() != 'id']
            
            if not template_columns:
                raise Exception("无法获取表结构信息")
            
            # 生成示例数据
            sample_data = {}
            for col in template_columns:
                col_lower = col.lower()
                if 'name' in col_lower:
                    sample_data[col] = ["示例名称1", "示例名称2"]
                elif 'description' in col_lower:
                    sample_data[col] = ["示例描述1", "示例描述2"]
                elif 'address' in col_lower:
                    sample_data[col] = ["示例地址1", "示例地址2"]
                elif 'website' in col_lower:
                    sample_data[col] = ["www.example1.com", "www.example2.com"]
                elif 'phone' in col_lower or 'contact' in col_lower:
                    sample_data[col] = ["010-12345678", "020-87654321"]
                elif 'email' in col_lower:
                    sample_data[col] = ["example1@test.com", "example2@test.com"]
                elif 'type' in col_lower:
                    sample_data[col] = ["类型A", "类型B"]
                elif 'status' in col_lower:
                    sample_data[col] = ["启用", "禁用"]
                else:
                    sample_data[col] = ["示例数据1", "示例数据2"]
            
            # 创建DataFrame
            df = pd.DataFrame(sample_data)
            
            # 生成模板文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.table_name}_template_{timestamp}.xlsx"
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            # 导出到Excel
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            return filepath
            
        except Exception as e:
            raise Exception(f"生成模板失败: {str(e)}")
    
    def export_to_csv(self, filename: str = None, query: str = None, params: tuple = None) -> str:
        """导出数据到CSV文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.table_name}_{timestamp}.csv"
            
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            # 获取数据
            cursor = self.connection.cursor()
            if query:
                cursor.execute(query, params or ())
            else:
                cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY id")
            
            # 获取列名和数据
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            if not rows:
                raise Exception("没有可导出的数据")
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(columns)
                writer.writerows(rows)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"导出失败: {str(e)}")
    
    def import_from_csv(self, filepath: str) -> Dict[str, Any]:
        """从CSV导入数据"""
        try:
            success_count = 0
            errors = []
            
            with open(filepath, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        # 跳过空行
                        if not any(row.values()):
                            continue
                        
                        # 清理数据：移除空值和ID字段
                        cleaned_data = {}
                        for key, value in row.items():
                            if value is not None and str(value).strip() != '':
                                if key.lower() != 'id':  # 跳过ID字段
                                    cleaned_data[key] = str(value).strip()
                        
                        if cleaned_data:
                            # 验证数据
                            valid = True
                            for key, value in cleaned_data.items():
                                if not value or value == '':
                                    valid = False
                                    errors.append(f"第{row_num}行: {key}不能为空")
                                    break
                            
                            if valid:
                                # 构建插入语句
                                columns_str = ', '.join(cleaned_data.keys())
                                placeholders = ', '.join(['?' for _ in cleaned_data])
                                query = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
                                
                                cursor = self.connection.cursor()
                                cursor.execute(query, tuple(cleaned_data.values()))
                                success_count += 1
                    
                    except Exception as e:
                        errors.append(f"第{row_num}行: {str(e)}")
            
            self.connection.commit()
            
            return {
                'success': True,
                'success_count': success_count,
                'errors': errors
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_template_csv(self) -> str:
        """生成CSV导入模板"""
        try:
            # 获取表结构
            cursor = self.connection.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns_info = cursor.fetchall()
            
            # 排除ID字段，生成模板列
            template_columns = [col[1] for col in columns_info if col[1].lower() != 'id']
            
            # 生成模板文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.table_name}_template_{timestamp}.csv"
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            # 写入模板
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(template_columns)
                
                # 添加示例数据行
                example_row = []
                for col in template_columns:
                    if col.lower() == 'name':
                        example_row.append('示例名称')
                    elif col.lower() == 'description':
                        example_row.append('示例描述')
                    elif col.lower() == 'address':
                        example_row.append('示例地址')
                    elif col.lower() == 'website':
                        example_row.append('www.example.com')
                    elif col.lower() == 'phone' or col.lower() == 'contact':
                        example_row.append('010-12345678')
                    elif col.lower() == 'email':
                        example_row.append('test@example.com')
                    else:
                        example_row.append('示例数据')
                
                writer.writerow(example_row)
            
            return filepath
            
        except Exception as e:
            raise Exception(f"生成模板失败: {str(e)}")
    
    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取单个项目"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (item_id,))
            
            columns = [description[0] for description in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f"获取 {self.entity_type} 数据失败: {e}")
            return None
    
    def update_item(self, item_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新单个项目"""
        try:
            # 构建更新语句
            columns = [k for k in data.keys() if k.lower() != 'id']
            if not columns:
                return {'success': False, 'errors': {'data': '没有有效的更新数据'}}
            
            set_clause = ', '.join([f"{col} = ?" for col in columns])
            values = [data[col] for col in columns] + [item_id]
            
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?"
            
            cursor = self.connection.cursor()
            cursor.execute(query, values)
            self.connection.commit()
            
            return {'success': True}
            
        except Exception as e:
            self.connection.rollback()
            return {'success': False, 'errors': {'database': str(e)}}
    
    def remove_item(self, item_id: int) -> Dict[str, Any]:
        """删除单个项目"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (item_id,))
            self.connection.commit()
            
            if cursor.rowcount > 0:
                return {'success': True}
            else:
                return {'success': False, 'errors': {'database': '未找到要删除的记录'}}
                
        except Exception as e:
            self.connection.rollback()
            return {'success': False, 'errors': {'database': str(e)}}
    
    def __del__(self):
        """析构函数：清理资源"""
        self.close_connection()