from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, 
                            QLineEdit, QMessageBox, QComboBox)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
import sqlite3
import os
import json
from datetime import datetime
from utils.permissions import has_permission

from utils.database_config import get_verified_database_path
DB_PATH = get_verified_database_path()

class AuthorizedUserManager(QWidget):
    _instance = None
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.columns = ["用户ID", "二维码", "登录方式", "手机号", "用户姓名", "登录时间", "IP地址", "位置", "状态"]
        
        # 初始化UI
        self.initUI()
        
        # 初始化数据库表
        self.init_auth_tables()
        
        # 加载数据
        self.load_authorized_users()
    
    def initUI(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("授权用户管理")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        
        # 创建表格
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        layout.addWidget(self.table)
        
        # 设置界面
        self.setup_ui()
    
    def init_auth_tables(self):
        """初始化授权用户表"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS authorized_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    qr_code TEXT NOT NULL,
                    login_type TEXT NOT NULL,
                    phone TEXT,
                    user_name TEXT,
                    wechat_openid TEXT,
                    wechat_nickname TEXT,
                    location_data TEXT,
                    device_info TEXT,
                    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    authorized_token TEXT,
                    expires_at DATETIME
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"初始化授权用户表失败: {e}")
    
    def setup_ui(self):
        """设置用户界面"""
        # 搜索筛选区域
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("搜索:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入手机号、姓名或二维码...")
        self.search_edit.textChanged.connect(self.filter_users)
        filter_layout.addWidget(self.search_edit)
        
        filter_layout.addWidget(QLabel("登录方式:"))
        self.login_type_combo = QComboBox()
        self.login_type_combo.addItems(["全部", "system", "phone", "wechat", "qq"])
        self.login_type_combo.currentTextChanged.connect(self.filter_users)
        filter_layout.addWidget(self.login_type_combo)
        
        # 插入到布局中
        self.layout().insertLayout(1, filter_layout)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
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
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
                border-color: #e0e0e0;
            }
        """
        
        # 新增用户按钮
        add_btn = QPushButton("➕ 新增用户")
        add_btn.setStyleSheet(button_style)
        add_btn.clicked.connect(self.add_user)
        button_layout.addWidget(add_btn)
        
        # 修改用户按钮
        edit_btn = QPushButton("✏️ 修改用户")
        edit_btn.setStyleSheet(button_style)
        edit_btn.clicked.connect(self.edit_user)
        button_layout.addWidget(edit_btn)
        
        # 删除用户按钮
        delete_btn = QPushButton("🗑️ 删除用户")
        delete_btn.setStyleSheet(button_style.replace("#4CAF50", "#f44336").replace("#2E7D32", "#c62828").replace("#f8fff8", "#fff8f8").replace("#e8f5e8", "#ffebee").replace("#c8e6c9", "#ffcdd2").replace("#45a049", "#e53935"))
        delete_btn.clicked.connect(self.delete_user)
        button_layout.addWidget(delete_btn)
        
        # 分隔线
        button_layout.addWidget(QLabel("|"))
        
        # 刷新数据按钮
        refresh_btn = QPushButton("🔄 刷新数据")
        refresh_btn.setStyleSheet(button_style.replace("#4CAF50", "#2196F3").replace("#2E7D32", "#1565C0").replace("#f8fff8", "#f8fcff").replace("#e8f5e8", "#e3f2fd").replace("#c8e6c9", "#bbdefb").replace("#45a049", "#1976D2"))
        refresh_btn.clicked.connect(self.load_authorized_users)
        button_layout.addWidget(refresh_btn)
        
        # 导出数据按钮
        export_btn = QPushButton("📊 导出数据")
        export_btn.setStyleSheet(button_style.replace("#4CAF50", "#FF9800").replace("#2E7D32", "#E65100").replace("#f8fff8", "#fffaf8").replace("#e8f5e8", "#fff3e0").replace("#c8e6c9", "#ffe0b2").replace("#45a049", "#F57C00"))
        export_btn.clicked.connect(self.export_users)
        button_layout.addWidget(export_btn)
        
        # 导入数据按钮
        import_btn = QPushButton("📥 导入数据")
        import_btn.setStyleSheet(button_style.replace("#4CAF50", "#9C27B0").replace("#2E7D32", "#6A1B9A").replace("#f8fff8", "#fdf8ff").replace("#e8f5e8", "#f3e5f5").replace("#c8e6c9", "#e1bee7").replace("#45a049", "#8E24AA"))
        import_btn.clicked.connect(self.import_users)
        button_layout.addWidget(import_btn)
        
        # 分隔线
        button_layout.addWidget(QLabel("|"))
        
        # 清除过期按钮
        clear_btn = QPushButton("🧹 清除过期")
        clear_btn.setStyleSheet(button_style.replace("#4CAF50", "#795548").replace("#2E7D32", "#5D4037").replace("#f8fff8", "#fafafa").replace("#e8f5e8", "#efebe9").replace("#c8e6c9", "#d7ccc8").replace("#45a049", "#6D4C41"))
        clear_btn.clicked.connect(self.clear_expired_users)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        self.layout().insertLayout(2, button_layout)
        
        # 设置表格
        self.setup_table()
    
    def setup_table(self):
        """设置表格样式"""
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
                color: #333;
            }
        """)
        
        # 设置表格属性
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(True)  # 显示网格线
        
        # 表头设置
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)  # 自动拉伸填满
        header.setStretchLastSection(True)
        
        # 设置最小列宽
        column_min_widths = [80, 120, 100, 120, 120, 160, 120, 120, 80]
        for i, min_width in enumerate(column_min_widths):
            if i < self.table.columnCount():
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                self.table.setColumnWidth(i, min_width)
        
        # 垂直表头
        v_header = self.table.verticalHeader()
        v_header.setVisible(False)  # 隐藏行号
        
        # 双击事件
        self.table.cellDoubleClicked.connect(self.show_user_detail)
    
    def load_authorized_users(self):
        """加载系统用户数据（包括系统用户和授权用户）"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 查询系统用户（users表 + staff表）
            system_users_sql = """
                SELECT 
                    u.id as user_id,
                    COALESCE(s.employee_id, u.username) as qr_code,
                    'system' as login_type,
                    COALESCE(s.phone, u.phone) as phone,
                    COALESCE(s.name, u.full_name) as user_name,
                    u.last_login as login_time,
                    '系统内部' as ip_address,
                    '系统用户' as location_data,
                    CASE WHEN u.is_active = 1 THEN '有效' ELSE '已禁用' END as status
                FROM users u
                LEFT JOIN staff s ON u.staff_id = s.id
                WHERE u.is_active = 1
            """
            
            # 查询授权用户（authorized_users表）
            auth_users_sql = """
                SELECT id, qr_code, login_type, phone, user_name, login_time, 
                       ip_address, location_data,
                       CASE WHEN expires_at > datetime('now') THEN '有效' ELSE '已过期' END as status
                FROM authorized_users 
            """
            
            # 合并查询
            combined_sql = f"""
                {system_users_sql}
                UNION ALL
                {auth_users_sql}
                ORDER BY login_time DESC
            """
            
            cursor.execute(combined_sql)
            rows = cursor.fetchall()
            conn.close()
            
            # 更新表格
            self.table.setRowCount(len(rows))
            
            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 7 and value:  # 位置信息
                        try:
                            location = json.loads(value)
                            lat = location.get('latitude', 'N/A')
                            lng = location.get('longitude', 'N/A')
                            value = f"{lat:.4f}, {lng:.4f}" if lat != 'N/A' else "无位置信息"
                        except:
                            value = "位置解析失败"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    
                    # 状态列颜色
                    if col_idx == 8:  # 状态列
                        if value == "有效":
                            item.setBackground(QColor(200, 255, 200))
                        else:
                            item.setBackground(QColor(255, 200, 200))
                    
                    self.table.setItem(row_idx, col_idx, item)
            
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"加载授权用户数据失败:\n{str(e)}")
    
    def filter_users(self):
        """筛选用户"""
        search_text = self.search_edit.text().strip().lower()
        login_type = self.login_type_combo.currentText()
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 系统用户查询
            system_users_sql = """
                SELECT 
                    u.id as user_id,
                    COALESCE(s.employee_id, u.username) as qr_code,
                    'system' as login_type,
                    COALESCE(s.phone, u.phone) as phone,
                    COALESCE(s.name, u.full_name) as user_name,
                    u.last_login as login_time,
                    '系统内部' as ip_address,
                    '系统用户' as location_data,
                    CASE WHEN u.is_active = 1 THEN '有效' ELSE '已禁用' END as status
                FROM users u
                LEFT JOIN staff s ON u.staff_id = s.id
                WHERE u.is_active = 1
            """
            
            # 授权用户查询
            auth_users_sql = """
                SELECT id, qr_code, login_type, phone, user_name, login_time, 
                       ip_address, location_data,
                       CASE WHEN expires_at > datetime('now') THEN '有效' ELSE '已过期' END as status
                FROM authorized_users WHERE 1=1
            """
            
            # 添加搜索条件
            search_conditions = []
            params = []
            
            if search_text:
                search_param = f"%{search_text}%"
                search_conditions.append("(LOWER(phone) LIKE ? OR LOWER(user_name) LIKE ? OR LOWER(qr_code) LIKE ?)")
                params.extend([search_param, search_param, search_param])
            
            if login_type != "全部":
                search_conditions.append("login_type = ?")
                params.append(login_type)
            
            # 应用搜索条件
            if search_conditions:
                condition_str = " AND " + " AND ".join(search_conditions)
                if login_type == "system" or login_type == "全部":
                    system_users_sql += condition_str
                if login_type != "system":
                    auth_users_sql += condition_str
            
            # 根据登录方式筛选决定查询哪些表
            if login_type == "system":
                # 只查询系统用户
                final_sql = system_users_sql + " ORDER BY login_time DESC"
                cursor.execute(final_sql, params[:len(params)//2] if search_text else params)
            elif login_type == "全部":
                # 查询所有用户
                combined_sql = f"""
                    {system_users_sql}
                    UNION ALL
                    {auth_users_sql}
                    ORDER BY login_time DESC
                """
                # 为两个查询准备参数
                all_params = params + params if search_text else params
                cursor.execute(combined_sql, all_params)
            else:
                # 只查询授权用户
                final_sql = auth_users_sql + " ORDER BY login_time DESC"
                cursor.execute(final_sql, params)
            
            rows = cursor.fetchall()
            conn.close()
            
            # 更新表格
            self.table.setRowCount(len(rows))
            for row_idx, row_data in enumerate(rows):
                for col_idx, value in enumerate(row_data):
                    if col_idx == 7 and value:
                        try:
                            location = json.loads(value)
                            lat = location.get('latitude', 'N/A')
                            lng = location.get('longitude', 'N/A')
                            value = f"{lat:.4f}, {lng:.4f}" if lat != 'N/A' else "无位置信息"
                        except:
                            value = "位置解析失败"
                    
                    item = QTableWidgetItem(str(value) if value else "")
                    if col_idx == 8 and value == "有效":
                        item.setBackground(QColor(200, 255, 200))
                    elif col_idx == 8:
                        item.setBackground(QColor(255, 200, 200))
                    
                    self.table.setItem(row_idx, col_idx, item)
            
        except Exception as e:
            QMessageBox.warning(self, "筛选失败", f"筛选用户数据失败:\n{str(e)}")
    
    def show_user_detail(self, row, col):
        """显示用户详情"""
        if row < self.table.rowCount():
            user_id = self.table.item(row, 0).text()
            qr_code = self.table.item(row, 1).text()
            
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM authorized_users WHERE id = ?
                """, (user_id,))
                
                user_data = cursor.fetchone()
                conn.close()
                
                if user_data:
                    detail_text = f"""
用户详细信息:
=================
用户ID: {user_data[0]}
二维码: {user_data[1]}
登录方式: {user_data[2]}
手机号: {user_data[3] or '未填写'}
用户姓名: {user_data[4] or '未填写'}
微信OpenID: {user_data[5] or '无'}
微信昵称: {user_data[6] or '无'}
登录时间: {user_data[9]}
IP地址: {user_data[10]}
用户代理: {user_data[11] or '无'}
授权令牌: {user_data[12][:16]}... (已隐藏)
过期时间: {user_data[13]}

位置信息:
{self.format_location_data(user_data[7])}

设备信息:
{self.format_device_info(user_data[8])}
                    """
                    
                    QMessageBox.information(self, f"用户详情 - {user_id}", detail_text)
                
            except Exception as e:
                QMessageBox.warning(self, "查询失败", f"获取用户详情失败:\n{str(e)}")
    
    def format_location_data(self, location_json):
        """格式化位置数据"""
        if not location_json:
            return "无位置信息"
        
        try:
            location = json.loads(location_json)
            return f"""
纬度: {location.get('latitude', 'N/A')}
经度: {location.get('longitude', 'N/A')}
精度: {location.get('accuracy', 'N/A')}m
时间戳: {location.get('timestamp', 'N/A')}
            """.strip()
        except:
            return "位置信息解析失败"
    
    def format_device_info(self, device_json):
        """格式化设备信息"""
        if not device_json:
            return "无设备信息"
        
        try:
            device = json.loads(device_json)
            return f"""
用户代理: {device.get('user_agent', 'N/A')[:50]}...
屏幕分辨率: {device.get('screen_resolution', 'N/A')}
语言: {device.get('language', 'N/A')}
平台: {device.get('platform', 'N/A')}
            """.strip()
        except:
            return "设备信息解析失败"
    
    def export_users(self):
        """导出用户数据"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, qr_code, login_type, phone, user_name, 
                       wechat_nickname, login_time, ip_address, 
                       location_data, device_info
                FROM authorized_users 
                ORDER BY login_time DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                QMessageBox.information(self, "提示", "没有可导出的数据")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存用户数据", f"授权用户数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                "CSV文件 (*.csv)"
            )
            
            if filename:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        "用户ID", "二维码", "登录方式", "手机号", "用户姓名", 
                        "微信昵称", "登录时间", "IP地址", "位置信息", "设备信息"
                    ])
                    for row in rows:
                        writer.writerow(row)
                
                QMessageBox.information(self, "导出成功", f"用户数据已导出到:\n{filename}")
        
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出用户数据失败:\n{str(e)}")
    
    def clear_expired_users(self):
        """清除过期用户"""
        reply = QMessageBox.question(self, "确认清除", 
                                    "确定要清除所有过期的授权用户记录吗？\n此操作不可撤销！",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM authorized_users WHERE expires_at <= datetime('now')")
                deleted_count = cursor.rowcount
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "清除完成", f"已清除 {deleted_count} 条过期记录")
                self.load_authorized_users()
                
            except Exception as e:
                QMessageBox.warning(self, "清除失败", f"清除过期用户失败:\n{str(e)}")
    
    def add_user(self):
        """新增用户"""
        from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QDateTimeEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("新增用户")
        dialog.setFixedSize(400, 500)
        
        layout = QFormLayout(dialog)
        
        # 输入字段
        qr_code_edit = QLineEdit()
        qr_code_edit.setPlaceholderText("二维码编号")
        
        login_type_combo = QComboBox()
        login_type_combo.addItems(["phone", "wechat", "qq", "system"])
        
        phone_edit = QLineEdit()
        phone_edit.setPlaceholderText("手机号码")
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("用户姓名")
        
        ip_edit = QLineEdit()
        ip_edit.setPlaceholderText("IP地址")
        ip_edit.setText("192.168.1.100")
        
        expires_edit = QDateTimeEdit()
        expires_edit.setDateTime(datetime.now().replace(year=datetime.now().year + 1))
        
        layout.addRow("二维码:", qr_code_edit)
        layout.addRow("登录方式:", login_type_combo)
        layout.addRow("手机号:", phone_edit)
        layout.addRow("用户姓名:", name_edit)
        layout.addRow("IP地址:", ip_edit)
        layout.addRow("过期时间:", expires_edit)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO authorized_users 
                    (qr_code, login_type, phone, user_name, ip_address, 
                     login_time, authorized_token, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    qr_code_edit.text(),
                    login_type_combo.currentText(),
                    phone_edit.text(),
                    name_edit.text(),
                    ip_edit.text(),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    f"token_{datetime.now().timestamp()}",
                    expires_edit.dateTime().toString('yyyy-MM-dd hh:mm:ss')
                ))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "成功", "用户添加成功！")
                self.load_authorized_users()
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"添加用户失败:\n{str(e)}")
    
    def edit_user(self):
        """修改用户"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要修改的用户")
            return
        
        user_id = self.table.item(current_row, 0).text()
        
        # 获取当前用户数据
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # 检查是否为系统用户
            login_type = self.table.item(current_row, 2).text()
            if login_type == "system":
                QMessageBox.warning(self, "提示", "系统用户不能在此修改，请使用用户权限管理模块")
                conn.close()
                return
            
            cursor.execute("SELECT * FROM authorized_users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            conn.close()
            
            if not user_data:
                QMessageBox.warning(self, "错误", "用户数据不存在")
                return
            
            # 创建编辑对话框
            from PyQt5.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QDateTimeEdit
            
            dialog = QDialog(self)
            dialog.setWindowTitle("修改用户")
            dialog.setFixedSize(400, 500)
            
            layout = QFormLayout(dialog)
            
            # 预填充数据
            qr_code_edit = QLineEdit(user_data[1])
            login_type_combo = QComboBox()
            login_type_combo.addItems(["phone", "wechat", "qq"])
            login_type_combo.setCurrentText(user_data[2])
            
            phone_edit = QLineEdit(user_data[3] or "")
            name_edit = QLineEdit(user_data[4] or "")
            ip_edit = QLineEdit(user_data[10] or "")
            
            expires_edit = QDateTimeEdit()
            if user_data[13]:
                expires_edit.setDateTime(datetime.strptime(user_data[13], '%Y-%m-%d %H:%M:%S'))
            
            layout.addRow("二维码:", qr_code_edit)
            layout.addRow("登录方式:", login_type_combo)
            layout.addRow("手机号:", phone_edit)
            layout.addRow("用户姓名:", name_edit)
            layout.addRow("IP地址:", ip_edit)
            layout.addRow("过期时间:", expires_edit)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            if dialog.exec_() == QDialog.Accepted:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE authorized_users 
                    SET qr_code=?, login_type=?, phone=?, user_name=?, 
                        ip_address=?, expires_at=?
                    WHERE id=?
                """, (
                    qr_code_edit.text(),
                    login_type_combo.currentText(),
                    phone_edit.text(),
                    name_edit.text(),
                    ip_edit.text(),
                    expires_edit.dateTime().toString('yyyy-MM-dd hh:mm:ss'),
                    user_id
                ))
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "成功", "用户修改成功！")
                self.load_authorized_users()
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"修改用户失败:\n{str(e)}")
    
    def delete_user(self):
        """删除用户"""
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户")
            return
        
        user_id = self.table.item(current_row, 0).text()
        user_name = self.table.item(current_row, 4).text()
        login_type = self.table.item(current_row, 2).text()
        
        if login_type == "system":
            QMessageBox.warning(self, "提示", "系统用户不能删除")
            return
        
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除用户 '{user_name}' 吗？\n此操作不可撤销！",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM authorized_users WHERE id = ?", (user_id,))
                conn.commit()
                conn.close()
                
                QMessageBox.information(self, "成功", f"用户 '{user_name}' 删除成功！")
                self.load_authorized_users()
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"删除用户失败:\n{str(e)}")
    
    def import_users(self):
        """导入用户数据"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择导入文件", "", "CSV文件 (*.csv);;Excel文件 (*.xlsx)"
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'r', encoding='utf-8-sig') as file:
                    reader = csv.DictReader(file)
                    
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    
                    imported_count = 0
                    for row in reader:
                        cursor.execute("""
                            INSERT INTO authorized_users 
                            (qr_code, login_type, phone, user_name, ip_address, 
                             login_time, authorized_token, expires_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            row.get('二维码', ''),
                            row.get('登录方式', 'phone'),
                            row.get('手机号', ''),
                            row.get('用户姓名', ''),
                            row.get('IP地址', '192.168.1.100'),
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            f"token_{datetime.now().timestamp()}_{imported_count}",
                            row.get('过期时间', '2025-12-31 23:59:59')
                        ))
                        imported_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(self, "导入成功", f"成功导入 {imported_count} 条用户记录")
                    self.load_authorized_users()
                    
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"导入用户数据失败:\n{str(e)}")

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance