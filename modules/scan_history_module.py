from modules.base_manager import BaseManager
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QLineEdit, QMessageBox, QSizePolicy
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
import os
# Excel功能支持
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("警告: pandas未安装，Excel功能将使用CSV替代")
from datetime import datetime
from utils.permissions import has_permission
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qr_system.db"))
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox

class ScanHistoryManager(BaseManager):
    _instance = None
    
    def __init__(self):
        columns = ["扫码编号", "QRC No.", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县", "设备信息"]
        sample_data = [
            ["SCAN-2024-001", "XPS-A1-30mm-白色-2024-001", "2024-01-15 15:30:00", "示例用户A", "13800000001", "demo_user_a", "中国", "示例省", "示例市A", "示例区A", "iPhone 12"],
            ["SCAN-2024-002", "XPS-A2-50mm-灰色-2024-002", "2024-01-16 09:15:00", "示例用户B", "13800000004", "demo_user_b", "中国", "示例省", "示例市B", "示例区B", "华为P40"]
        ]
        super().__init__("扫码历史信息", columns, sample_data)
        self.data = sample_data
        ScanHistoryManager._instance = self
    
    @staticmethod
    def get_instance():
        if ScanHistoryManager._instance is None:
            ScanHistoryManager()
        return ScanHistoryManager._instance
    
    @staticmethod
    def get_scan_numbers():
        instance = ScanHistoryManager.get_instance()
        if instance and hasattr(instance, 'data'):
            return [row[0] for row in instance.data]
        return []
    
    @staticmethod
    def add_scan_record(scan_data):
        instance = ScanHistoryManager.get_instance()
        if instance and hasattr(instance, 'data'):
            scan_numbers = [row[0] for row in instance.data]
            if scan_data[0] not in scan_numbers:
                instance.data.append(scan_data)


class ScanHistoryModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "scan_history.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查导出权限
        can_export = has_permission(user, "scan_history.export")
        if hasattr(self, 'exportBtn'):
            self.exportBtn.setEnabled(can_export)
            if not can_export:
                self.exportBtn.setToolTip("您没有导出扫描历史的权限")
                
        # 检查导入权限
        can_import = has_permission(user, "scan_history.import")
        if hasattr(self, 'importBtn'):
            self.importBtn.setEnabled(can_import)
            if not can_import:
                self.importBtn.setToolTip("您没有导入扫描历史的权限")
                
        # 检查下载模板权限
        can_download_template = has_permission(user, "scan_history.download_template")
        if hasattr(self, 'templateBtn'):
            self.templateBtn.setEnabled(can_download_template)
            if not can_download_template:
                self.templateBtn.setToolTip("您没有下载模板的权限")
                
        # 检查删除权限
        can_delete = has_permission(user, "scan_history.delete")
        if hasattr(self, 'deleteBtn'):
            self.deleteBtn.setEnabled(can_delete)
            if not can_delete:
                self.deleteBtn.setToolTip("您没有删除扫描历史的权限")
                
        # 检查打印权限
        can_print = has_permission(user, "scan_history.print")
        if hasattr(self, 'printBtn'):
            self.printBtn.setEnabled(can_print)
            if not can_print:
                self.printBtn.setToolTip("您没有打印扫描历史的权限")
                
        print(f"扫描历史模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 导出: {can_export}, 导入: {can_import}, 下载模板: {can_download_template}, 删除: {can_delete}, 打印: {can_print}")
    
    def setup_corner_header(self):
        """设置表格左上角的'序号'标题"""
        try:
            # 启用左上角按钮
            self.table.setCornerButtonEnabled(True)
            
            # 使用定时器延迟设置，确保表格完全初始化
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.delayed_corner_setup)
        except Exception as e:
            print(f"设置左上角标题失败: {e}")
    
    def delayed_corner_setup(self):
        """延迟设置左上角标题"""
        try:
            for child in self.table.children():
                if isinstance(child, QPushButton):
                    child.setText("序号")
                    child.setStyleSheet("""
                        QPushButton {
                            background-color: #f0f0f0;
                            border: 1px solid #d0d0d0;
                            font-size: 14px;
                            font-weight: bold;
                            color: #333;
                            text-align: center;
                        }
                    """)
                    break
        except Exception as e:
            print(f"延迟设置左上角标题失败: {e}")

    def load_data_from_db(self, filters=None, search_type="normal"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        sql = "SELECT scan_id, qr_code, scan_time, scanner_name, scanner_phone, scanner_wechat, country, province, city, district, device_info FROM scan_history WHERE 1=1"
        params = []
        
        if filters:
            fields = ["scan_id", "qr_code", "scan_time", "scanner_name", "scanner_phone", "scanner_wechat", "country", "province", "city", "district"]
            for i, value in enumerate(filters):
                if value and i < len(fields):
                    field_name = fields[i]
                    
                    # 特殊处理手机号字段
                    if field_name == "scanner_phone":
                        # 支持多种手机号格式搜索
                        phone_conditions = []
                        
                        # 原始格式搜索
                        if search_type == "exact":
                            phone_conditions.append(f"{field_name} = ?")
                            params.append(value)
                        else:
                            phone_conditions.append(f"{field_name} LIKE ?")
                            params.append(f"%{value}%")
                        
                        # 如果输入是纯数字（不含+86），尝试匹配带+86的格式
                        if value.isdigit() and len(value) == 11:
                            if search_type == "exact":
                                phone_conditions.append(f"{field_name} = ?")
                                params.append(f"+86{value}")
                            else:
                                phone_conditions.append(f"{field_name} LIKE ?")
                                params.append(f"%+86{value}%")
                        
                        # 如果输入包含+86，尝试匹配纯数字格式
                        elif value.startswith("+86") and value[3:].isdigit():
                            pure_number = value[3:]
                            if search_type == "exact":
                                phone_conditions.append(f"{field_name} = ?")
                                params.append(pure_number)
                            else:
                                phone_conditions.append(f"{field_name} LIKE ?")
                                params.append(f"%{pure_number}%")
                        
                        # 组合手机号搜索条件
                        if phone_conditions:
                            sql += " AND (" + " OR ".join(phone_conditions) + ")"
                    else:
                        # 其他字段的正常搜索逻辑
                        if search_type == "exact":
                            # 精确搜索：完全匹配
                            sql += f" AND {field_name} = ?"
                            params.append(value)
                        elif search_type == "fuzzy":
                            # 模糊搜索：包含匹配（默认行为）
                            sql += f" AND {field_name} LIKE ?"
                            params.append(f"%{value}%")
                        else:
                            # 普通查询：包含匹配
                            sql += f" AND {field_name} LIKE ?"
                            params.append(f"%{value}%")
        
        # 按扫码时间倒序排列，最新的记录在前面
        sql += " ORDER BY scan_time DESC, scan_id DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        self.table.setRowCount(len(rows))
        
        # 设置垂直表头标签（只显示行号）
        if len(rows) > 0:
            vertical_labels = [str(i+1) for i in range(len(rows))]
            self.table.setVerticalHeaderLabels(vertical_labels)
        
        # 填充数据（只显示前10列，隐藏设备信息列）
        for row_idx, row_data in enumerate(rows):
            # 只处理前10列数据，跳过第11列（设备信息）
            display_cols = min(10, len(row_data))
            for col_idx in range(display_cols):
                value = row_data[col_idx] if col_idx < len(row_data) else ""
                display_value = str(value) if value is not None else ""
                
                # 特殊处理手机号，添加国家区号
                if col_idx == 4 and display_value and display_value != "":
                    if not display_value.startswith("(+86)") and display_value != "N/A":
                        display_value = f"(+86) {display_value}"
                
                item = QTableWidgetItem(display_value)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(row_idx, col_idx, item)

        
        # 自动调整列宽以适应内容
        self.table.resizeColumnsToContents()
        
        # 重新应用智能列宽设置，确保优化生效
        column_widths = [120, 180, 160, 90, 140, 120, 70, 100, 100, 110]
        for i, width in enumerate(column_widths):
            if i < self.table.columnCount():
                self.table.setColumnWidth(i, width)
        
        print(f"扫码历史数据加载完成，共 {len(rows)} 条记录")

    def on_query(self):
        filters = [edit.text().strip() for edit in self.filter_edits]
        
        # 检查是否有搜索条件
        if not any(filters):
            # 如果没有搜索条件，显示所有记录
            self.load_data_from_db()
            QMessageBox.information(self, "查询完成", f"已显示所有扫码记录，共 {self.table.rowCount()} 条")
        else:
            # 如果有搜索条件，执行查询
            self.load_data_from_db(filters)
            search_terms = [f for f in filters if f]
            QMessageBox.information(self, "查询完成", 
                                  f"搜索条件: {', '.join(search_terms)}\n"
                                  f"找到 {self.table.rowCount()} 条匹配记录")

    def on_fuzzy_search(self):
        """模糊搜索功能"""
        try:
            filters = [edit.text().strip() for edit in self.filter_edits]
            
            # 检查是否有搜索条件
            if not any(filters):
                QMessageBox.information(self, "提示", "请在上方输入框中输入搜索条件！")
                return
            
            # 使用模糊搜索加载数据
            self.load_data_from_db(filters, search_type="fuzzy")
            
            # 统计搜索结果
            result_count = self.table.rowCount()
            search_terms = [f for f in filters if f]
            QMessageBox.information(self, "模糊搜索完成", 
                                  f"搜索条件: {', '.join(search_terms)}\n"
                                  f"找到 {result_count} 条匹配记录")
            
        except Exception as e:
            QMessageBox.warning(self, "搜索失败", f"模糊搜索失败:\n{str(e)}")

    def on_exact_search(self):
        """精确搜索功能"""
        try:
            filters = [edit.text().strip() for edit in self.filter_edits]
            
            # 检查是否有搜索条件
            if not any(filters):
                QMessageBox.information(self, "提示", "请在上方输入框中输入搜索条件！")
                return
            
            # 使用精确搜索加载数据
            self.load_data_from_db(filters, search_type="exact")
            
            # 统计搜索结果
            result_count = self.table.rowCount()
            search_terms = [f for f in filters if f]
            QMessageBox.information(self, "精确搜索完成", 
                                  f"搜索条件: {', '.join(search_terms)}\n"
                                  f"找到 {result_count} 条匹配记录")
            
        except Exception as e:
            QMessageBox.warning(self, "搜索失败", f"精确搜索失败:\n{str(e)}")

    def on_refresh(self):
        """刷新扫码历史数据"""
        try:
            # 清空所有过滤条件
            for edit in self.filter_edits:
                edit.clear()
            
            # 重新加载所有数据
            self.load_data_from_db()
            
            # 统计记录总数
            total_count = self.table.rowCount()
            
            # 显示刷新成功消息
            QMessageBox.information(self, "刷新成功", 
                                  f"扫码历史数据已刷新！\n"
                                  f"已显示最新的 {total_count} 条扫码记录。\n"
                                  f"提示：可以使用上方搜索框查找特定记录。")
            
        except Exception as e:
            QMessageBox.warning(self, "刷新失败", f"刷新扫码历史数据失败:\n{str(e)}")

    def export_to_excel(self):
        """导出扫码历史数据到Excel文件"""
        try:
            # 获取当前查询条件下的数据
            filters = [edit.text().strip() for edit in self.filter_edits]
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            sql = "SELECT scan_id, qr_code, scan_time, scanner_name, scanner_phone, scanner_wechat, country, province, city, district, device_info FROM scan_history WHERE 1=1"
            params = []
            if any(filters):
                fields = ["scan_id", "qr_code", "scan_time", "scanner_name", "scanner_phone", "scanner_wechat", "country", "province", "city", "district", "town", "street", "address", "device_info"]
                for i, value in enumerate(filters):
                    if value:
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
                "扫码编号", "QRC No.", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县", "设备信息"
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
        """从Excel文件导入扫码历史数据"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "选择Excel文件", "", "Excel文件 (*.xlsx *.xls)"
            )
            if not filename:
                return
            
            # 读取Excel文件
            df = pd.read_excel(filename)
            
            # 验证列名 - 支持新旧多种格式
            new_columns = ["扫码编号", "QRC No.", "扫码时间", "手机号", "微信号", "国家", "省份", "城市", "区/县", "乡镇", "街道", "详细地址", "设备信息"]
            old_columns_v3 = ["扫码编号", "QRC No.", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县", "乡镇", "街道", "详细地址", "设备信息"]
            old_columns_v2 = ["扫码编号", "移动端ID号", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县", "乡镇", "街道", "详细地址", "设备信息"]
            old_columns_v1 = ["扫码编号", "二维码内容", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县", "乡镇", "街道", "详细地址", "设备信息"]
            
            if list(df.columns) == old_columns_v1:
                # 如果是最旧格式（二维码内容），重命名列头以保持兼容性
                df.columns = new_columns
            elif list(df.columns) == old_columns_v2:
                # 如果是中间格式（移动端ID号），重命名列头以保持兼容性
                df.columns = new_columns
            elif list(df.columns) != new_columns:
                QMessageBox.warning(self, "导入失败", f"Excel列名不正确。\n支持的列名格式:\n最新格式: {', '.join(new_columns)}\n兼容格式1: {', '.join(old_columns_v2)}\n兼容格式2: {', '.join(old_columns_v1)}")
                return
            
            # 导入数据
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            imported_count = 0
            for _, row in df.iterrows():
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO scan_history (scan_id, qr_code, scan_time, scanner_name, scanner_phone, scanner_wechat, country, province, city, district, town, street, address, device_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row["扫码编号"]),
                        str(row["QRC No."]),
                        str(row["扫码时间"]),
                        str(row["姓名"]),
                        str(row["手机号"]),
                        str(row["微信号"]),
                        str(row["国家"]),
                        str(row["省份"]),
                        str(row["城市"]),
                        str(row["区/县"]),
                        str(row["乡镇"]),
                        str(row["街道"]),
                        str(row["详细地址"]),
                        str(row["设备信息"])
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
        try:
            template_data = {
                "扫码编号": ["SCAN-2024-001", "SCAN-2024-002"],
                "QRC No.": ["XPS-A1-30mm-白色-2024-001", "XPS-A2-50mm-灰色-2024-002"],
                "扫码时间": ["2024-01-15 15:30:00", "2024-01-16 09:15:00"],
                "姓名": ["示例用户A", "示例用户B"],
                "手机号": ["(+86) 13800000001", "(+86) 13800000004"],
                "微信号": ["demo_user_a", "demo_user_b"],
                "国家": ["中国", "中国"],
                "省份": ["示例省", "示例省"],
                "城市": ["示例市A", "示例市B"],
                "区/县": ["示例区A", "示例区B"],
                "设备信息": ["iPhone 12", "华为P40"]
            }
            
            df = pd.DataFrame(template_data)
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存模板文件", "扫码历史导入模板.xlsx", "Excel文件 (*.xlsx)"
            )
            if filename:
                df.to_excel(filename, index=False, engine='openpyxl')
                QMessageBox.information(self, "成功", f"模板已保存到:\n{filename}")
                
        except Exception as e:
            QMessageBox.warning(self, "下载失败", f"下载模板失败:\n{str(e)}")

    def on_delete(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的记录！")
            return
        scan_id = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除扫码编号为 {scan_id} 的记录吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM scan_history WHERE scan_id=?", (scan_id,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "成功", "记录已删除！")
                self.load_data_from_db([edit.text().strip() for edit in self.filter_edits])
            except Exception as e:
                QMessageBox.warning(self, "失败", f"删除失败: {e}")

    # 移除edit_record方法和相关弹窗类
    
    def darken_color(self, color, factor=0.2):
        """将颜色变暗指定比例"""
        if color.startswith('#'):
            # 处理十六进制颜色
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            r = max(0, min(255, int(r * (1 - factor))))
            g = max(0, min(255, int(g * (1 - factor))))
            b = max(0, min(255, int(b * (1 - factor))))
            return f"#{r:02x}{g:02x}{b:02x}"
        return color

    def initUI(self):
        layout = QVBoxLayout(self)
        # 调整为与其他模块一致的边距，实现基线对齐
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("扫码历史信息管理")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 查询输入框行 - 现代化样式
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        self.filter_edits = []
        filter_labels = ["扫码编号", "QRC No.", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县"]
        for label in filter_labels:
            edit = QLineEdit()
            edit.setPlaceholderText(label)
            edit.setFixedWidth(150)  # 统一宽度，视觉对齐
            edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    padding: 8px 12px;
                    font-size: 14px;
                    background-color: white;
                }
                QLineEdit:focus {
                    border: 2px solid #80bdff;
                    background-color: #f8f9fa;
                }
                QLineEdit::placeholder {
                    color: #6c757d;
                    font-style: italic;
                }
            """)
            self.filter_edits.append(edit)
            filter_layout.addWidget(edit)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # 操作按钮 - 现代化样式
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        
        # 按钮样式模板
        button_style = """
            QPushButton {
                border: 1px solid #007bff;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0056b3;
                color: white;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """
        
        # 主要操作按钮（蓝色主题）
        primary_buttons = [
            ("查询", self.on_query, "#007bff", "white"),
            ("模糊搜索", self.on_fuzzy_search, "#17a2b8", "white"),
            ("精确搜索", self.on_exact_search, "#28a745", "white"),
            ("刷新", self.on_refresh, "#6c757d", "white")
        ]
        
        for text, callback, bg_color, text_color in primary_buttons:
            btn = QPushButton(text)
            btn.setFixedWidth(100)
            btn.setFont(QFont("Microsoft YaHei", 12))
            btn.clicked.connect(callback)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {bg_color};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {self.darken_color(bg_color)};
                    border-color: {self.darken_color(bg_color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(bg_color, 0.3)};
                }}
            """)
            btnLayout.addWidget(btn)
        
        # 次要操作按钮（边框主题）
        secondary_buttons = [
            ("导出Excel", self.export_to_excel, "#28a745", "exportBtn"),
            ("导入Excel", self.import_from_excel, "#ffc107", "importBtn"),
            ("下载模板", self.download_template, "#17a2b8", "templateBtn"),
            ("删除", self.on_delete, "#dc3545", "deleteBtn"),
            ("打印", None, "#6c757d", "printBtn")
        ]
        
        for text, callback, color, var_name in secondary_buttons:
            btn = QPushButton(text)
            setattr(self, var_name, btn)  # 保存按钮引用
            btn.setFixedWidth(100)
            btn.setFont(QFont("Microsoft YaHei", 12))
            if callback:
                btn.clicked.connect(callback)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-size: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: white;
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color, 0.3)};
                    border-color: {self.darken_color(color, 0.3)};
                }}
            """)
            btnLayout.addWidget(btn)
        
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 数据表格 - 基线对齐优化
        self.table = QTableWidget(0, 10)
        self.table.setShowGrid(True)  # 显示网格线
        self.table.setHorizontalHeaderLabels(["扫码编号", "QRC No.", "扫码时间", "姓名", "手机号", "微信号", "国家", "省份", "城市", "区/县"])
        
        # 表格基线对齐设置：确保与页面左右边界完全对齐
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setFixedHeight(40)
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                font-size: 17px;
                font-weight: bold;
                background-color: #f8f9fa;
                border: none;
                border-bottom: 2px solid #dee2e6;
                padding: 8px 4px;
            }
        """)
        
        # 确保表格宽度与页面基线对齐
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 设置智能列宽 - 根据内容特点优化分配界面空间
        column_widths = [
            140,  # 扫码编号 - 加宽，容纳完整编号
            220,  # QRC No. - 显著加宽，产品编号较长
            180,  # 扫码时间 - 加宽，完整显示日期时间
            100,  # 姓名 - 适度加宽，中文姓名显示
            160,  # 手机号 - 加宽，容纳(+86)格式
            140,  # 微信号 - 加宽，微信号较长
            80,   # 国家 - 保持紧凑，通常是"中国"
            120,  # 省份 - 加宽，容纳完整省份名称
            120,  # 城市 - 加宽，容纳完整城市名称
            130   # 区/县 - 显著加宽，充分利用右侧空间
        ]
        
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)
        
        # 强制刷新列宽设置，确保生效
        self.table.resizeColumnsToContents()
        for i, width in enumerate(column_widths):
            self.table.setColumnWidth(i, width)
        
        # 设置垂直表头
        self.table.verticalHeader().setFixedWidth(60)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列，删除重叠框框
        
        # 设置垂直表头样式
        self.table.verticalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-right: 1px solid #dee2e6;
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                text-align: center;
            }
        """)
        
        # 设置左上角的"序号"标题
        self.setup_corner_header()
        

        # 设置表格主体样式 - 现代化设计
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
                color: #333;
            }
        """)
        
        # 启用斑马纹效果
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)  # 显示网格线
        
        layout.addWidget(self.table)

        # 初始加载全部数据
        self.load_data_from_db()