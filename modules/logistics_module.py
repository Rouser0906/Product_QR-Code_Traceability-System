from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
import sqlite3
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import os
from utils.permissions import has_permission
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')

class LogisticsModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = {}
        self.initUI()
        self.refresh_table()

    def get_conn(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"无法连接数据库: {e}")
            return None

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("物流车牌号管理")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)
        self.addBtn = QPushButton("新增")
        self.addBtn.setFixedWidth(100)
        self.addBtn.setFont(QFont("Microsoft YaHei", 12))
        self.addBtn.clicked.connect(self.add_vehicle)
        btnLayout.addWidget(self.addBtn)

        self.delBtn = QPushButton("删除")
        self.delBtn.setFixedWidth(100)
        self.delBtn.setFont(QFont("Microsoft YaHei", 12))
        self.delBtn.clicked.connect(self.delete_vehicle)
        btnLayout.addWidget(self.delBtn)

        for text in ["下载", "打印"]:
            btn = QPushButton(text)
            btn.setFixedWidth(100)
            btn.setFont(QFont("Microsoft YaHei", 12))
            btnLayout.addWidget(btn)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["车牌号", "司机姓名", "联系电话", "车型", "载重量", "状态", "备注", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setFixedHeight(40)
        self.table.horizontalHeader().setStyleSheet("font-size: 17px; font-weight: bold;")
        self.table.verticalHeader().setFixedWidth(48)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列，删除重叠框框
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        layout.addWidget(self.table)

    def refresh_table(self):
        conn = self.get_conn()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT plate_number, driver_name, phone, vehicle_type, load_capacity, status, remark FROM logistics_vehicles ORDER BY id")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx in range(7):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(row[col_idx]) if row[col_idx] else ""))
                # 新增编辑按钮（替换为链接样式）
                edit_item = QTableWidgetItem("编辑")
                edit_item.setFlags(Qt.ItemIsEnabled)
                edit_item.setData(Qt.UserRole, row)
                edit_item.setForeground(QColor("#1976d2"))
                edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
                edit_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 7, edit_item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新物流车辆表格出错: {e}")
        finally:
            conn.close()

    def add_vehicle(self):
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        class AddVehicleDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("新增车辆信息")
                self.resize(400, 300)
                layout = QFormLayout(self)
                self.plate_number_edit = QLineEdit()
                self.driver_name_edit = QLineEdit()
                self.phone_edit = QLineEdit()
                self.vehicle_type_edit = QLineEdit()
                self.load_capacity_edit = QLineEdit()
                self.status_edit = QLineEdit()
                self.remark_edit = QLineEdit()
                layout.addRow("车牌号", self.plate_number_edit)
                layout.addRow("司机姓名", self.driver_name_edit)
                layout.addRow("联系电话", self.phone_edit)
                layout.addRow("车型", self.vehicle_type_edit)
                layout.addRow("载重量", self.load_capacity_edit)
                layout.addRow("状态", self.status_edit)
                layout.addRow("备注", self.remark_edit)
                self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                self.button_box.accepted.connect(self.accept)
                self.button_box.rejected.connect(self.reject)
                layout.addRow(self.button_box)
            def get_data(self):
                return {
                    'plate_number': self.plate_number_edit.text(),
                    'driver_name': self.driver_name_edit.text(),
                    'phone': self.phone_edit.text(),
                    'vehicle_type': self.vehicle_type_edit.text(),
                    'load_capacity': self.load_capacity_edit.text(),
                    'status': self.status_edit.text(),
                    'remark': self.remark_edit.text()
                }
        dialog = AddVehicleDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO logistics_vehicles (plate_number, driver_name, phone, vehicle_type, load_capacity, status, remark) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data['plate_number'], data['driver_name'], data['phone'], data['vehicle_type'], data['load_capacity'], data['status'], data['remark'])
                )
                conn.commit()
                QMessageBox.information(self, "成功", "车辆添加成功！")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "失败", "车牌号已存在，不能重复添加！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"添加车辆失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def delete_vehicle(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的车辆！")
            return
        plate_number = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除车辆：{plate_number} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM logistics_vehicles WHERE plate_number=?", (plate_number,))
                conn.commit()
                QMessageBox.information(self, "成功", "车辆删除成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"删除车辆失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def edit_vehicle(self, row_data):
        class EditVehicleDialog(QDialog):
            def __init__(self, vehicle_data, parent=None):
                super().__init__(parent)
                self.setWindowTitle("编辑车辆信息")
                self.resize(400, 300)
                layout = QFormLayout(self)
                self.plate_number_edit = QLineEdit(vehicle_data[0]); self.plate_number_edit.setObjectName("DialogEdit")
                self.driver_name_edit = QLineEdit(vehicle_data[1]); self.driver_name_edit.setObjectName("DialogEdit")
                self.phone_edit = QLineEdit(vehicle_data[2]); self.phone_edit.setObjectName("DialogEdit")
                self.vehicle_type_edit = QLineEdit(vehicle_data[3]); self.vehicle_type_edit.setObjectName("DialogEdit")
                self.load_capacity_edit = QLineEdit(vehicle_data[4]); self.load_capacity_edit.setObjectName("DialogEdit")
                self.status_edit = QLineEdit(vehicle_data[5]); self.status_edit.setObjectName("DialogEdit")
                self.remark_edit = QLineEdit(vehicle_data[6]); self.remark_edit.setObjectName("DialogEdit")
                layout.addRow("车牌号", self.plate_number_edit)
                layout.addRow("司机姓名", self.driver_name_edit)
                layout.addRow("联系电话", self.phone_edit)
                layout.addRow("车型", self.vehicle_type_edit)
                layout.addRow("载重量", self.load_capacity_edit)
                layout.addRow("状态", self.status_edit)
                layout.addRow("备注", self.remark_edit)
                self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                self.button_box.accepted.connect(self.accept)
                self.button_box.rejected.connect(self.reject)
                layout.addRow(self.button_box)
                # 专属QSS，确保输入框有蓝色圆角边框
                self.setStyleSheet("""
                    QLineEdit#DialogEdit {
                        border: 1.5px solid #1976d2;
                        border-radius: 6px;
                        padding: 4px 8px;
                        background: #fff;
                    }
                """)
            def get_data(self):
                return {
                    'plate_number': self.plate_number_edit.text(),
                    'driver_name': self.driver_name_edit.text(),
                    'phone': self.phone_edit.text(),
                    'vehicle_type': self.vehicle_type_edit.text(),
                    'load_capacity': self.load_capacity_edit.text(),
                    'status': self.status_edit.text(),
                    'remark': self.remark_edit.text()
                }
        dialog = EditVehicleDialog(row_data, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE logistics_vehicles SET plate_number=?, driver_name=?, phone=?, vehicle_type=?, load_capacity=?, status=?, remark=? WHERE plate_number=?",
                    (data['plate_number'], data['driver_name'], data['phone'], data['vehicle_type'], data['load_capacity'], data['status'], data['remark'], row_data[0])
                )
                conn.commit()
                QMessageBox.information(self, "成功", "车辆信息修改成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"修改车辆信息失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    # 权限应用钩子：由主窗口在模块加载后调用
    def apply_permissions(self, user):
        self.current_user = user or {}
        # 操作员允许新增/编辑；管理者/浏览者不允许；删除仅管理员
        can_create_or_update = has_permission(self.current_user, "logistics.create") or has_permission(self.current_user, "logistics.update")
        can_delete = has_permission(self.current_user, "logistics.delete")
        # 按权限禁用按钮（禁用比隐藏更直观）
        if hasattr(self, 'addBtn'):
            self.addBtn.setEnabled(bool(can_create_or_update))
        if hasattr(self, 'delBtn'):
            self.delBtn.setEnabled(bool(can_delete))

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 7:  # 操作列
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                # 校验编辑权限
                if not has_permission(self.current_user, "logistics.update"):
                    QMessageBox.warning(self, "权限不足", "您没有编辑车辆信息的权限。")
                    return
                row_data = item.data(Qt.UserRole)
                self.edit_vehicle(row_data)
