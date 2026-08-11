import sqlite3
import os
import csv
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

# 使用CSV作为Excel的降级方案
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
    
    def export_to_csv(self, filename: str = None) -> str:
        """导出数据到CSV文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.table_name}_{timestamp}.csv"
            
            filepath = os.path.join('exports', filename)
            os.makedirs('exports', exist_ok=True)
            
            # 获取数据
            data = self.get_all_data()
            if not data:
                raise Exception("没有可导出的数据")
            
            # 获取列名
            if data:
                columns = list(data[0].keys())
            else:
                columns = []
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
                writer.writerows(data)
            
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
                            # 简单验证
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

# 导出函数别名，保持兼容性
export_to_excel = export_to_csv
import_from_excel = import_from_csv
generate_template_excel = generate_template_csv