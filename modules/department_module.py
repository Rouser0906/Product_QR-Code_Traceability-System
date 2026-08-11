from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
import os
from utils.permissions import has_permission
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')

class DepartmentModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("部门名称管理")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 操作按钮
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)
        self.addBtn = QPushButton("新增")
        self.addBtn.setFixedWidth(100)
        self.addBtn.setFont(QFont("Microsoft YaHei", 12))
        self.addBtn.clicked.connect(self.add_department)
        btnLayout.addWidget(self.addBtn)

        self.delBtn = QPushButton("删除")
        self.delBtn.setFixedWidth(100)
        self.delBtn.setFont(QFont("Microsoft YaHei", 12))
        self.delBtn.clicked.connect(self.delete_department)
        btnLayout.addWidget(self.delBtn)

        for text in ["下载", "打印"]:
            btn = QPushButton(text)
            btn.setFixedWidth(100)
            btn.setFont(QFont("Microsoft YaHei", 12))
            btnLayout.addWidget(btn)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 数据表格
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([
            "部门名称", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 连接单元格点击事件
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        # 美化表头和序号列
        self.table.horizontalHeader().setFixedHeight(40)
        self.table.horizontalHeader().setStyleSheet("font-size: 17px; font-weight: bold;")
        self.table.verticalHeader().setFixedWidth(48)
        self.table.verticalHeader().setDefaultSectionSize(60)  # 增大每一行高度为60
        # 设置序号列
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列，删除重叠框框
        # 在数据加载/刷新时自动设置序号
        layout.addWidget(self.table)

        self.refresh_table()

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "department.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "department.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增部门的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "department.delete")
        self.delBtn.setEnabled(can_delete)
        if not can_delete:
            self.delBtn.setToolTip("您没有删除部门的权限")
            
        print(f"部门模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 删除: {can_delete}")

    def get_conn(self):
        try:
            conn = sqlite3.connect(DB_PATH)
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
            cursor.execute("SELECT id, name FROM departments ORDER BY id")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row[1]) if row[1] else ""))
                
                # 创建可点击的编辑链接（直接显示在单元格内，避免按钮框重叠）
                edit_item = QTableWidgetItem("编辑")
                edit_item.setFlags(Qt.ItemIsEnabled)  # 保持可点击状态
                edit_item.setData(Qt.UserRole, row[0])  # 存储部门ID
                edit_item.setForeground(QColor("#1976d2"))     # 蓝色文字，类似链接
                edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
                edit_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 1, edit_item)
        except Exception as e:
            import traceback
            print(f"[ERROR] 刷新部门表格出错: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新部门表格出错: {e}")
        finally:
            conn.close()

    def add_department(self):
        # name, ok = QInputDialog.getText(self, "新增部门", "请输入部门名称：")
        dialog = AddDepartmentDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_name()
            if name.strip():
                conn = self.get_conn()
                if not conn:
                    return
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO departments (name) VALUES (?)", (name.strip(),))
                    conn.commit()
                    QMessageBox.information(self, "成功", "部门添加成功！")
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "失败", "部门名称已存在，不能重复添加！")
                except Exception as e:
                    QMessageBox.warning(self, "失败", f"添加部门失败: {e}")
                finally:
                    conn.close()
                self.refresh_table()

    def delete_department(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的部门！")
            return
        name = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除部门：{name} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            try:
                # 检查是否有关联员工等外键依赖（如有员工表）
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='staff'")
                if cursor.fetchone()[0]:
                    cursor.execute("SELECT COUNT(*) FROM staff WHERE department_id=(SELECT id FROM departments WHERE name=?)", (name,))
                    if cursor.fetchone()[0] > 0:
                        QMessageBox.warning(self, "失败", "该部门下还有员工，不能删除！")
                        return
                cursor.execute("DELETE FROM departments WHERE name=?", (name,))
                conn.commit()
                QMessageBox.information(self, "成功", "部门删除成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"删除部门失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def edit_department(self, dept_id):
        conn = self.get_conn()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM departments WHERE id=?", (dept_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "错误", "未找到部门数据")
                return
            dept_data = {'name': row[0] or ""}
            dialog = EditDepartmentDialog(dept_data, self)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                cursor.execute("UPDATE departments SET name=? WHERE id=?", (new_data['name'], dept_id))
                conn.commit()
                QMessageBox.information(self, "成功", "部门信息已更新！")
                self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "失败", f"编辑部门失败: {e}")
        finally:
            conn.close()

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 1:  # 操作列（第2列）
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                dept_id = item.data(Qt.UserRole)
                if dept_id:
                    self.edit_department(dept_id)

class EditDepartmentDialog(QDialog):
    def __init__(self, dept_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑部门信息")
        self.resize(300, 120)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit(dept_data['name'])
        self.name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        layout.addRow("部门名称", self.name_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    def get_data(self):
        return {'name': self.name_edit.text()}

class AddDepartmentDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增部门")
        self.resize(300, 120)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        layout.addRow("请输入部门名称:", self.name_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    def get_name(self):
        return self.name_edit.text()