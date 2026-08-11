from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QHBoxLayout, QTableWidget, QTableWidgetItem, 
                           QHeaderView, QMessageBox, QInputDialog, QDialog, 
                           QFormLayout, QLineEdit, QDialogButtonBox, QCheckBox)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sys
import os

# 导入安全模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
from modules.base_manager import BaseManager
from utils.logger import log_info, log_error, log_warning, log_user_action
from utils.validator import data_validator
from utils.permissions import has_permission

class CompanyModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.base_manager = BaseManager(
            title="公司名称管理",
            columns=["公司名称", "公司英文名", "公司地址", "公司网址", "前台电话", "客服电话", "操作"],
            table_name="companies",
            entity_type="company"
        )
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("公司名称管理")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 操作按钮
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)
        
        self.addBtn = QPushButton("新增")
        self.addBtn.setFixedWidth(100)
        self.addBtn.setFont(QFont("Microsoft YaHei", 12))
        self.addBtn.clicked.connect(self.add_company)
        btnLayout.addWidget(self.addBtn)

        self.delBtn = QPushButton("删除")
        self.delBtn.setFixedWidth(100)
        self.delBtn.setFont(QFont("Microsoft YaHei", 12))
        self.delBtn.clicked.connect(self.delete_company)
        btnLayout.addWidget(self.delBtn)

        self.refreshBtn = QPushButton("刷新")
        self.refreshBtn.setFixedWidth(100)
        self.refreshBtn.setFont(QFont("Microsoft YaHei", 12))
        self.refreshBtn.clicked.connect(self.refresh_table)
        btnLayout.addWidget(self.refreshBtn)

        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 搜索功能
        searchLayout = QHBoxLayout()
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("搜索公司名称...")
        self.searchEdit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.searchEdit.textChanged.connect(self.search_companies)
        searchLayout.addWidget(self.searchEdit)
        
        self.searchBtn = QPushButton("搜索")
        self.searchBtn.clicked.connect(self.search_companies)
        searchLayout.addWidget(self.searchBtn)
        layout.addLayout(searchLayout)

        # 数据表格
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "公司名称", "公司英文名", "公司地址", "公司网址", "前台电话", "客服电话", "操作"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        # 连接单元格点击事件
        self.table.cellClicked.connect(self.on_table_cell_clicked)
        self.table.setAlternatingRowColors(False)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                border: none;
                border-bottom: 1px solid #f0f0f0;
                padding: 8px 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 2px solid #dee2e6;
                padding: 8px 4px;
                font-weight: bold;
            }
        """)
        self.table.horizontalHeader().setFixedHeight(40)
        self.table.verticalHeader().setVisible(False)  # 隐藏序号列，删除重叠框框
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        self.refresh_table()

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "company.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "company.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增公司的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "company.delete")
        self.delBtn.setEnabled(can_delete)
        if not can_delete:
            self.delBtn.setToolTip("您没有删除公司的权限")
            
        print(f"公司模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 删除: {can_delete}")

    def refresh_table(self):
        """刷新表格数据"""
        try:
            companies = self.base_manager.get_all_data()
            self.update_table_display(companies)
        except Exception as e:
            log_error("刷新公司表格失败", exception=e)
            QMessageBox.critical(self, "错误", f"刷新公司表格出错: {e}")

    def update_table_display(self, companies):
        """更新表格显示"""
        self.table.setRowCount(len(companies))
        
        for row_idx, company in enumerate(companies):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(company.get('name', ''))))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(company.get('english_name', ''))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(company.get('address', ''))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(company.get('website', ''))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(company.get('front_phone', ''))))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(company.get('service_phone', ''))))
            
            # 创建可点击的编辑链接（直接显示在单元格内，避免按钮框重叠）
            edit_item = QTableWidgetItem("编辑")
            edit_item.setFlags(Qt.ItemIsEnabled)  # 保持可点击状态
            edit_item.setData(Qt.UserRole, company['id'])  # 存储公司ID
            edit_item.setForeground(QColor("#1976d2"))     # 蓝色文字，类似链接
            edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
            edit_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 6, edit_item)

    def add_company(self):
        """添加公司"""
        dialog = EditCompanyDialog({}, self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            
            # 使用安全的基础管理器添加
            result = self.base_manager.add_item(new_data)
            
            if result['success']:
                QMessageBox.information(self, "成功", "公司添加成功！")
                log_user_action("admin", "ADD_COMPANY", details=new_data)
                self.refresh_table()
            else:
                error_msg = '\n'.join([f"{k}: {v}" for k, v in result['errors'].items()])
                QMessageBox.warning(self, "失败", f"添加公司失败:\n{error_msg}")

    def delete_company(self):
        """删除公司"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选中要删除的公司！")
            return
            
        company_id = None
        for company in self.base_manager.get_all_data():
            if company['name'] == self.table.item(row, 0).text():
                company_id = company['id']
                break
        
        if not company_id:
            return
            
        name = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除公司：{name} 吗？", 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            result = self.base_manager.remove_item(company_id)
            if result['success']:
                QMessageBox.information(self, "成功", "公司删除成功！")
                log_user_action("admin", "DELETE_COMPANY", resource=name)
                self.refresh_table()
            else:
                QMessageBox.warning(self, "失败", f"删除公司失败: {result['errors']['database']}")

    def search_companies(self):
        """搜索公司"""
        search_term = self.searchEdit.text().strip()
        if not search_term:
            self.refresh_table()
            return
            
        companies = self.base_manager.search_items(search_term, ['name', 'english_name'])
        self.update_table_display(companies)

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 6:  # 操作列（第7列）
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                company_id = item.data(Qt.UserRole)
                if company_id:
                    self.edit_company(company_id)

    def edit_company(self, company_id):
        """编辑公司"""
        company = self.base_manager.get_item_by_id(company_id)
        if not company:
            QMessageBox.warning(self, "错误", "未找到公司数据")
            return

        dialog = EditCompanyDialog(company, self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            
            result = self.base_manager.update_item(company_id, new_data)
            
            if result['success']:
                QMessageBox.information(self, "成功", "公司信息已更新！")
                log_user_action("admin", "UPDATE_COMPANY", resource=company['name'], details=new_data)
                self.refresh_table()
            else:
                error_msg = '\n'.join([f"{k}: {v}" for k, v in result['errors'].items()])
                QMessageBox.warning(self, "失败", f"编辑公司失败:\n{error_msg}")

class EditCompanyDialog(QDialog):
    def __init__(self, company_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑公司信息")
        self.resize(450, 400)
        
        layout = QFormLayout(self)
        
        # 创建输入控件
        self.name_edit = QLineEdit(str(company_data.get('name', '')))
        self.name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        
        self.english_name_edit = QLineEdit(str(company_data.get('english_name', '')))
        self.english_name_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        
        self.address_edit = QLineEdit(str(company_data.get('address', '')))
        self.address_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        
        self.website_edit = QLineEdit(str(company_data.get('website', '')))
        self.website_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        
        self.front_phone_edit = QLineEdit(str(company_data.get('front_phone', '')))
        self.front_phone_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        
        self.service_phone_edit = QLineEdit(str(company_data.get('service_phone', '')))
        self.service_phone_edit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        
        # 添加表单字段
        layout.addRow("公司名称*", self.name_edit)
        layout.addRow("公司英文名", self.english_name_edit)
        layout.addRow("公司地址", self.address_edit)
        layout.addRow("公司网址", self.website_edit)
        layout.addRow("前台电话", self.front_phone_edit)
        layout.addRow("客服电话", self.service_phone_edit)
        
        # 添加必填提示
        required_label = QLabel("* 为必填项")
        required_label.setStyleSheet("color: #d32f2f; font-size: 12px;")
        layout.addRow(required_label)
        
        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    
    def validate_and_accept(self):
        """验证输入并确认"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "公司名称不能为空！")
            return False
            
        # 验证电话号码
        front_phone = self.front_phone_edit.text().strip()
        service_phone = self.service_phone_edit.text().strip()
        
        if front_phone:
            result = data_validator.validate_phone_number(front_phone)
            if not result['valid']:
                QMessageBox.warning(self, "警告", f"前台电话格式不正确: {result['errors'][0]}")
                return False
        
        if service_phone:
            result = data_validator.validate_phone_number(service_phone)
            if not result['valid']:
                QMessageBox.warning(self, "警告", f"客服电话格式不正确: {result['errors'][0]}")
                return False
        
        # 验证网址
        website = self.website_edit.text().strip()
        if website and not website.startswith(('http://', 'https://')):
            self.website_edit.setText('http://' + website)
        
        self.accept()
    
    def get_data(self):
        """获取表单数据"""
        return {
            'name': self.name_edit.text().strip(),
            'english_name': self.english_name_edit.text().strip(),
            'address': self.address_edit.text().strip(),
            'website': self.website_edit.text().strip(),
            'front_phone': self.front_phone_edit.text().strip(),
            'service_phone': self.service_phone_edit.text().strip()
        }