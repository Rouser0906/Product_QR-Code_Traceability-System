from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt

class CustomModuleManager:
    """简化版自定义扩展管理器，不依赖数据库"""
    _instance = None
    
    def __init__(self):
        self.data = [
            ["数据备份", "自动备份系统数据", "启用", "2024-01-01", "定期备份系统重要数据"],
            ["报表生成", "自动生成统计报表", "启用", "2024-01-02", "生成各类统计和分析报表"],
            ["数据导入", "批量导入外部数据", "禁用", "2024-01-03", "支持Excel、CSV等格式导入"],
            ["数据导出", "批量导出系统数据", "启用", "2024-01-04", "支持多种格式导出"]
        ]
        CustomModuleManager._instance = self
    
    @staticmethod
    def get_instance():
        if CustomModuleManager._instance is None:
            CustomModuleManager()
        return CustomModuleManager._instance
    
    @staticmethod
    def get_extension_names():
        instance = CustomModuleManager.get_instance()
        if instance and hasattr(instance, 'data'):
            return [row[0] for row in instance.data]
        return []
    
    @staticmethod
    def add_extension(extension_data):
        instance = CustomModuleManager.get_instance()
        if instance and hasattr(instance, 'data'):
            extension_names = [row[0] for row in instance.data]
            if extension_data[0] not in extension_names:
                instance.data.append(extension_data)
                return True
        return False


class CustomModule(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.initUI()
        except Exception as e:
            # 避免初始化失败导致闪退
            import traceback
            print("CustomModule init error:", str(e))
            traceback.print_exc()
            
            # 创建简单错误显示界面
            layout = QVBoxLayout(self)
            error_label = QLabel(f"自定义扩展模块初始化失败\n错误: {str(e)}")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: red; font-size: 14px; padding: 20px;")
            layout.addWidget(error_label)

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("自定义扩展管理")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 操作按钮
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)
        for text in ["新增", "删除", "启用", "禁用"]:
            btn = QPushButton(text)
            btn.setFixedWidth(100)
            btn.setFont(QFont("Microsoft YaHei", 12))
            btnLayout.addWidget(btn)
        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 数据表格
        self.manager = CustomModuleManager.get_instance()
        data = self.manager.data
        
        self.table = QTableWidget(len(data), 6)
        self.table.setHorizontalHeaderLabels(["扩展名称", "功能描述", "状态", "创建时间", "备注", "操作"])
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
        
        # 填充表格数据
        for row_idx, row_data in enumerate(data):
            for col_idx, value in enumerate(row_data):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            # 创建可点击的编辑链接（直接显示在单元格内，避免按钮框重叠）
            edit_item = QTableWidgetItem("编辑")
            edit_item.setFlags(Qt.ItemIsEnabled)  # 保持可点击状态
            edit_item.setData(Qt.UserRole, row_idx + 1)  # 存储扩展ID
            edit_item.setForeground(QColor("#1976d2"))     # 蓝色文字，类似链接
            edit_item.setFont(QFont("Microsoft YaHei", 10, QFont.Medium))
            edit_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row_idx, 5, edit_item)
        
        layout.addWidget(self.table)

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        if column == 5:  # 操作列（第6列）
            item = self.table.item(row, column)
            if item and item.text() == "编辑":
                extension_id = item.data(Qt.UserRole)
                if extension_id:
                    self.edit_extension(extension_id)

    def edit_extension(self, extension_id):
        """编辑扩展"""
        try:
            # 获取扩展数据
            if 1 <= extension_id <= len(self.manager.data):
                extension_data = self.manager.data[extension_id - 1]
                extension_name = extension_data[0]
                extension_desc = extension_data[1]
                extension_status = extension_data[2]
                
                QMessageBox.information(self, "扩展详情", 
                    f"扩展名称: {extension_name}\n"
                    f"功能描述: {extension_desc}\n"
                    f"当前状态: {extension_status}\n\n"
                    f"编辑功能正在开发中...")
            else:
                QMessageBox.warning(self, "错误", "无效的扩展ID")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"编辑扩展时发生错误: {str(e)}")