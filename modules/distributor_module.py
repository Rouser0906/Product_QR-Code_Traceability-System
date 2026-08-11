from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
import os
from utils.permissions import has_permission
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')

class DistributorModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("经销商信息管理")
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
        self.addBtn.clicked.connect(self.add_distributor)
        btnLayout.addWidget(self.addBtn)

        self.delBtn = QPushButton("删除")
        self.delBtn.setFixedWidth(100)
        self.delBtn.setFont(QFont("Microsoft YaHei", 12))
        self.delBtn.clicked.connect(self.delete_distributor)
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
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["经销商名称", "联系人", "联系电话", "地址", "合作时间", "状态", "备注", "操作"])
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
        can_view = has_permission(user, "distributor.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "distributor.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增经销商的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "distributor.delete")
        self.delBtn.setEnabled(can_delete)
        if not can_delete:
            self.delBtn.setToolTip("您没有删除经销商的权限")
            
        # 检查下载权限
        can_download = has_permission(user, "distributor.download")
        self.downloadBtn.setEnabled(can_download)
        if not can_download:
            self.downloadBtn.setToolTip("您没有下载经销商信息的权限")
            
        # 检查打印权限
        can_print = has_permission(user, "distributor.print")
        self.printBtn.setEnabled(can_print)
        if not can_print:
            self.printBtn.setToolTip("您没有打印经销商信息的权限")
            
        print(f"经销商模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 删除: {can_delete}, 下载: {can_download}, 打印: {can_print}")

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
            cursor.execute("SELECT name, contact_person, phone, address, cooperation_date, status, remark FROM distributors ORDER BY id")
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
            import traceback
            print(f"[ERROR] 刷新经销商表格出错: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "错误", f"刷新经销商表格出错: {e}")
        finally:
            conn.close()

    def add_distributor(self):
        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        class AddDistributorDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("新增经销商信息")
                self.resize(400, 300)
                layout = QFormLayout(self)
                self.name_edit = QLineEdit()
                self.contact_person_edit = QLineEdit()
                self.phone_edit = QLineEdit()
                self.address_edit = QLineEdit()
                self.cooperation_date_edit = QLineEdit()
                self.status_edit = QLineEdit()
                self.remark_edit = QLineEdit()
                layout.addRow("经销商名称", self.name_edit)
                layout.addRow("联系人", self.contact_person_edit)
                layout.addRow("联系电话", self.phone_edit)
                layout.addRow("地址", self.address_edit)
                layout.addRow("合作时间", self.cooperation_date_edit)
                layout.addRow("状态", self.status_edit)
                layout.addRow("备注", self.remark_edit)
                self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
                self.button_box.accepted.connect(self.accept)
                self.button_box.rejected.connect(self.reject)
                layout.addRow(self.button_box)
            def get_data(self):
                return {
                    'name': self.name_edit.text(),
                    'contact_person': self.contact_person_edit.text(),
                    'phone': self.phone_edit.text(),
                    'address': self.address_edit.text(),
                    'cooperation_date': self.cooperation_date_edit.text(),
                    'status': self.status_edit.text(),
                    'remark': self.remark_edit.text()
                }
        dialog = AddDistributorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            try:
                conn = self.get_conn()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO distributors (name, contact_person, phone, address, cooperation_date, status, remark) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (data['name'], data['contact_person'], data['phone'], data['address'], data['cooperation_date'], data['status'], data['remark'])
                )
                conn.commit()
                QMessageBox.information(self, "成功", "经销商添加成功！")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "失败", "经销商名称已存在，不能重复添加！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"添加经销商失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def delete_distributor(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的经销商！")
            return
        name = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除经销商：{name} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = self.get_conn()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute("DELETE FROM distributors WHERE name=?", (name,))
                conn.commit()
                QMessageBox.information(self, "成功", "经销商删除成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"删除经销商失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def edit_distributor(self, row_data):
        class EditDistributorDialog(QDialog):
            def __init__(self, data, parent=None):
                super().__init__(parent)
                self.setWindowTitle("编辑经销商信息")
                self.resize(400, 300)
                layout = QFormLayout(self)
                self.name_edit = QLineEdit(data[0]); self.name_edit.setObjectName("DialogEdit")
                self.contact_person_edit = QLineEdit(data[1]); self.contact_person_edit.setObjectName("DialogEdit")
                self.phone_edit = QLineEdit(data[2]); self.phone_edit.setObjectName("DialogEdit")
                self.address_edit = QLineEdit(data[3]); self.address_edit.setObjectName("DialogEdit")
                self.cooperation_date_edit = QLineEdit(data[4]); self.cooperation_date_edit.setObjectName("DialogEdit")
                self.status_edit = QLineEdit(data[5]); self.status_edit.setObjectName("DialogEdit")
                self.remark_edit = QLineEdit(data[6]); self.remark_edit.setObjectName("DialogEdit")
                layout.addRow("经销商名称", self.name_edit)
                layout.addRow("联系人", self.contact_person_edit)
                layout.addRow("联系电话", self.phone_edit)
                layout.addRow("地址", self.address_edit)
                layout.addRow("合作时间", self.cooperation_date_edit)
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
                return [
                    self.name_edit.text(),
                    self.contact_person_edit.text(),
                    self.phone_edit.text(),
                    self.address_edit.text(),
                    self.cooperation_date_edit.text(),
                    self.status_edit.text(),
                    self.remark_edit.text()
                ]
        dialog = EditDistributorDialog(row_data, self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            try:
                conn = self.get_conn()
                if not conn:
                    return
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE distributors SET name=?, contact_person=?, phone=?, address=?, cooperation_date=?, status=?, remark=? WHERE name=?""",
                    (*new_data, row_data[0])
                )
                conn.commit()
                QMessageBox.information(self, "成功", "经销商信息已更新！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"更新失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 7:  # 操作列
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                row_data = item.data(Qt.UserRole)
                self.edit_distributor(row_data)
