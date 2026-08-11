import csv
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List

class SimpleExportImportManager:
    """简化版的导入导出管理器（不依赖pandas）"""
    
    def __init__(self):
        self.export_dir = os.path.join('exports')
        self.import_dir = os.path.join('imports')
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保目录存在"""
        os.makedirs(self.export_dir, exist_ok=True)
        os.makedirs(self.import_dir, exist_ok=True)
    
    def export_to_csv(self, table_name: str, filename: str = None) -> str:
        """导出数据到CSV文件"""
        try:
            db_path = os.path.join('app', 'qr_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 获取数据
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # 获取列名
            column_names = [description[0] for description in cursor.description]
            
            # 生成文件名
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{table_name}_{timestamp}.csv"
            
            filepath = os.path.join(self.export_dir, filename)
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                writer.writerows(rows)
            
            conn.close()
            return filepath
            
        except Exception as e:
            raise Exception(f"导出CSV失败: {str(e)}")
    
    def import_from_csv(self, filepath: str, table_name: str) -> Dict[str, Any]:
        """从CSV导入数据"""
        try:
            db_path = os.path.join('app', 'qr_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            success_count = 0
            errors = []
            
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=1):
                    try:
                        # 动态构建SQL
                        columns = ', '.join(row.keys())
                        placeholders = ', '.join(['?' for _ in row.values()])
                        
                        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        cursor.execute(sql, list(row.values()))
                        success_count += 1
                        
                    except Exception as e:
                        errors.append(f"第{row_num}行: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'success_count': success_count,
                'errors': errors
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_template(self, table_name: str, file_type: str = 'csv') -> str:
        """生成导入模板"""
        try:
            db_path = os.path.join('app', 'qr_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 获取列信息
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            # 生成模板文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_template_{timestamp}.csv"
            filepath = os.path.join(self.export_dir, filename)
            
            # 写入模板
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                # 添加示例数据行
                writer.writerow(['示例数据'] * len(column_names))
            
            conn.close()
            return filepath
            
        except Exception as e:
            raise Exception(f"生成模板失败: {str(e)}")
    
    def export_users_to_csv(self) -> str:
        """导出用户数据到CSV"""
        try:
            db_path = os.path.join('app', 'qr_system.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.full_name, u.username, u.email, u.created_at, u.is_active,
                       GROUP_CONCAT(r.name) as roles
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """)
            
            rows = cursor.fetchall()
            column_names = ['ID', '姓名', '工号', '邮箱', '创建时间', '状态', '角色']
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"users_{timestamp}.csv"
            filepath = os.path.join(self.export_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(column_names)
                writer.writerows(rows)
            
            conn.close()
            return filepath
            
        except Exception as e:
            raise Exception(f"导出用户数据失败: {str(e)}")

# 全局实例
export_manager = SimpleExportImportManager()