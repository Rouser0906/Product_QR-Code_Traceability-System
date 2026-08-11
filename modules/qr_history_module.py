from modules.base_manager import BaseManager
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox, QFileDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
import sqlite3
import os
from utils.permissions import has_permission
# 安全导入pandas，避免缺失依赖导致闪退
has_pandas = False
try:
    import pandas as pd
    has_pandas = True
except ImportError:
    pd = None
    print("警告: pandas未安装，Excel功能将使用CSV替代")
from datetime import datetime
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qr_system.db"))

class QRHistoryManager(BaseManager):
    _instance = None
    
    def __init__(self):
        columns = ["二维码编号", "QRC No.", "生成时间", "生成人", "状态", "备注"]
        sample_data = [
            ["QR-2024-001", "XPS-A1-30mm-白色", "2024-01-15 10:30:00", "示例用户A", "已打印", ""],
            ["QR-2024-002", "XPS-A2-50mm-灰色", "2024-01-16 14:20:00", "示例用户B", "已打印", ""]
        ]
        super().__init__("二维码历史", columns, sample_data)
        self.data = sample_data
        QRHistoryManager._instance = self
    
    @staticmethod
    def get_instance():
        if QRHistoryManager._instance is None:
            QRHistoryManager()
        return QRHistoryManager._instance
    
    @staticmethod
    def get_qr_numbers():
        instance = QRHistoryManager.get_instance()
        if instance and hasattr(instance, 'data'):
            return [row[0] for row in instance.data]
        return []
    
    @staticmethod
    def add_qr_record(qr_data):
        instance = QRHistoryManager.get_instance()
        if instance and hasattr(instance, 'data'):
            qr_numbers = [row[0] for row in instance.data]
            if qr_data[0] not in qr_numbers:
                instance.data.append(qr_data)


class QRHistoryModule(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {'username': 'guest', 'employee_id': 'guest'}
        self.initUI()
    
    def is_admin_or_developer(self):
        """检查当前用户是否为系统管理员或开发者"""
        return (self.current_user.get('username') == 'admin' and 
                self.current_user.get('employee_id') == 'admin')

    def load_data_from_db(self, filters=None, limit_records=True):
        filters = filters or []
        # 在数据加载前临时禁用排序，确保数据按数据库查询顺序显示
        sorting_was_enabled = self.table.isSortingEnabled()
        self.table.setSortingEnabled(False)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 查询完整的产品信息，关联员工表获取发行人姓名，使用COALESCE处理NULL值
        sql = """
        SELECT qr.qr_sequence, 
               COALESCE(qr.company_name, '') as company_name,
               COALESCE(qr.product_type, '') as product_type, 
               COALESCE(qr.product_spec, '') as product_spec, 
               COALESCE(qr.product_color, '') as product_color, 
               COALESCE(qr.product_feature, '') as product_feature, 
               CASE WHEN qr.batch_number IS NULL OR qr.batch_number = '' THEN '无' ELSE qr.batch_number END as batch_number, 
               COALESCE(qr.production_date, '') as production_date, 
               COALESCE(qr.distributor_name, '') as distributor_name, 
               COALESCE(qr.phone, '') as phone, 
               COALESCE(qr.created_at, '') as created_at, 
               COALESCE(e.name, qr.issuer_name, '未知') as issuer_display_name,
               COALESCE(qr.standard, '') as standard, 
               CASE WHEN qr.remark IS NULL OR qr.remark = '' THEN '无' ELSE qr.remark END as remark
        FROM qr_records qr
        LEFT JOIN staff e ON qr.issuer_name = e.employee_id
        WHERE (qr.qr_sequence LIKE 'HS-Q%' OR qr.qr_sequence LIKE 'ZY-Q%')
        """
        
        params = []
        if filters:
            fields = ["qr.qr_sequence", "qr.company_name", "qr.product_type", "qr.product_spec", "qr.product_color", 
                     "qr.product_feature", "qr.batch_number", "qr.production_date", "qr.distributor_name", 
                     "qr.phone", "qr.created_at", "issuer_display_name", "qr.standard", "qr.remark"]
            for i, value in enumerate(filters):
                if value and i < len(fields):
                    if i == 11:  # 发行人字段，需要特殊处理
                        sql += f" AND (e.name LIKE ? OR qr.issuer_name LIKE ?)"
                        params.extend([f"%{value}%", f"%{value}%"])
                    else:
                        sql += f" AND {fields[i]} LIKE ?"
                        params.append(f"%{value}%")
        
        # 按创建时间倒序排列
        sql += " ORDER BY qr.created_at DESC"
        
        # 智能数据加载策略：如果没有搜索条件且启用限制，则只显示最近10000条记录
        if limit_records and (not filters or not any(filters)):
            sql += " LIMIT 10000"
        
        try:
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    # 直接显示COALESCE处理后的值
                    display_value = str(value) if value is not None else ""
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
            
            # 数据加载完成后恢复排序设置
            if sorting_was_enabled:
                self.table.setSortingEnabled(True)
                # 设置默认排序：按创建时间列（第10列）降序排列
                self.table.sortByColumn(10, Qt.SortOrder.DescendingOrder)
            
            # 显示加载信息，区分不同的加载模式
            if limit_records and (not filters or not any(filters)):
                print(f"✅ 二维码历史数据加载完成，显示最近 {len(rows)} 条记录（默认限制10000条）")
                self.update_status_message(f"默认显示最近 {len(rows)} 条记录（最多10000条），使用搜索或显示全部查看更多数据")
            else:
                print(f"✅ 二维码历史数据搜索完成，共找到 {len(rows)} 条记录")
                if any(filters):
                    self.update_status_message(f"搜索完成，共找到 {len(rows)} 条匹配记录")
                else:
                    self.update_status_message(f"显示全部历史数据，共 {len(rows)} 条记录")
            
            # 显示加载的数据统计
            if len(rows) > 0:
                # 统计各公司的记录数
                company_stats = {}
                for row in rows:
                    company = row[1] if row[1] and row[1].strip() else "数据不完整"
                    company_stats[company] = company_stats.get(company, 0) + 1
                
                print("📊 加载的数据统计:")
                for company, count in sorted(company_stats.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {company}: {count} 条")
                    
        except Exception as e:
            print(f"❌ 关联查询失败: {e}")
            # 如果关联查询失败，使用简单查询作为备选
            try:
                simple_sql = """
                SELECT qr_sequence, 
                       COALESCE(company_name, '') as company_name,
                       COALESCE(product_type, '') as product_type, 
                       COALESCE(product_spec, '') as product_spec, 
                       COALESCE(product_color, '') as product_color, 
                       COALESCE(product_feature, '') as product_feature, 
                       CASE WHEN batch_number IS NULL OR batch_number = '' THEN '无' ELSE batch_number END as batch_number, 
                       COALESCE(production_date, '') as production_date, 
                       COALESCE(distributor_name, '') as distributor_name, 
                       COALESCE(phone, '') as phone, 
                       COALESCE(created_at, '') as created_at, 
                       COALESCE(issuer_name, '未知') as issuer_name, 
                       COALESCE(standard, '') as standard, 
                       CASE WHEN remark IS NULL OR remark = '' THEN '无' ELSE remark END as remark
                FROM qr_records 
                WHERE (qr_sequence LIKE 'HS-Q%' OR qr_sequence LIKE 'ZY-Q%')
                """
                
                # 添加过滤条件
                if filters:
                    fields = ["qr_sequence", "company_name", "product_type", "product_spec", "product_color", 
                             "product_feature", "batch_number", "production_date", "distributor_name", 
                             "phone", "created_at", "issuer_name", "standard", "remark"]
                    for i, value in enumerate(filters):
                        if value and i < len(fields):
                            simple_sql += f" AND {fields[i]} LIKE ?"
                            params.append(f"%{value}%")
                
                simple_sql += " ORDER BY created_at DESC"
                
                # 智能数据加载策略：如果没有搜索条件且启用限制，则只显示最近10000条记录
                if limit_records and (not filters or not any(filters)):
                    simple_sql += " LIMIT 10000"
                
                cursor.execute(simple_sql, params)
                rows = cursor.fetchall()
                
                self.table.setRowCount(len(rows))
                for row_idx, row_data in enumerate(rows):
                    for col_idx, value in enumerate(row_data):
                        display_value = str(value) if value is not None else ""
                        self.table.setItem(row_idx, col_idx, QTableWidgetItem(display_value))
                
                # 备用查询完成后也恢复排序设置
                if sorting_was_enabled:
                    self.table.setSortingEnabled(True)
                    # 设置默认排序：按创建时间列（第10列）降序排列
                    self.table.sortByColumn(10, Qt.SortOrder.DescendingOrder)
                
                # 显示备用查询加载信息
                if limit_records and (not filters or not any(filters)):
                    print(f"⚠️ 使用备选查询，显示最近 {len(rows)} 条记录（默认限制10000条）")
                    self.update_status_message(f"默认显示最近 {len(rows)} 条记录（最多10000条），使用搜索或显示全部查看更多数据")
                else:
                    print(f"⚠️ 使用备选查询，搜索到 {len(rows)} 条记录")
                    if filters and any(filters):
                        self.update_status_message(f"搜索完成，共找到 {len(rows)} 条匹配记录")
                    else:
                        self.update_status_message(f"显示全部历史数据，共 {len(rows)} 条记录")
                
                # 显示统计信息
                if len(rows) > 0:
                    company_stats = {}
                    for row in rows:
                        company = row[1] if row[1] and row[1].strip() else "数据不完整"
                        company_stats[company] = company_stats.get(company, 0) + 1
                    
                    print("📊 备选查询数据统计:")
                    for company, count in sorted(company_stats.items(), key=lambda x: x[1], reverse=True):
                        print(f"  {company}: {count} 条")
                
            except Exception as e2:
                print(f"❌ 备选查询也失败: {e2}")
                # 确保在异常情况下也恢复排序设置
                if sorting_was_enabled:
                    self.table.setSortingEnabled(True)
        
        finally:
            conn.close()

    def on_query(self):
        filters = [edit.text().strip() for edit in self.filter_edits]
        # 搜索时不限制记录数，显示所有匹配的结果
        self.load_data_from_db(filters, limit_records=False)
    
    def reset_search(self):
        """重置搜索条件并重新加载默认数据"""
        # 清空所有搜索框
        for edit in self.filter_edits:
            edit.clear()
        # 重新加载数据（默认限制10000条）
        self.load_data_from_db()
        self.update_status_message("已重置搜索条件，显示默认数据")
    
    def show_all_data(self):
        """显示全部数据（不限制记录数）"""
        # 清空所有搜索框
        for edit in self.filter_edits:
            edit.clear()
        # 显示所有数据（不限制记录数）
        self.load_data_from_db(filters=None, limit_records=False)
        self.update_status_message("正在显示全部历史数据")
    
    def update_status_message(self, message):
        """更新状态消息"""
        if hasattr(self, 'statusLabel'):
            self.statusLabel.setText(f"💡 {message}")

    def export_to_excel(self):
        """导出二维码历史数据到Excel文件"""
        if not has_pandas or pd is None:
            QMessageBox.warning(self, "导出失败", "未安装 pandas，暂不支持导出 Excel。")
            return
        try:
            # 获取当前查询条件下的数据
            filters = [edit.text().strip() for edit in self.filter_edits]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            sql = """
            SELECT qr_sequence, company_name, product_type, product_spec, product_color, 
                   product_feature, batch_number, production_date, distributor_name, 
                   phone, created_at, issuer_name, standard, remark
            FROM qr_records 
            WHERE 1=1
            """
            params = []
            if any(filters):
                fields = ["qr_sequence", "company_name", "product_type", "product_spec", "product_color", 
                         "product_feature", "batch_number", "production_date", "distributor_name", 
                         "phone", "created_at", "issuer_name", "standard", "remark"]
                for i, value in enumerate(filters):
                    if value and i < len(fields):
                        sql += f" AND {fields[i]} LIKE ?"
                        params.append(f"%{value}%")
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "没有可导出的数据")
                return
            
            # 创建DataFrame
            df = pd.DataFrame(rows, columns=[
                "QRC No.", "公司名称", "产品类型", "产品规格", "产品颜色", 
                "产品特性", "生产批次", "生产日期", "经销商", "联系电话", 
                "生成时间", "发行人", "执行标准", "备注"
            ])
            
            # 保存文件
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存Excel文件", "", "Excel文件 (*.xlsx)"
            )
            if filename:
                df.to_excel(filename, index=False, engine='openpyxl')
                QMessageBox.information(self, "成功", f"数据已导出到:\n{filename}")
                
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出Excel文件失败:\n{str(e)}")

    def import_from_excel(self):
        """从Excel文件导入二维码历史数据"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
            )
            if not filename:
                return
            
            # 读取Excel文件（需要pandas）
            if not has_pandas or pd is None:
                QMessageBox.warning(self, "导入失败", "未安装 pandas，暂不支持 Excel 导入。")
                return
            df = pd.read_excel(filename)
            
            # 验证列名
            expected_columns = ["二维码编号", "QRC No.", "生成时间", "生成人", "状态", "备注"]
            if list(df.columns) != expected_columns:
                QMessageBox.warning(self, "导入失败", f"Excel列名不正确。\n预期列名: {', '.join(expected_columns)}")
                return
            
            # 导入数据
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO qr_history (qr_code, product_info, create_time, creator, status, remark)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(row["二维码编号"]),
                        str(row["QRC No."]),
                        str(row["生成时间"]),
                        str(row["生成人"]),
                        str(row["状态"]),
                        str(row["备注"])
                    ))
                    imported_count += 1
                except Exception as e:
                    print(f"跳过行导入错误: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "导入成功", f"成功导入 {imported_count} 条记录")
            self.load_data_from_db()
            
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"导入Excel文件失败:\n{str(e)}")

    def download_template(self):
        """下载Excel导入模板"""
        if not has_pandas or pd is None:
            QMessageBox.warning(self, "下载失败", "未安装 pandas，暂不支持生成 Excel 模板。")
            return
        try:
            template_data = {
                "二维码编号": ["QR-2024-001", "QR-2024-002"],
                "QRC No.": ["XPS-A1-30mm-白色", "XPS-A2-50mm-灰色"],
                "生成时间": ["2024-01-15 10:30:00", "2024-01-16 14:20:00"],
                "生成人": ["示例用户A", "示例用户B"],
                "状态": ["已打印", "已打印"],
                "备注": ["", ""]
            }
            
            df = pd.DataFrame(template_data)
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存模板文件", "二维码历史导入模板.xlsx", "Excel文件 (*.xlsx)"
            )
            if filename:
                df.to_excel(filename, index=False, engine='openpyxl')
                QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
                
        except Exception as e:
            QMessageBox.warning(self, "下载失败", f"下载模板失败:\n{str(e)}")

    def on_delete(self):
        # 权限检查：只有系统管理员或开发者才能删除
        if not self.is_admin_or_developer():
            QMessageBox.warning(self, "权限不足", 
                              "抱歉，只有系统管理员或系统开发者才能执行删除操作！\n\n"
                              "如需删除记录，请联系系统管理员。")
            return
        
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的记录！")
            return
        
        qr_code = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", 
                                   f"管理员操作确认\n\n"
                                   f"确定要删除二维码编号为 {qr_code} 的记录吗？\n"
                                   f"此操作不可撤销！", 
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM qr_records WHERE qr_sequence=?", (qr_code,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "删除成功", f"二维码记录 {qr_code} 已成功删除！")
                self.load_data_from_db([edit.text().strip() for edit in self.filter_edits])
            except Exception as e:
                # 确保连接关闭
                try:
                    if 'conn' in locals():
                        conn.close()
                except:
                    pass
                QMessageBox.warning(self, "删除失败", f"删除失败: {e}")

    # 移除edit_record方法和相关弹窗类

    def apply_permissions(self, user):
        """按角色权限控制二维码历史模块按钮可用性"""
        try:
            # 删除权限
            can_delete = has_permission(user, "qr_history.delete")
            if hasattr(self, "deleteBtn"):
                self.deleteBtn.setEnabled(bool(can_delete))
                if not can_delete:
                    self.deleteBtn.setToolTip("您没有删除二维码历史的权限")
            # 导出（下载）权限
            can_download = has_permission(user, "qr_history.download")
            if hasattr(self, "exportBtn"):
                self.exportBtn.setEnabled(bool(can_download))
            # 打印权限
            can_print = has_permission(user, "qr_history.print")
            if hasattr(self, "printBtn"):
                self.printBtn.setEnabled(bool(can_print))
            # 其他按钮（查询/重置/显示全部/模板/导入）保持现状
        except Exception:
            pass

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("二维码历史管理")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 查询输入框行
        filter_layout = QHBoxLayout()
        self.filter_edits = []
        filter_labels = ["QRC No.", "公司名称", "产品类型", "产品规格", "产品颜色", "产品特性", "生产批次", "生产日期", "经销商", "联系电话", "生成时间", "发行人", "执行标准", "备注"]
        for label in filter_labels:
            edit = QLineEdit()
            edit.setPlaceholderText(label)
            edit.setFixedWidth(100)  # 减小宽度以适应更多字段
            self.filter_edits.append(edit)
            filter_layout.addWidget(edit)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 操作按钮
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)
        self.queryBtn = QPushButton("查询")
        self.queryBtn.setFixedWidth(100)
        self.queryBtn.setFont(QFont("Microsoft YaHei", 12))
        self.queryBtn.clicked.connect(self.on_query)
        btnLayout.addWidget(self.queryBtn)
        
        # 重置按钮
        self.resetBtn = QPushButton("重置")
        self.resetBtn.setFixedWidth(100)
        self.resetBtn.setFont(QFont("Microsoft YaHei", 12))
        self.resetBtn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        self.resetBtn.clicked.connect(self.reset_search)
        btnLayout.addWidget(self.resetBtn)
        
        # 显示全部按钮
        self.showAllBtn = QPushButton("显示全部")
        self.showAllBtn.setFixedWidth(100)
        self.showAllBtn.setFont(QFont("Microsoft YaHei", 12))
        self.showAllBtn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        self.showAllBtn.clicked.connect(self.show_all_data)
        btnLayout.addWidget(self.showAllBtn)
        self.exportBtn = QPushButton("导出Excel")
        self.exportBtn.setFixedWidth(100)
        self.exportBtn.setFont(QFont("Microsoft YaHei", 12))
        self.exportBtn.clicked.connect(self.export_to_excel)
        btnLayout.addWidget(self.exportBtn)
        
        self.importBtn = QPushButton("导入Excel")
        self.importBtn.setFixedWidth(100)
        self.importBtn.setFont(QFont("Microsoft YaHei", 12))
        self.importBtn.clicked.connect(self.import_from_excel)
        btnLayout.addWidget(self.importBtn)
        
        self.templateBtn = QPushButton("下载模板")
        self.templateBtn.setFixedWidth(100)
        self.templateBtn.setFont(QFont("Microsoft YaHei", 12))
        self.templateBtn.clicked.connect(self.download_template)
        btnLayout.addWidget(self.templateBtn)
        # 删除按钮 - 只有管理员或开发者才能看到
        if self.is_admin_or_developer():
            self.deleteBtn = QPushButton("删除")
            self.deleteBtn.setFixedWidth(100)
            self.deleteBtn.setFont(QFont("Microsoft YaHei", 12))
            self.deleteBtn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
            self.deleteBtn.clicked.connect(self.on_delete)
            btnLayout.addWidget(self.deleteBtn)
        self.printBtn = QPushButton("打印")
        self.printBtn.setFixedWidth(100)
        self.printBtn.setFont(QFont("Microsoft YaHei", 12))
        btnLayout.addWidget(self.printBtn)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)
        
        # 状态提示标签
        self.statusLabel = QLabel("💡 默认显示最近10000条记录，使用搜索功能可查看全部历史数据")
        self.statusLabel.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 8px;
                background-color: #f0f8ff;
                border: 1px solid #ddd;
                border-radius: 4px;
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.statusLabel)

        # 数据表格 - 显示完整的产品信息
        self.table = QTableWidget(0, 14)
        self.table.setHorizontalHeaderLabels([
            "QRC No.", "公司名称", "产品类型", "产品规格", "产品颜色", 
            "产品特性", "生产批次", "生产日期", "经销商", "联系电话", 
            "生成时间", "发行人", "执行标准", "备注"
        ])
        
        # 表格样式优化 - 清晰网格线
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #c0c0c0;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #e3f2fd;
                border: 2px solid #808080;
                show-decoration-selected: 1;
            }
            QTableWidget::item {
                padding: 8px;
                border-right: 1px solid #c0c0c0;
                border-bottom: 1px solid #c0c0c0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 10px;
                border: 1px solid #808080;
                font-weight: bold;
                font-size: 14px;
                color: #333;
            }
        """)
        
        # 设置表格属性
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(True)  # 显示网格线
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 表头设置
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)  # 允许手动调整列宽
        header.setFixedHeight(45)
        
        # 垂直表头
        v_header = self.table.verticalHeader()
        v_header.setVisible(False)  # 隐藏行号
        v_header.setDefaultSectionSize(50)
        
        # 设置列宽
        column_widths = [120, 150, 100, 120, 80, 100, 100, 100, 120, 120, 140, 100, 120, 100]
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)
        
        layout.addWidget(self.table)

        # 初始加载全部数据
        self.load_data_from_db()
        # 权限应用：根据当前用户角色控制按钮
        try:
            if hasattr(self, "current_user"):
                self.apply_permissions(self.current_user)
        except Exception:
            pass
