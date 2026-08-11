from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
import os
from utils.permissions import has_permission
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')

class ProductSpecModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("产品规格管理")
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
        self.addBtn.clicked.connect(self.add_spec)
        btnLayout.addWidget(self.addBtn)

        self.delBtn = QPushButton("删除")
        self.delBtn.setFixedWidth(100)
        self.delBtn.setFont(QFont("Microsoft YaHei", 12))
        self.delBtn.clicked.connect(self.delete_spec)
        btnLayout.addWidget(self.delBtn)

        # 下载和打印按钮
        self.downloadBtn = QPushButton("下载")
        self.downloadBtn.setFixedWidth(100)
        self.downloadBtn.setFont(QFont("Microsoft YaHei", 12))
        btnLayout.addWidget(self.downloadBtn)
        
        self.printBtn = QPushButton("打印")
        self.printBtn.setFixedWidth(100)
        self.printBtn.setFont(QFont("Microsoft YaHei", 12))
        btnLayout.addWidget(self.printBtn)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 数据表格
        self.table = QTableWidget(0, 3)
        self.table.setShowGrid(True)  # 显示网格线
        self.table.setHorizontalHeaderLabels(["产品规格", "自定义", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 美化表头和序号列
        self.table.horizontalHeader().setFixedHeight(40)
        self.table.horizontalHeader().setStyleSheet("font-size: 17px; font-weight: bold;")
        self.table.verticalHeader().setFixedWidth(48)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列，删除重叠框框
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        layout.addWidget(self.table)
        self.refresh_table()

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "product.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "product.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增产品规格的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "product.delete")
        self.delBtn.setEnabled(can_delete)
        if not can_delete:
            self.delBtn.setToolTip("您没有删除产品规格的权限")
            
        # 检查下载权限
        can_download = has_permission(user, "product.download")
        self.downloadBtn.setEnabled(can_download)
        if not can_download:
            self.downloadBtn.setToolTip("您没有下载产品规格的权限")
            
        # 检查打印权限
        can_print = has_permission(user, "product.print")
        self.printBtn.setEnabled(can_print)
        if not can_print:
            self.printBtn.setToolTip("您没有打印产品规格的权限")
            
        print(f"产品规格模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 删除: {can_delete}, 下载: {can_download}, 打印: {can_print}")

    def get_conn(self):
        return sqlite3.connect(DB_PATH)

    def refresh_table(self):
        try:
            conn = self.get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT name, IFNULL(remark, '') FROM product_specs ORDER BY id")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value) if value else ""))
                # 新增编辑按钮（替换为链接样式）
                edit_item = QTableWidgetItem("编辑")
                edit_item.setFlags(Qt.ItemIsEnabled)
                edit_item.setData(Qt.UserRole, row)
                edit_item.setForeground(QColor("#1976d2"))
                edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
                edit_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 2, edit_item)
            conn.close()
        except Exception as e:
            import traceback
            print(f"[ERROR] 刷新产品规格表格出错: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新产品规格表格出错: {e}")

    def add_spec(self):
        dialog = EditProductSpecDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = self.get_conn()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO product_specs (name, remark) VALUES (?, ?)", (data['name'], data['remark']))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "成功", "产品规格添加成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"添加产品规格失败: {e}")
            self.refresh_table()

    def delete_spec(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的产品规格！")
            return
        name = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除产品规格：{name} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = self.get_conn()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM product_specs WHERE name=?", (name,))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "成功", "产品规格删除成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"删除产品规格失败: {e}")
            self.refresh_table()

    def edit_spec(self, row_data):
        dialog = EditProductSpecDialog(parent=self)
        dialog.setWindowTitle("编辑产品规格")
        dialog.name_edit.setText(row_data[0])
        dialog.remark_edit.setText(row_data[1])
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = self.get_conn()
                cursor = conn.cursor()
                cursor.execute("UPDATE product_specs SET name=?, remark=? WHERE name=?", (data['name'], data['remark'], row_data[0]))
                conn.commit()
                conn.close()
                QMessageBox.information(self, "成功", "产品规格修改成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"修改产品规格失败: {e}")
            self.refresh_table()

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 2:  # 操作列
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                row_data = item.data(Qt.UserRole)
                self.edit_spec(row_data)

class EditProductSpecDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增产品规格")
        self.resize(300, 120)
        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.remark_edit = QLineEdit()
        self.remark_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        layout.addRow("产品规格", self.name_edit)
        layout.addRow("自定义", self.remark_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    def get_data(self):
        return {'name': self.name_edit.text(), 'remark': self.remark_edit.text()}
