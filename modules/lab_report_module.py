import sqlite3
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QMessageBox, QFormLayout, QDialogButtonBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import traceback
import os
from utils.permissions import has_permission
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'qr_system.db')

class LabReportModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()
        self.refresh_table()

    def get_conn(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", str(e))
            return None

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("实验检测报告")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)
        self.addBtn = QPushButton("新增")
        self.addBtn.setFixedWidth(100)
        self.addBtn.setFont(QFont("Microsoft YaHei", 12))
        self.addBtn.clicked.connect(self.add_report)
        btnLayout.addWidget(self.addBtn)

        self.delBtn = QPushButton("删除")
        self.delBtn.setFixedWidth(100)
        self.delBtn.setFont(QFont("Microsoft YaHei", 12))
        self.delBtn.clicked.connect(self.delete_report)
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

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["报告编号", "检测项目", "检测结果", "检测日期", "备注", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setFixedHeight(40)
        self.table.horizontalHeader().setStyleSheet("font-size: 17px; font-weight: bold;")
        self.table.verticalHeader().setFixedWidth(48)
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列，删除重叠框框
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        layout.addWidget(self.table)

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "lab_report.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "lab_report.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增实验检测报告的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "lab_report.delete")
        self.delBtn.setEnabled(can_delete)
        if not can_delete:
            self.delBtn.setToolTip("您没有删除实验检测报告的权限")
            
        # 检查下载权限
        can_download = has_permission(user, "lab_report.download")
        self.downloadBtn.setEnabled(can_download)
        if not can_download:
            self.downloadBtn.setToolTip("您没有下载实验检测报告的权限")
            
        # 检查打印权限
        can_print = has_permission(user, "lab_report.print")
        self.printBtn.setEnabled(can_print)
        if not can_print:
            self.printBtn.setToolTip("您没有打印实验检测报告的权限")
            
        print(f"实验检测报告模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 删除: {can_delete}, 下载: {can_download}, 打印: {can_print}")

    def refresh_table(self):
        conn = self.get_conn()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, report_no, item, result, test_date, remark FROM lab_reports ORDER BY id")
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx in range(1, 6):
                    self.table.setItem(row_idx, col_idx-1, QTableWidgetItem(str(row[col_idx]) if row[col_idx] else ""))
                # 新增编辑按钮（替换为链接样式）
                edit_item = QTableWidgetItem("编辑")
                edit_item.setFlags(Qt.ItemIsEnabled)
                edit_item.setData(Qt.UserRole, row[0])  # 存储report_id
                edit_item.setForeground(QColor("#1976d2"))
                edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
                edit_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 5, edit_item)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"刷新实验检测报告表格出错: {e}")
        finally:
            conn.close()

    def add_report(self):
        dialog = EditLabReportDialog({}, self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO lab_reports (report_no, item, result, test_date, remark) VALUES (?, ?, ?, ?, ?)",
                    (data['report_no'], data['item'], data['result'], data['test_date'], data['remark'])
                )
                conn.commit()
                QMessageBox.information(self, "成功", "实验检测报告添加成功！")
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "失败", "报告编号已存在，不能重复添加！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"添加实验检测报告失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def delete_report(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的报告！")
            return
        report_no = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", f"确定要删除报告：{report_no} 吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            conn = self.get_conn()
            if not conn:
                return
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM lab_reports WHERE report_no=?", (report_no,))
                conn.commit()
                QMessageBox.information(self, "成功", "报告删除成功！")
            except Exception as e:
                QMessageBox.warning(self, "失败", f"删除报告失败: {e}")
            finally:
                conn.close()
            self.refresh_table()

    def edit_report(self, report_id):
        conn = self.get_conn()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT report_no, item, result, test_date, remark FROM lab_reports WHERE id=?", (report_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.warning(self, "错误", "未找到报告数据")
                return
            report_data = {
                'report_no': row[0] or "",
                'item': row[1] or "",
                'result': row[2] or "",
                'test_date': row[3] or "",
                'remark': row[4] or ""
            }
            dialog = EditLabReportDialog(report_data, self)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_data()
                cursor.execute(
                    "UPDATE lab_reports SET report_no=?, item=?, result=?, test_date=?, remark=? WHERE id=?",
                    (new_data['report_no'], new_data['item'], new_data['result'], new_data['test_date'], new_data['remark'], report_id)
                )
                conn.commit()
                QMessageBox.information(self, "成功", "报告信息已更新！")
                self.refresh_table()
        except Exception as e:
            QMessageBox.warning(self, "失败", f"编辑报告失败: {e}")
        finally:
            conn.close()

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 5:  # 操作列
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                report_id = item.data(Qt.UserRole)
                self.edit_report(report_id)

class EditLabReportDialog(QDialog):
    def __init__(self, report_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑实验检测报告信息")
        self.resize(400, 250)
        layout = QFormLayout(self)
        self.report_no_edit = QLineEdit(report_data.get('report_no', ''))
        self.report_no_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.item_edit = QLineEdit(report_data.get('item', ''))
        self.item_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.result_edit = QLineEdit(report_data.get('result', ''))
        self.result_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.test_date_edit = QLineEdit(report_data.get('test_date', ''))
        self.test_date_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.remark_edit = QLineEdit(report_data.get('remark', ''))
        self.remark_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        layout.addRow("报告编号", self.report_no_edit)
        layout.addRow("检测项目", self.item_edit)
        layout.addRow("检测结果", self.result_edit)
        layout.addRow("检测日期", self.test_date_edit)
        layout.addRow("备注", self.remark_edit)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    def get_data(self):
        return {
            'report_no': self.report_no_edit.text(),
            'item': self.item_edit.text(),
            'result': self.result_edit.text(),
            'test_date': self.test_date_edit.text(),
            'remark': self.remark_edit.text()
        }
