from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QGridLayout, QStackedWidget, QApplication,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QIcon
import sys
import os
import sqlite3
import shutil
from datetime import datetime
from utils.logger import log_info, log_warning, log_error, log_debug




















class MainSystemWindow(QMainWindow):
    def gracefulExit(self):
        """优雅退出：先停止自动同步服务，再退出应用，并绕开最小化逻辑"""
        try:
            self._force_exit = True
            # 停止自动同步服务
            try:
                import main as _app_main
                if hasattr(_app_main, 'stop_auto_sync_service'):
                    _app_main.stop_auto_sync_service()
            except Exception as e:
                log_debug("停止自动同步服务时发生异常", module="系统退出", exception=e)
            # 关闭自身并退出应用
            try:
                self.close()
            except Exception as e:
                log_debug("关闭窗口时发生异常", module="系统退出", exception=e)
            app = QApplication.instance()
            if app:
                app.quit()
        except Exception as e:
            log_error("系统退出过程中发生异常", module="系统退出", exception=e)
            try:
                app = QApplication.instance()
                if app:
                    app.quit()
            except Exception as inner_e:
                log_error("强制退出应用时也发生异常", module="系统退出", exception=inner_e)
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user or {'username': 'guest', 'user_id': 0}
        self.current_user_roles = []
        self.current_user_permissions = []
        
        self.load_user_permissions()
        
        self.setWindowTitle("产品溯源二维码发行&管理系统")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
            }
        """)
        self.initUI()
        self.initTimer()
        self.initSystemTray()
        
    def load_user_permissions(self):
        """加载当前用户权限（基于数据库权限系统）"""
        try:
            log_info("开始加载用户权限", module="权限系统")
            from utils.permissions import get_user_permissions, get_user_role_names, has_permission
            
            # 从数据库获取用户的实际权限
            self.current_user_permissions = get_user_permissions(self.current_user)
            self.current_user_roles = get_user_role_names(self.current_user)
            
            # 尝试初始化权限UI辅助器，如果失败就跳过
            try:
                from utils.permission_ui_helper import PermissionUIHelper
                self.permission_helper = PermissionUIHelper(self.current_user)
                log_info("权限UI辅助器初始化成功", module="权限系统")
            except ImportError as e:
                log_debug(f"权限UI辅助器不存在，跳过: {e}", module="权限系统")
                self.permission_helper = None
            except Exception as e:
                log_warning("权限UI辅助器初始化失败", module="权限系统", exception=e)
                self.permission_helper = None
            
            log_info("用户权限加载成功", module="权限系统",
                    username=self.current_user.get('username', 'unknown'),
                    roles=str(self.current_user_roles),
                    permissions_count=len(self.current_user_permissions))
        except Exception as e:
            log_error("加载用户权限失败，使用默认权限配置", module="权限系统", exception=e)
            # 失败时兜底为只读浏览者
            self.current_user_roles = ['viewer']
            self.current_user_permissions = [
                'company.view', 'department.view', 'staff.view', 
                'logistics.view', 'qr.view', 'qr_history.view'
            ]
            self.permission_helper = None
            log_info("默认权限配置已应用", module="权限系统")
    
    def has_permission(self, permission):
        """检查用户是否有特定权限"""
        from utils.permissions import has_permission as check_permission
        return check_permission(self.current_user, permission)
    
    def is_general_user(self):
        """检查是否为一般使用者"""
        return 'general_user' in self.current_user_roles
    
    def check_module_permission(self, permission):
        """检查模块权限"""
        if not self.current_user:
            return True  # 默认显示所有模块
            
        # 管理员拥有所有权限
        if 'admin' in self.current_user_roles:
            return True
            
        # 权限匹配 - 修复权限检查逻辑
        if permission.endswith('.*'):
            prefix = permission[:-2]
            return any(p.startswith(prefix) or p == permission for p in self.current_user_permissions)
        else:
            return permission in self.current_user_permissions or any(p.endswith('.*') and permission.startswith(p[:-2]) for p in self.current_user_permissions)
        
    def initUI(self):
        central = QWidget()
        self.setCentralWidget(central)
        mainLayout = QVBoxLayout(central)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 顶部栏
        topBar = QHBoxLayout()
        topBar.setContentsMargins(12, 8, 12, 0)
        topBar.setSpacing(10)

        # 左上角功能按钮区域
        leftBar = QHBoxLayout()
        leftBar.setSpacing(8)
        
        # 切换用户按钮 - 统一高度
        self.switchUserBtn = QPushButton("🔁 切换用户")
        self.switchUserBtn.setFont(QFont("Microsoft YaHei", 11, QFont.Medium))
        self.switchUserBtn.setStyleSheet("""
            QPushButton {
                background: #e8f5e8;
                border: 2px solid #4caf50;
                border-radius: 8px;
                color: #2e7d32;
                padding: 8px 16px;
                min-height: 32px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #c8e6c9;
                border: 2px solid #388e3c;
                color: #1b5e20;
            }
            QPushButton:pressed {
                background: #a5d6a7;
            }
        """)
        self.switchUserBtn.clicked.connect(self.switchUser)
        leftBar.addWidget(self.switchUserBtn)
        
        # 退出系统按钮 - 现代化设计
        self.exitSystemBtn = QPushButton("🚪  退出系统")
        self.exitSystemBtn.setFont(QFont("Microsoft YaHei", 11, QFont.Medium))
        self.exitSystemBtn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 2px solid #dc3545;
                border-radius: 8px;
                color: #dc3545;
                padding: 8px 16px;
                min-height: 32px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #dc3545;
                color: white;
            }
            QPushButton:pressed {
                background: #c82333;
                border-color: #c82333;
            }
        """)
        self.exitSystemBtn.clicked.connect(self.exitSystem)
        leftBar.addWidget(self.exitSystemBtn)
        
        # 用户信息标签
        if self.permission_helper:
            permission_status = self.permission_helper.create_permission_status_text()
        else:
            username = self.current_user.get('username', 'unknown')
            role_text = ', '.join(self.current_user_roles) if self.current_user_roles else 'viewer'
            permission_status = f"{username} ({role_text})"
        
        self.userInfoLabel = QLabel(f"👤  {permission_status}")
        self.userInfoLabel.setFont(QFont("Microsoft YaHei", 11, QFont.Medium))
        self.userInfoLabel.setStyleSheet("""
            QLabel {
                color: #495057;
                background: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 8px;
                padding: 8px 16px;
                min-height: 32px;
                margin-left: 12px;
                font-weight: 500;
            }
        """)
        leftBar.addWidget(self.userInfoLabel)
        
        leftBar.addStretch()
        
        # 右上角时间
        self.timeLabel = QLabel()
        self.timeLabel.setFont(QFont("JetBrains Mono, Consolas, monospace", 12, QFont.Medium))
        self.timeLabel.setStyleSheet("""
            QLabel {
                color: #6c757d;
                background: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 16px;
                min-height: 32px;
                font-weight: 500;
                letter-spacing: 0.5px;
            }
        """)
        rightBar = QHBoxLayout()
        rightBar.addStretch()
        rightBar.addWidget(self.timeLabel)
        
        topBar.addLayout(leftBar, 1)
        topBar.addLayout(rightBar, 0)
        mainLayout.addLayout(topBar, 0)

        # 主体区域
        bodyLayout = QHBoxLayout()
        bodyLayout.setContentsMargins(0, 0, 0, 0)
        bodyLayout.setSpacing(0)

        # 左侧菜单
        menuFrame = QFrame()
        menuFrame.setFixedWidth(280)
        menuFrame.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border-right: 2px solid #dee2e6;
                border-radius: 0px;
            }
        """)
        menuLayout = QVBoxLayout(menuFrame)
        menuLayout.setContentsMargins(8, 12, 8, 12)
        menuLayout.setSpacing(2)

        # 定义模块和对应的权限（使用字符串避免导入阶段解析类名）
        self.modules_config = [
            {"name": "公司名称管理", "icon": "🏢", "permission": "company.view", "module": "modules.company_module", "class": "CompanyModule"},
            {"name": "部门名称管理", "icon": "🏬", "permission": "department.view", "module": "modules.department_module", "class": "DepartmentModule"},
            {"name": "产品种类管理", "icon": "📦", "permission": "company.view", "module": "modules.product_type_module", "class": "ProductTypeModule"},
            {"name": "产品规格管理", "icon": "📏", "permission": "company.view", "module": "modules.product_spec_module", "class": "ProductSpecModule"},
            {"name": "产品颜色管理", "icon": "🎨", "permission": "company.view", "module": "modules.product_color_module", "class": "ProductColorModule"},
            {"name": "产品特性管理", "icon": "⭐", "permission": "company.view", "module": "modules.product_feature_module", "class": "ProductFeatureModule"},
            {"name": "实验检测报告", "icon": "📋", "permission": "company.view", "module": "modules.lab_report_module", "class": "LabReportModule"},
            {"name": "出货检验报告", "icon": "📄", "permission": "company.view", "module": "modules.oqc_report_module", "class": "OQCReportModule"},

            {"name": "员工信息管理", "icon": "👥", "permission": "staff.view", "module": "modules.staff_module", "class": "StaffModule"},
            {"name": "二维码打印", "icon": "🖨️", "permission": "qr.generate", "module": "modules.qr_print_widget", "class": "QRPrintWidget"},
            {"name": "二维码历史", "icon": "📊", "permission": "qr_history.view", "module": "modules.qr_history_module", "class": "QRHistoryModule"},
            {"name": "扫码历史信息", "icon": "📱", "permission": "qr_history.view", "module": "modules.scan_history_module", "class": "ScanHistoryModule"},
            {"name": "物流车牌号管理", "icon": "🚛", "permission": "logistics.view", "module": "modules.logistics_module", "class": "LogisticsModule"},
            {"name": "经销商信息管理", "icon": "🤝", "permission": "company.view", "module": "modules.distributor_module", "class": "DistributorModule"},
            {"name": "用户权限管理", "icon": "🔐", "permission": "users.view", "module": "modules.user_permission_module", "class": "UserPermissionModule"},
            {"name": "自定义扩展", "icon": "⚙️", "permission": "company.view", "module": "modules.custom_module", "class": "CustomModule"}
        ]
        
        # 创建可见的模块按钮
        self.menuButtons = []
        self.visible_modules = []
        
        # 模块按钮
        for idx, config in enumerate(self.modules_config):
            btn = QPushButton(f"  {config['icon']}   {config['name']}")
            btn.setFont(QFont("Microsoft YaHei", 13, QFont.Medium))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    color: #495057;
                    padding: 12px 16px;
                    text-align: left;
                    min-height: 44px;
                    margin: 1px 4px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: rgba(13, 110, 253, 0.1);
                    color: #0d6efd;
                    border-left: 3px solid #0d6efd;
                }
                QPushButton:checked {
                    background: #0d6efd;
                    color: white;
                    border-left: 4px solid #ffffff;
                    font-weight: 600;
                }
                QPushButton:pressed {
                    background: #0a58ca;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, index=idx: self.onMenuClicked(index))
            self.menuButtons.append(btn)
            self.visible_modules.append(config)
            menuLayout.addWidget(btn)
        
        # 分隔线
        menuLayout.addSpacing(8)
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("""
            QFrame {
                background: #ced4da;
                border: none;
                max-height: 1px;
                margin: 8px 16px;
            }
        """)
        separator.setFixedHeight(1)
        menuLayout.addWidget(separator)
        menuLayout.addSpacing(8)
        
        # 数据备份按钮
        if self.check_module_permission("backup.manage"):
            backup_btn = QPushButton("  💾   数据备份")
            backup_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Medium))
            backup_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1px solid #198754;
                    border-radius: 8px;
                    color: #198754;
                    padding: 10px 16px;
                    text-align: left;
                    min-height: 38px;
                    margin: 1px 4px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background: #198754;
                    color: white;
                }
                QPushButton:pressed {
                    background: #157347;
                }
            """)
            backup_btn.clicked.connect(self.showBackupMenu)
            menuLayout.addWidget(backup_btn)
        menuLayout.addStretch()
        bodyLayout.addWidget(menuFrame, 0)

        # 右侧内容区
        self.stackedWidget = QStackedWidget()
        
        # 初始化模块列表（懒加载）
        self.modules = [None] * 18
        self.module_classes = [
            'modules.company_module:CompanyModule',
            'modules.department_module:DepartmentModule',
            'modules.product_type_module:ProductTypeModule',
            'modules.product_spec_module:ProductSpecModule',
            'modules.product_color_module:ProductColorModule',
            'modules.product_feature_module:ProductFeatureModule',
            'modules.lab_report_module:LabReportModule',
            'modules.oqc_report_module:OQCReportModule',

            'modules.staff_module:StaffModule',
            'modules.qr_print_widget:QRPrintWidget',
            'modules.qr_history_module:QRHistoryModule',
            'modules.scan_history_module:ScanHistoryModule',

            'modules.logistics_module:LogisticsModule',
            'modules.distributor_module:DistributorModule',
            'modules.user_permission_module:UserPermissionModule',
            'modules.custom_module:CustomModule'
        ]
        
        for i in range(18):
            placeholder = QWidget()
            placeholder.setObjectName(f"placeholder_{i}")
            self.stackedWidget.addWidget(placeholder)
        bodyLayout.addWidget(self.stackedWidget, 1)

        mainLayout.addLayout(bodyLayout, 1)

        # 默认选中二维码打印模块（第10个，索引9）
        try:
            log_info("初始化默认模块（二维码打印）", module="模块管理")
            self.loadModule(9)
            self.switchModule(9)
            log_info("默认模块初始化完成", module="模块管理")
        except Exception as e:
            log_warning("默认模块初始化失败，尝试加载备用模块", module="模块管理", exception=e)
            # 如果默认模块加载失败，尝试加载第一个可用模块
            for i in range(len(self.modules)):
                try:
                    self.loadModule(i)
                    self.switchModule(i)
                    log_info(f"已切换到备用模块 {i}", module="模块管理")
                    break
                except:
                    continue
        
    def switchModule(self, idx):
        try:
            # 动态导入前强制修复运行时路径，避免 EXE 环境下导入失败
            try:
                from utils.runtime_paths import ensure_runtime_paths
                ensure_runtime_paths(chdir=False)
            except Exception:
                pass
            log_debug(f"切换模块到索引: {idx}", module="模块管理")
            
            # 检查索引有效性
            if idx < 0 or idx >= len(self.menuButtons):
                log_warning(f"无效的模块索引: {idx}", module="模块管理")
                return
            
            # 更新按钮状态
            for i, btn in enumerate(self.menuButtons):
                btn.setChecked(i == idx)
            
            # 检查模块是否需要加载
            if idx >= len(self.modules) or self.modules[idx] is None:
                log_debug("模块未加载，开始加载", module="模块管理", module_index=idx)
                self.loadModule(idx)
            
            # 检查模块是否加载成功
            if idx < len(self.modules) and self.modules[idx] is not None:
                log_debug("设置当前模块", module="模块管理", module_index=idx)
                self.stackedWidget.setCurrentIndex(idx)
                
                # 特殊处理：二维码打印模块的数据加载
                if idx == 9 and hasattr(self.modules[9], 'load_data_to_combos'):
                    try:
                        log_debug("刷新二维码模块数据", module="模块管理")
                        self.modules[9].load_data_to_combos()
                    except Exception as e:
                        log_warning("二维码模块数据刷新失败", module="模块管理", exception=e)
                
                log_info("模块切换完成", module="模块管理", module_index=idx)
            else:
                log_error("模块加载失败，无法切换", module="模块管理", module_index=idx)
                
        except Exception as e:
            import traceback
            log_error("模块切换失败", module="模块管理", exception=e, 
                     error_trace=traceback.format_exc())
            
            # 尝试恢复到默认模块（二维码打印）
            try:
                if idx != 9 and len(self.menuButtons) > 9:
                    log_info("尝试恢复到默认模块", module="模块管理")
                    self.menuButtons[9].setChecked(True)
                    if self.modules[9] is not None:
                        self.stackedWidget.setCurrentIndex(9)
            except Exception as recovery_e:
                log_error("连恢复都失败了", module="模块管理", exception=recovery_e)
    
    def onMenuClicked(self, idx):
        try:
            log_debug(f"切换到模块索引: {idx}", module="模块管理")
            if idx < len(self.modules_config):
                module_name = self.modules_config[idx]['name']
                log_debug(f"模块名称: {module_name}", module="模块管理")
            
            self.switchModule(idx)
        except Exception as e:
            import traceback
            error_info = traceback.format_exc()
            log_error("菜单点击失败", module="模块管理", exception=e, 
                     error_trace=error_info)
            
            # 显示友好的错误信息而不是崩溃
            module_name = self.modules_config[idx]['name'] if idx < len(self.modules_config) else f"模块 {idx}"
            error_widget = QLabel(f"模块加载失败: {module_name}\n\n错误信息: {str(e)}\n\n请检查系统日志或联系管理员")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("""
                color: #d32f2f; 
                font-size: 14px; 
                background: #ffebee; 
                border: 2px solid #ffcdd2; 
                border-radius: 8px; 
                padding: 20px; 
                margin: 20px;
            """)
            error_widget.setWordWrap(True)
            
            try:
                old_widget = self.stackedWidget.widget(idx)
                if old_widget:
                    self.stackedWidget.removeWidget(old_widget)
                    old_widget.deleteLater()
                self.stackedWidget.insertWidget(idx, error_widget)
                self.modules[idx] = error_widget
            except Exception as inner_e:
                log_error("连错误处理都失败了", module="模块管理", exception=inner_e)
                # 最后的兜底措施
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self, "严重错误", f"模块 {module_name} 加载失败:\n{str(e)}")
            
            # 选中第一个按钮作为兜底
            if self.menuButtons:
                self.menuButtons[0].setChecked(True)

    def loadModule(self, idx):
        """动态加载指定模块"""
        if idx >= len(self.module_classes):
            log_warning(f"无效的模块索引: {idx}", module="模块管理")
            return
            
        module_info = self.module_classes[idx]
        module_name = self.modules_config[idx]['name'] if idx < len(self.modules_config) else f"模块 {idx}"
        
        try:
            log_info(f"开始加载模块: {module_name} (索引: {idx})", module="模块管理")
            log_debug(f"模块信息: {module_info}", module="模块管理")
            
            # 解析模块路径和类名
            if ':' not in module_info:
                raise ValueError(f"模块信息格式错误: {module_info}")
            
            module_path, class_name = module_info.split(':')
            log_debug(f"模块路径: {module_path}, 类名: {class_name}", module="模块管理")
            
            # 导入模块（更稳健的导入方式 + 失败重试）
            import importlib
            log_debug(f"导入模块: {module_path}", module="模块管理")
            try:
                module = importlib.import_module(module_path)
            except Exception as _e1:
                # 兜底：再次修复路径后重试一次
                try:
                    from utils.runtime_paths import ensure_runtime_paths
                    ensure_runtime_paths(chdir=False)
                except Exception:
                    pass
                module = importlib.import_module(module_path)
            
            # 获取类
            log_debug(f"获取类: {class_name}", module="模块管理")
            module_class = getattr(module, class_name)
            
            # 实例化模块
            log_debug("实例化模块", module="模块管理")
            if class_name == 'QRPrintWidget':
                module_instance = module_class(current_user=self.current_user)
                # 🚨 立即检查二维码打印权限
                from utils.permissions import has_permission
                can_generate = has_permission(self.current_user, "qr.generate")
                log_debug(f"二维码打印权限检查: qr.generate = {can_generate}", module="权限系统")
                if not can_generate:
                    log_warning(f"用户 {self.current_user.get('username', 'unknown')} 没有qr.generate权限，立即禁用模块", module="权限系统")
                    # 立即禁用整个模块
                    module_instance.setEnabled(False)
                    module_instance.setStyleSheet("QWidget { background-color: #f8f9fa; color: #6c757d; }")
                    module_instance.setToolTip("您没有使用二维码打印模块的权限 - 系统浏览者仅限查看")
            else:
                module_instance = module_class()
            
            log_info("模块实例化成功", module="模块管理", module_name=module_name)
            
            # 设置权限
            try:
                log_debug("设置权限", module="权限系统", module_name=module_name)
                if hasattr(module_instance, 'setup_permissions'):
                    # 新的权限设置方法
                    module_instance.setup_permissions(self.current_user)
                elif hasattr(module_instance, 'apply_permissions'):
                    module_instance.apply_permissions(self.current_user)
                elif hasattr(module_instance, 'set_current_user'):
                    module_instance.set_current_user(self.current_user)
                elif hasattr(module_instance, 'current_user') and hasattr(module_instance, 'current_user_roles'):
                    module_instance.current_user = self.current_user
                    module_instance.current_user_roles = self.current_user_roles
                    if hasattr(module_instance, '_apply_ui_permissions'):
                        module_instance._apply_ui_permissions()
                log_info("权限设置完成", module="权限系统", module_name=module_name)
            except Exception as e:
                log_warning("模块权限设置失败", module="权限系统", exception=e, module_name=module_name)
                # 权限设置失败不影响模块加载
            
            # 更新UI
            log_debug("更新界面", module="模块管理", module_name=module_name)
            try:
                old_widget = self.stackedWidget.widget(idx)
                if old_widget:
                    self.stackedWidget.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                self.stackedWidget.insertWidget(idx, module_instance)
                self.modules[idx] = module_instance
                log_info(f"模块 {module_name} 加载完成", module="模块管理")
            except Exception as e:
                log_error("界面更新失败", module="模块管理", exception=e, module_name=module_name)
                raise e
            
        except Exception as e:
            import traceback
            error_info = traceback.format_exc()
            log_error(f"模块加载失败: {module_name}", module="模块管理", 
                     exception=e, error_trace=error_info)
            
            # 创建错误显示组件
            error_widget = QLabel(f"模块加载失败\n\n模块: {module_name}\n错误: {str(e)}\n\n请检查:\n• 模块文件是否存在\n• 依赖是否正确安装\n• 数据库连接是否正常")
            error_widget.setAlignment(Qt.AlignCenter)
            error_widget.setStyleSheet("""
                color: #d32f2f; 
                font-size: 14px; 
                background: #ffebee; 
                border: 2px solid #ffcdd2; 
                border-radius: 8px; 
                padding: 20px; 
                margin: 20px;
            """)
            error_widget.setWordWrap(True)
            
            try:
                old_widget = self.stackedWidget.widget(idx)
                if old_widget:
                    self.stackedWidget.removeWidget(old_widget)
                    old_widget.deleteLater()
                
                self.stackedWidget.insertWidget(idx, error_widget)
                self.modules[idx] = error_widget
                log_info("错误界面已显示", module="模块管理", module_name=module_name)
            except Exception as inner_e:
                log_error("连错误界面都无法创建", module="模块管理", exception=inner_e)
                # 最后的兜底措施：显示消息框
                try:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "模块加载失败", f"无法加载模块: {module_name}\n\n错误: {str(e)}")
                except Exception as msg_e:
                    log_error("连消息框都无法显示，系统可能存在严重问题", module="模块管理", exception=msg_e)
        
    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)
        self.updateTime()
        
    def updateTime(self):
        now = QDateTime.currentDateTime()
        self.timeLabel.setText(now.toString("yyyy.MM.dd.HH:mm:ss"))

    def initSystemTray(self):
        """初始化系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "系统托盘", "系统不支持托盘功能")
            return
            
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon())
        self.trayIcon.setToolTip("产品溯源二维码发行&管理系统")
        
        trayMenu = QMenu()
        
        showAction = QAction("显示主窗口", self)
        showAction.triggered.connect(self.showNormal)
        trayMenu.addAction(showAction)
        
        hideAction = QAction("隐藏窗口", self)
        hideAction.triggered.connect(self.hide)
        trayMenu.addAction(hideAction)
        
        trayMenu.addSeparator()
        
        exitAction = QAction("退出系统", self)
        exitAction.triggered.connect(self.gracefulExit)
        trayMenu.addAction(exitAction)
        
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()
        
        self.trayIcon.activated.connect(self.trayIconActivated)
    
    def trayIconActivated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.raise_()
                self.activateWindow()
    
    def closeEvent(self, event):
        """重写关闭事件，最小化到托盘"""
        if hasattr(self, 'trayIcon') and self.trayIcon.isVisible():
            self.hide()
            self.trayIcon.showMessage(
                "系统提示",
                "程序已最小化到系统托盘，双击托盘图标可恢复显示",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
    
    def backupDatabase(self):
        """备份数据库"""
        try:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_system.db')
            
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"qr_system_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            shutil.copy2(db_path, backup_path)
            
            QMessageBox.information(self, "备份成功", f"数据库已成功备份到:\n{backup_path}")
            return backup_path
            
        except Exception as e:
            QMessageBox.critical(self, "备份失败", f"数据库备份失败:\n{str(e)}")
            return None
    
    def restoreDatabase(self):
        """恢复数据库"""
        try:
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
            
            if not os.path.exists(backup_dir):
                QMessageBox.warning(self, "恢复失败", "未找到备份目录")
                return
            
            backup_path, _ = QFileDialog.getOpenFileName(
                self, 
                "选择备份文件",
                backup_dir,
                "数据库文件 (*.db);;所有文件 (*.*)"
            )
            
            if not backup_path:
                return
            
            reply = QMessageBox.question(
                self, 
                "确认恢复", 
                "恢复数据库将覆盖当前所有数据，确定要继续吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qr_system.db')
            
            shutil.copy2(backup_path, db_path)
            
            QMessageBox.information(self, "恢复成功", "数据库已成功恢复，请重启应用程序以应用更改")
            
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", f"数据库恢复失败:\n{str(e)}")
    
    def autoBackupDatabase(self):
        """自动备份数据库"""
        try:
            backup_path = self.backupDatabase()
            if backup_path:
                log_info("自动备份完成", module="系统维护", backup_path=backup_path)
        except Exception as e:
            log_error("自动备份失败", module="系统维护", exception=e)
    
    def showBackupMenu(self):
        """显示备份菜单"""
        menu = QMenu(self)
        
        backup_action = QAction("立即备份", self)
        backup_action.triggered.connect(self.backupDatabase)
        menu.addAction(backup_action)
        
        restore_action = QAction("恢复备份", self)
        restore_action.triggered.connect(self.restoreDatabase)
        menu.addAction(restore_action)
        
        menu.exec_(self.mapToGlobal(self.pos()))

    def switchUser(self):
        """切换用户功能"""
        try:
            from PyQt5.QtWidgets import QMessageBox, QApplication
            from welcome import WelcomeWindow
            
            reply = QMessageBox.question(
                self,
                "确认切换用户",
                "确定要切换用户吗？当前用户的未保存数据将会丢失。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.close()
                
                self.welcomeWin = WelcomeWindow()
                self.welcomeWin.show()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"切换用户失败：{str(e)}")

    def exitSystem(self):
        """退出系统功能（走优雅退出）"""
        try:
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "确认退出",
                "确定要退出系统吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.gracefulExit()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"退出系统失败：{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon())
    
    win = MainSystemWindow()
    win.show()
    sys.exit(app.exec_())