from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QDateEdit
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
from datetime import datetime
import os
from utils.permissions import has_permission
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')

class StaffModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("员工信息管理")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 操作按钮区域
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(12)
        
        # 按钮样式
        button_style = """
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
                min-width: 100px;
                min-height: 36px;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                background-color: #f8fff8;
                color: #2E7D32;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #e8f5e8;
                border-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #c8e6c9;
            }
        """
        
        # 新增员工
        self.addBtn = QPushButton("➕ 新增员工")
        self.addBtn.setStyleSheet(button_style)
        self.addBtn.clicked.connect(self.add_staff)
        btnLayout.addWidget(self.addBtn)
        
        # 修改员工
        self.editBtn = QPushButton("✏️ 修改员工")
        self.editBtn.setStyleSheet(button_style)
        self.editBtn.clicked.connect(self.edit_staff)
        btnLayout.addWidget(self.editBtn)

        # 删除员工
        self.delBtn = QPushButton("🗑️ 删除员工")
        self.delBtn.setStyleSheet(button_style.replace("#4CAF50", "#f44336").replace("#2E7D32", "#c62828").replace("#f8fff8", "#fff8f8").replace("#e8f5e8", "#ffebee").replace("#c8e6c9", "#ffcdd2").replace("#45a049", "#e53935"))
        self.delBtn.clicked.connect(self.delete_staff)
        btnLayout.addWidget(self.delBtn)
        
        # 分隔线
        btnLayout.addWidget(QLabel("|"))
        
        # 刷新数据
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.setStyleSheet(button_style.replace("#4CAF50", "#2196F3").replace("#2E7D32", "#1565C0").replace("#f8fff8", "#f8fcff").replace("#e8f5e8", "#e3f2fd").replace("#c8e6c9", "#bbdefb").replace("#45a049", "#1976D2"))
        refresh_btn.clicked.connect(self.refresh_table)
        btnLayout.addWidget(refresh_btn)
        
        # 导出数据
        export_btn = QPushButton("📊 导出数据")
        export_btn.setStyleSheet(button_style.replace("#4CAF50", "#FF9800").replace("#2E7D32", "#E65100").replace("#f8fff8", "#fffaf8").replace("#e8f5e8", "#fff3e0").replace("#c8e6c9", "#ffe0b2").replace("#45a049", "#F57C00"))
        export_btn.clicked.connect(self.export_staff)
        btnLayout.addWidget(export_btn)
        
        # 导入数据
        import_btn = QPushButton("📥 导入数据")
        import_btn.setStyleSheet(button_style.replace("#4CAF50", "#9C27B0").replace("#2E7D32", "#6A1B9A").replace("#f8fff8", "#fdf8ff").replace("#e8f5e8", "#f3e5f5").replace("#c8e6c9", "#e1bee7").replace("#45a049", "#8E24AA"))
        import_btn.clicked.connect(self.import_staff)
        btnLayout.addWidget(import_btn)
        
        # 打印报表
        print_btn = QPushButton("🖨️ 打印报表")
        print_btn.setStyleSheet(button_style.replace("#4CAF50", "#795548").replace("#2E7D32", "#5D4037").replace("#f8fff8", "#fafafa").replace("#e8f5e8", "#efebe9").replace("#c8e6c9", "#d7ccc8").replace("#45a049", "#6D4C41"))
        print_btn.clicked.connect(self.print_staff)
        btnLayout.addWidget(print_btn)
        
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 数据表格
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["员工姓名", "工号", "部门名称", "联系电话", "入职日期", "操作"])
        
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
        
        # 表格属性设置
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setShowGrid(True)  # 显示网格线
        
        # 表头设置 - 充分利用空间
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # 自动拉伸填满
        header.setStretchLastSection(True)
        header.setFixedHeight(45)
        
        # 垂直表头
        v_header = self.table.verticalHeader()
        v_header.setVisible(False)  # 隐藏行号
        v_header.setDefaultSectionSize(50)
        
        # 连接事件
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        
        layout.addWidget(self.table)

        self.refresh_table()

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "staff.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "staff.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增员工的权限")
            
        # 检查修改权限  
        can_update = has_permission(user, "staff.update")
        self.editBtn.setEnabled(can_update)
        if not can_update:
            self.editBtn.setToolTip("您没有修改员工的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "staff.delete")
        self.delBtn.setEnabled(can_delete)
        if not can_delete:
            self.delBtn.setToolTip("您没有删除员工的权限")
            
        print(f"员工模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 修改: {can_update}, 删除: {can_delete}")

    def get_conn(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            # 设置WAL模式以提高并发性能
            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            conn.execute('PRAGMA cache_size=10000;')
            conn.execute('PRAGMA temp_store=MEMORY;')
            return conn
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"无法连接数据库: {e}")
            return None

    def refresh_table(self):
        conn = self.get_conn()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.name, s.employee_id, d.name as department_name, s.phone, s.created_at 
                FROM staff s 
                LEFT JOIN departments d ON s.department_id = d.id 
                ORDER BY s.id
            """)
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row[1]) if row[1] else ""))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row[2]) if row[2] else ""))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(row[3]) if row[3] else ""))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(row[4]) if row[4] else ""))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(row[5]) if row[5] else ""))
                
                # 创建可点击的编辑链接（直接显示在单元格内，避免按钮框重叠）
                edit_item = QTableWidgetItem("编辑")
                edit_item.setFlags(Qt.ItemIsEnabled)  # 保持可点击状态
                edit_item.setData(Qt.UserRole, row[0])  # 存储员工ID
                edit_item.setForeground(QColor("#1976d2"))     # 蓝色文字，类似链接
                edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
                edit_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 5, edit_item)
        except Exception as e:
            import traceback
            print(f"[ERROR] 刷新员工表格出错: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新员工表格出错: {e}")
        finally:
            conn.close()

    def add_staff(self):
        dialog = EditStaffDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = self.get_conn()
                if not conn:
                    return
                cursor = conn.cursor()
                # 校验部门ID是否存在
                cursor.execute("SELECT id FROM departments WHERE id=?", (data['department_id'],))
                dept_row = cursor.fetchone()
                if not dept_row:
                    QMessageBox.warning(self, "失败", "部门ID不存在，无法添加员工！")
                    return
                cursor.execute("INSERT INTO staff (name, employee_id, department_id, phone, created_at) VALUES (?, ?, ?, ?, ?)",
                               (data['name'], data['employee_id'], data['department_id'], data['phone'], data['created_at']))
                conn.commit()
                QMessageBox.information(self, "成功", "员工添加成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"添加员工失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def delete_staff(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的员工！")
            return
        name = self.table.item(row, 0).text()
        employee_id = self.table.item(row, 1).text()
        
        # 获取员工ID
        try:
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM staff WHERE name=? AND employee_id=?", (name, employee_id))
            staff_row = cursor.fetchone()
            if staff_row:
                staff_id = staff_row[0]
                reply = QMessageBox.question(self, "确认删除", f"确定要删除员工：{name}({employee_id}) 吗？", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    cursor.execute("DELETE FROM staff WHERE id=?", (staff_id,))
                    conn.commit()
                    QMessageBox.information(self, "成功", "员工删除成功！")
            conn.close()
            self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "失败", f"删除员工失败: {e}")

    def edit_staff(self, staff_id):
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        conn = self.get_conn()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name, employee_id, department_id, phone, created_at FROM staff WHERE id=?", (staff_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "错误", "未找到员工数据")
                return
            class EditStaffDialog(QDialog):
                def __init__(self, staff_data, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("编辑员工信息")
                    self.resize(400, 250)
                    layout = QFormLayout(self)
                    self.name_edit = QLineEdit(staff_data['name'])
                    self.name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
                    self.employee_id_edit = QLineEdit(staff_data['employee_id'])
                    self.employee_id_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
                    self.department_id_edit = QLineEdit(str(staff_data['department_id']))
                    self.department_id_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
                    self.phone_edit = QLineEdit(staff_data['phone'])
                    self.phone_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
                    self.created_at_edit = QLineEdit(staff_data['created_at'])
                    self.created_at_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
                    layout.addRow("员工姓名", self.name_edit)
                    layout.addRow("工号", self.employee_id_edit)
                    layout.addRow("部门ID", self.department_id_edit)
                    layout.addRow("联系电话", self.phone_edit)
                    layout.addRow("入职日期", self.created_at_edit)
                    self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                    self.button_box.accepted.connect(self.accept)
                    self.button_box.rejected.connect(self.reject)
                    layout.addRow(self.button_box)
                def get_data(self):
                    return {
                        'name': self.name_edit.text(),
                        'employee_id': self.employee_id_edit.text(),
                        'department_id': self.department_id_edit.text(),
                        'phone': self.phone_edit.text(),
                        'created_at': self.created_at_edit.text()
                    }
            staff_data = {
                'name': row[0] or "",
                'employee_id': row[1] or "",
                'department_id': row[2] or "",
                'phone': row[3] or "",
                'created_at': row[4] or ""
            }
            dialog = EditStaffDialog(staff_data, self)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                # 校验部门ID是否存在
                cursor.execute("SELECT id FROM departments WHERE id=?", (new_data['department_id'],))
                dept_row = cursor.fetchone()
                if not dept_row:
                    QMessageBox.warning(self, "失败", "部门ID不存在，无法修改员工！")
                    return
                cursor.execute(
                    "UPDATE staff SET name=?, employee_id=?, department_id=?, phone=?, created_at=? WHERE id=?",
                    (new_data['name'], new_data['employee_id'], new_data['department_id'], new_data['phone'], new_data['created_at'], staff_id)
                )
                conn.commit()
                QMessageBox.information(self, "成功", "员工信息已更新！")
                self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "失败", f"编辑员工失败: {e}")
        finally:
            conn.close()

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 5:  # 操作列（第6列）
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                staff_id = item.data(Qt.UserRole)
                if staff_id:
                    self.edit_staff(staff_id)
    
    def export_staff(self):
        """导出员工数据"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存员工数据", f"员工数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                "CSV文件 (*.csv)"
            )
            
            if filename:
                conn = self.get_conn()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT s.name, s.employee_id, d.name, s.phone, s.position, s.created_at
                    FROM staff s
                    LEFT JOIN departments d ON s.department_id = d.id
                    ORDER BY s.created_at DESC
                """)
                
                rows = cursor.fetchall()
                conn.close()
                
                import csv
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow(["员工姓名", "工号", "部门名称", "联系电话", "职位", "入职日期"])
                    for row in rows:
                        writer.writerow(row)
                
                QMessageBox.information(self, "导出成功", f"员工数据已导出到:\n{filename}")
        
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出员工数据失败:\n{str(e)}")
    
    def import_staff(self):
        """导入员工数据"""
        from PyQt5.QtWidgets import QFileDialog
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "CSV文件 (*.csv);;Excel文件 (*.xlsx)"
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'r', encoding='utf-8-sig') as file:
                    reader = csv.DictReader(file)
                    
                    conn = self.get_conn()
                    cursor = conn.cursor()
                    
                    imported_count = 0
                    for row in reader:
                        # 获取部门ID
                        dept_name = row.get('部门名称', '')
                        cursor.execute("SELECT id FROM departments WHERE name = ?", (dept_name,))
                        dept_result = cursor.fetchone()
                        dept_id = dept_result[0] if dept_result else None
                        
                        cursor.execute("""
                            INSERT INTO staff (name, employee_id, department_id, phone, position, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('员工姓名', ''),
                            row.get('工号', ''),
                            dept_id,
                            row.get('联系电话', ''),
                            row.get('职位', ''),
                            row.get('入职日期', datetime.now().strftime('%Y-%m-%d'))
                        ))
                        imported_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(self, "导入成功", f"成功导入 {imported_count} 条员工记录")
                    self.refresh_table()
                    
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"导入员工数据失败:\n{str(e)}")
    
    def print_staff(self):
        """打印员工报表"""
        try:
            from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt5.QtGui import QPainter, QFont
            from PyQt5.QtCore import QRect
            
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                painter = QPainter(printer)
                
                # 设置字体
                font = QFont("Microsoft YaHei", 12)
                painter.setFont(font)
                
                # 打印标题
                title_font = QFont("Microsoft YaHei", 16, QFont.Bold)
                painter.setFont(title_font)
                painter.drawText(100, 100, "员工信息报表")
                
                # 打印表格数据
                y = 200
                painter.setFont(font)
                
                for row in range(self.table.rowCount()):
                    x = 100
                    for col in range(self.table.columnCount() - 1):  # 排除操作列
                        item = self.table.item(row, col)
                        if item:
                            painter.drawText(x, y, item.text())
                            x += 150
                    y += 30
                    
                    if y > 2800:  # 换页
                        printer.newPage()
                        y = 100
                
                painter.end()
                QMessageBox.information(self, "打印完成", "员工报表打印完成！")
                
        except Exception as e:
            QMessageBox.warning(self, "打印失败", f"打印员工报表失败:\n{str(e)}")

class EditStaffDialog(QDialog):
    def __init__(self, staff_data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑员工信息" if staff_data else "新增员工信息")
        self.resize(400, 250)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(staff_data['name'] if staff_data else "")
        self.name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.employee_id_edit = QLineEdit(staff_data['employee_id'] if staff_data else "")
        self.employee_id_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.department_id_edit = QLineEdit(str(staff_data['department_id']) if staff_data else "")
        self.department_id_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.phone_edit = QLineEdit(staff_data['phone'] if staff_data else "")
        self.phone_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.created_at_edit = QLineEdit(staff_data['created_at'] if staff_data else "")
        self.created_at_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        layout.addRow("员工姓名", self.name_edit)
        layout.addRow("工号", self.employee_id_edit)
        layout.addRow("部门ID", self.department_id_edit)
        layout.addRow("联系电话", self.phone_edit)
        layout.addRow("入职日期", self.created_at_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    def get_data(self):
        return {
            'name': self.name_edit.text(),
            'employee_id': self.employee_id_edit.text(),
            'department_id': self.department_id_edit.text(),
            'phone': self.phone_edit.text(),
            'created_at': self.created_at_edit.text()
        }
