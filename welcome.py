import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QApplication,
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QLineEdit, QFormLayout
)
from PyQt5.QtCore import Qt, QTimer, QDateTime
from PyQt5.QtGui import QFont, QPixmap, QColor, QPainter, QPalette, QIcon

class WelcomeWindow(QWidget):
    def exit_app(self):
        """优雅退出：先停止自动同步服务，再退出应用"""
        try:
            # 标记强制退出，绕开最小化逻辑
            self._force_exit = True
            # 停止自动同步服务
            try:
                import main as _app_main
                if hasattr(_app_main, 'stop_auto_sync_service'):
                    _app_main.stop_auto_sync_service()
            except Exception:
                pass
            # 退出应用
            qapp = QApplication.instance()
            if qapp:
                qapp.quit()
        except Exception as e:
            print(f"[WARNING] 退出流程异常: {e}")
            qapp = QApplication.instance()
            if qapp:
                qapp.quit()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("B·A·PTQRCs - 欢迎页面")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet("background: white;")
        self.initUI()
        self.initTimer()
        self.current_user = None

    def initUI(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 顶部栏
        topBar = QHBoxLayout()
        topBar.setContentsMargins(12, 8, 12, 0)
        topBar.setSpacing(0)

        # LOGO+简称
        logoLabel = QLabel()
        logoPixmap = QPixmap(48, 48)
        logoPixmap.fill(QColor("#b2dfdb"))
        painter = QPainter(logoPixmap)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#7fc8a9"))
        painter.drawRect(0, 0, 24, 24)
        painter.setPen(QColor("#3b5998"))
        painter.setFont(QFont("Arial", 24, QFont.Bold))
        painter.drawText(0, 0, 48, 48, Qt.AlignCenter, "B")
        painter.end()
        logoLabel.setPixmap(logoPixmap)
        logoLabel.setFixedSize(48, 48)

        titleLabel = QLabel("（产品溯源二维码发行＆管理）")
        titleLabel.setFont(QFont("Arial", 16, QFont.Bold))
        titleLabel.setStyleSheet("color: #7fa6c7; margin-left: 8px;")
        leftBar = QHBoxLayout()
        leftBar.addWidget(logoLabel)
        leftBar.addWidget(titleLabel)
        leftBar.addStretch()

        # 右上角时间
        self.timeLabel = QLabel()
        self.timeLabel.setFont(QFont("Arial", 12))
        self.timeLabel.setStyleSheet("color: #2d3a4a; background: #f7f7f7; border-radius: 8px; padding: 4px 12px;")
        rightBar = QHBoxLayout()
        rightBar.addStretch()
        rightBar.addWidget(self.timeLabel)

        topBar.addLayout(leftBar, 1)
        topBar.addLayout(rightBar, 0)
        mainLayout.addLayout(topBar, 0)

        # 中间内容
        centerLayout = QVBoxLayout()
        centerLayout.setSpacing(16)
        centerLayout.addStretch()

        # 欢迎大标题
        welcomeLabel = QLabel("欢迎使用示例集团公司多功能数智系统")
        welcomeLabel.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        welcomeLabel.setStyleSheet("color: #2366a8;")
        welcomeLabel.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(welcomeLabel, 0, Qt.AlignHCenter | Qt.AlignTop)

        # 副标题
        subTitle = QLabel("（产品溯源二维码发行＆管理）")
        subTitle.setFont(QFont("Microsoft YaHei", 36, QFont.Bold))
        subTitle.setStyleSheet("color: #2366a8;")
        subTitle.setAlignment(Qt.AlignCenter)
        centerLayout.addWidget(subTitle, 0, Qt.AlignHCenter | Qt.AlignTop)

        # 登录表单区域
        loginLayout = QVBoxLayout()
        loginLayout.setSpacing(8)  # 8-10mm垂直间距，转换为像素
        
        # 用户名输入
        self.usernameEdit = QLineEdit()
        self.usernameEdit.setPlaceholderText("请输入用户名（员工请使用员工工号）")
        self.usernameEdit.setFixedSize(360, 40)
        self.usernameEdit.setFont(QFont("Microsoft YaHei", 14))
        self.usernameEdit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #7fa6c7;
                border-radius: 8px;
                padding: 8px 12px;
                background: white;
                color: #2d3a4a;
                text-align: center;
            }
            QLineEdit:focus {
                border: 2px solid #d13ca1;
                background: #f8f9fa;
            }
        """)
        self.usernameEdit.setAlignment(Qt.AlignCenter)
        
        # 员工ID输入
        self.employeeIdEdit = QLineEdit()
        self.employeeIdEdit.setPlaceholderText("请输入员工工号")
        self.employeeIdEdit.setFixedSize(360, 40)
        self.employeeIdEdit.setFont(QFont("Microsoft YaHei", 14))
        self.employeeIdEdit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #7fa6c7;
                border-radius: 8px;
                padding: 8px 12px;
                background: white;
                color: #2d3a4a;
                text-align: center;
            }
            QLineEdit:focus {
                border: 2px solid #d13ca1;
                background: #f8f9fa;
            }
        """)
        self.employeeIdEdit.setAlignment(Qt.AlignCenter)
        
        # 密码输入
        self.passwordEdit = QLineEdit()
        self.passwordEdit.setPlaceholderText("请输入密码")
        self.passwordEdit.setEchoMode(QLineEdit.Password)
        self.passwordEdit.setFixedSize(360, 40)
        self.passwordEdit.setFont(QFont("Microsoft YaHei", 14))
        self.passwordEdit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #7fa6c7;
                border-radius: 8px;
                padding: 8px 12px;
                background: white;
                color: #2d3a4a;
                text-align: center;
            }
            QLineEdit:focus {
                border: 2px solid #d13ca1;
                background: #f8f9fa;
            }
        """)
        self.passwordEdit.setAlignment(Qt.AlignCenter)
        
        loginLayout.addWidget(self.usernameEdit, alignment=Qt.AlignHCenter)
        loginLayout.addWidget(self.employeeIdEdit, alignment=Qt.AlignHCenter)
        loginLayout.addWidget(self.passwordEdit, alignment=Qt.AlignHCenter)
        
        # 进入系统按钮
        self.enterBtn = QPushButton("进入系统")
        self.enterBtn.setFixedSize(360, 80)
        self.enterBtn.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        self.enterBtn.setStyleSheet("""
            QPushButton {
                background: #e3e6f3;
                color: #d13ca1;
                border: 2px solid #7fa6c7;
                border-radius: 12px;
                margin-top: 16px;
                margin-bottom: 16px;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: #f8e1f4;
                color: #b80060;
                border: 2px solid #d13ca1;
            }
            QPushButton:pressed {
                background: #d13ca1;
                color: white;
            }
        """)
        self.enterBtn.clicked.connect(self.loginAndEnterSystem)
        loginLayout.addWidget(self.enterBtn, alignment=Qt.AlignHCenter)
        
        # 按钮区域
        buttonLayout = QHBoxLayout()
        buttonLayout.setSpacing(20)
        
        # 忘记密码按钮
        self.forgotPasswordBtn = QPushButton("忘记密码")
        self.forgotPasswordBtn.setFixedSize(120, 32)
        self.forgotPasswordBtn.setFont(QFont("Microsoft YaHei", 12))
        self.forgotPasswordBtn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #7fa6c7;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #d13ca1;
            }
        """)
        self.forgotPasswordBtn.clicked.connect(self.forgotPassword)
        buttonLayout.addWidget(self.forgotPasswordBtn)
        
        # 修改密码按钮
        self.changePasswordBtn = QPushButton("修改密码")
        self.changePasswordBtn.setFixedSize(120, 32)
        self.changePasswordBtn.setFont(QFont("Microsoft YaHei", 12))
        self.changePasswordBtn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #7fa6c7;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #d13ca1;
            }
        """)
        self.changePasswordBtn.clicked.connect(self.changePassword)
        buttonLayout.addWidget(self.changePasswordBtn)
        
        loginLayout.addLayout(buttonLayout)
        
        centerLayout.addLayout(loginLayout)

        centerLayout.addStretch()
        mainLayout.addLayout(centerLayout, 1)

        # 底部版权
        bottomBar = QHBoxLayout()
        bottomBar.setContentsMargins(0, 0, 0, 0)
        bottomBar.setSpacing(0)
        copyrightLabel = QLabel("版权 [Author] & Example Group)所有 盗版必究！")
        copyrightLabel.setFont(QFont("Microsoft YaHei", 14))
        copyrightLabel.setStyleSheet("color: #eac6f7;")
        bottomBar.addWidget(copyrightLabel, alignment=Qt.AlignLeft)
        bottomBar.addStretch()
        sysLabel = QLabel("（产品溯源二维码发行＆管理）")
        sysLabel.setFont(QFont("Microsoft YaHei", 12))
        sysLabel.setStyleSheet("color: #bfae9e;")
        bottomBar.addWidget(sysLabel, alignment=Qt.AlignRight)
        mainLayout.addLayout(bottomBar, 0)

    def initTimer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)
        self.updateTime()

    def updateTime(self):
        now = QDateTime.currentDateTime()
        self.timeLabel.setText(now.toString("yyyy.MM.dd.HH:mm:ss"))

    def enterSystem(self):
        """安全进入主系统（异步切换，避免回车重入导致退出）"""
        if getattr(self, "_entering_system", False):
            return
        self._entering_system = True
        try:
            print("🔍 开始导入MainSystemWindow...")
            from main_system import MainSystemWindow
            print("✅ MainSystemWindow导入成功")
            
            print("🔍 开始创建MainSystemWindow实例...")
            self.mainWin = MainSystemWindow(current_user=self.current_user)
            print("✅ MainSystemWindow实例创建成功")
            
            # 先显示主窗口
            print("🔍 开始显示主窗口...")
            self.mainWin.showMaximized()
            print("✅ 主窗口显示成功")
            
            # 异步隐藏欢迎页，避免立即 close 造成事件循环提前结束
            print("🔍 隐藏欢迎页...")
            QTimer.singleShot(50, self.hide)
            print("✅ 进入主系统完成")
            
        except Exception as e:
            # 失败时保留欢迎页并清除标记
            print(f"❌ 进入主系统失败: {e}")
            import traceback
            traceback.print_exc()
            
            from PyQt5.QtWidgets import QMessageBox
            error_msg = f"进入主系统时发生错误：{str(e)}\n\n详细信息已输出到控制台，请检查。"
            QMessageBox.critical(self, "系统错误", error_msg)
            self._entering_system = False

    def loginAndEnterSystem(self):
        """登录并进入系统"""
        try:
            import os
            import sqlite3
            
            # 确保正确的导入路径
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            from utils.auth import auth_manager
            
            username = self.usernameEdit.text().strip()
            employee_id = self.employeeIdEdit.text().strip()
            password = self.passwordEdit.text()
            
            # 验证输入
            if not username or not password:
                QMessageBox.warning(self, "登录失败", "请输入用户名和密码")
                return
            
            # 获取数据库路径
            db_path = os.path.join(os.path.dirname(__file__), 'qr_system.db')
            
            # 智能登录逻辑：支持用户名、员工工号或姓名登录
            login_username = username
            actual_employee_id = employee_id  # 保存用户输入的员工工号
            
            # 如果不是管理员，尝试智能匹配用户
            if username != "admin":
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # 首先检查用户名是否直接存在于users表中
                    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
                    if not cursor.fetchone():
                        # 用户名不存在，尝试通过姓名查找员工工号
                        cursor.execute("SELECT employee_id FROM staff WHERE name = ?", (username,))
                        staff_result = cursor.fetchone()
                        if staff_result:
                            login_username = staff_result[0]  # 使用员工工号作为登录用户名
                            actual_employee_id = staff_result[0]  # 更新实际的员工工号
                    
                    conn.close()
                except Exception as e:
                    print(f"查找用户信息时出错: {e}")
            
            # 尝试登录
            result = auth_manager.authenticate_user(login_username, password)
            
            if result['success']:
                self.current_user = {'username': login_username, 'user_id': result['user_id'], 'employee_id': actual_employee_id}
                # 获取用户的真实姓名用于欢迎信息
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT full_name FROM users WHERE username = ?", (login_username,))
                    user_result = cursor.fetchone()
                    display_name = user_result[0] if user_result else login_username
                    conn.close()
                except:
                    display_name = login_username
                
                QMessageBox.information(self, "登录成功", f"欢迎回来，{display_name}！")
                # 异步切换，避免回车关闭弹窗的同时触发重入导致闪退
                QTimer.singleShot(0, self.enterSystem)
            else:
                QMessageBox.warning(self, "登录失败", result.get('error', '用户名或密码错误'))
                
        except Exception as e:
            QMessageBox.critical(self, "登录错误", f"登录过程中发生错误：{str(e)}")

    def forgotPassword(self):
        """忘记密码处理"""
        try:
            # 创建简单的找回密码对话框
            dialog = QMessageBox(self)
            dialog.setWindowTitle("忘记密码")
            dialog.setText("请联系系统管理员重置您的密码。\n\n管理员联系信息：\n• 内部系统：用户权限管理模块\n• 邮箱：user@example.com\n• 电话：010-12345678")
            dialog.setIcon(QMessageBox.Information)
            dialog.setStandardButtons(QMessageBox.Ok)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理忘记密码时发生错误：{str(e)}")

    def changePassword(self):
        """修改密码功能"""
        try:
            from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
            
            # 创建修改密码对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("修改密码")
            dialog.resize(350, 200)
            
            layout = QFormLayout(dialog)
            
            # 用户名输入
            usernameEdit = QLineEdit()
            usernameEdit.setPlaceholderText("请输入用户名")
            layout.addRow("用户名*", usernameEdit)
            
            # 员工工号输入
            employeeIdEdit = QLineEdit()
            employeeIdEdit.setPlaceholderText("请输入员工工号")
            layout.addRow("员工工号*", employeeIdEdit)
            
            # 旧密码输入
            oldPasswordEdit = QLineEdit()
            oldPasswordEdit.setEchoMode(QLineEdit.Password)
            oldPasswordEdit.setPlaceholderText("请输入旧密码")
            layout.addRow("旧密码*", oldPasswordEdit)
            
            # 新密码输入
            newPasswordEdit = QLineEdit()
            newPasswordEdit.setEchoMode(QLineEdit.Password)
            newPasswordEdit.setPlaceholderText("请输入新密码")
            layout.addRow("新密码*", newPasswordEdit)
            
            # 确认新密码输入
            confirmPasswordEdit = QLineEdit()
            confirmPasswordEdit.setEchoMode(QLineEdit.Password)
            confirmPasswordEdit.setPlaceholderText("请再次输入新密码")
            layout.addRow("确认新密码*", confirmPasswordEdit)
            
            # 按钮
            buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            layout.addRow(buttonBox)
            
            def changePassword():
                username = usernameEdit.text().strip()
                employee_id = employeeIdEdit.text().strip()
                old_password = oldPasswordEdit.text()
                new_password = newPasswordEdit.text()
                confirm_password = confirmPasswordEdit.text()
                
                if not all([username, employee_id, old_password, new_password, confirm_password]):
                    QMessageBox.warning(dialog, "错误", "请填写所有必填字段")
                    return
                
                if new_password != confirm_password:
                    QMessageBox.warning(dialog, "错误", "新密码与确认密码不一致")
                    return
                
                if len(new_password) < 6:
                    QMessageBox.warning(dialog, "错误", "新密码长度不能少于6位")
                    return
                
                try:
                    from utils.auth import auth_manager
                    from utils.security import security_manager
                    import sqlite3
                    
                    # 验证用户身份
                    conn = sqlite3.connect('qr_system.db')
                    cursor = conn.cursor()
                    
                    # 特殊处理管理员账户
                    if username == "admin" and employee_id == "admin":
                        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
                    else:
                        # 验证员工工号和姓名匹配
                        cursor.execute("SELECT name FROM staff WHERE employee_id = ?", (employee_id,))
                        staff_result = cursor.fetchone()
                        if not staff_result:
                            QMessageBox.warning(dialog, "错误", "员工工号不存在")
                            conn.close()
                            return
                        
                        staff_name = staff_result[0]
                        if staff_name != username:
                            QMessageBox.warning(dialog, "错误", "员工姓名与用户名不匹配")
                            conn.close()
                            return
                        
                        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
                    
                    user_result = cursor.fetchone()
                    
                    if not user_result:
                        QMessageBox.warning(dialog, "错误", "用户不存在")
                        conn.close()
                        return
                    
                    user_id, password_hash = user_result
                    
                    # 验证旧密码
                    if not security_manager.verify_password(old_password, password_hash):
                        QMessageBox.warning(dialog, "错误", "旧密码错误")
                        conn.close()
                        return
                    
                    # 更新密码
                    new_hash = security_manager.hash_password(new_password)
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (new_hash, user_id)
                    )
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(dialog, "成功", "密码修改成功！")
                    dialog.accept()
                    
                except Exception as e:
                    QMessageBox.critical(dialog, "错误", f"修改密码失败：{str(e)}")
            
            buttonBox.accepted.connect(changePassword)
            buttonBox.rejected.connect(dialog.reject)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理修改密码时发生错误：{str(e)}")

    def keyPressEvent(self, event):
        """键盘事件处理，支持回车键登录"""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.loginAndEnterSystem()
        else:
            super().keyPressEvent(event)

    def initSystemTray(self):
        """初始化系统托盘"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(self, "系统托盘", "系统不支持托盘功能")
            return
            
        self.trayIcon = QSystemTrayIcon(self)
        # 生成一个简易图标，避免出现 "No Icon set" 提示
        icon_pix = QPixmap(32, 32)
        icon_pix.fill(QColor("#b2dfdb"))
        p = QPainter(icon_pix)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#7fc8a9"))
        p.drawRect(0, 0, 16, 16)
        p.setPen(QColor("#3b5998"))
        p.setFont(QFont("Arial", 14, QFont.Bold))
        p.drawText(0, 0, 32, 32, Qt.AlignCenter, "B")
        p.end()
        self.trayIcon.setIcon(QIcon(icon_pix))
        self.trayIcon.setToolTip("（产品溯源二维码发行&管理） - 欢迎页面")
        
        # 创建托盘菜单
        trayMenu = QMenu()
        
        showAction = QAction("显示主窗口", self)
        showAction.triggered.connect(self.showNormal)
        trayMenu.addAction(showAction)
        
        exitAction = QAction("退出系统", self)
        exitAction.triggered.connect(self.exit_app)
        trayMenu.addAction(exitAction)
        
        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()
        
        # 托盘图标点击事件
        self.trayIcon.activated.connect(self.trayIconActivated)
    
    def trayIconActivated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.raise_()
            self.activateWindow()
    
    def closeEvent(self, event):
        """重写关闭事件，最小化到托盘；若明确选择“退出系统”，则走优雅退出流程"""
        if getattr(self, '_force_exit', False):
            event.accept()
            return
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序图标（与托盘一致）
    icon_pix = QPixmap(32, 32)
    icon_pix.fill(QColor("#b2dfdb"))
    p = QPainter(icon_pix)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#7fc8a9"))
    p.drawRect(0, 0, 16, 16)
    p.setPen(QColor("#3b5998"))
    p.setFont(QFont("Arial", 14, QFont.Bold))
    p.drawText(0, 0, 32, 32, Qt.AlignCenter, "B")
    p.end()
    app.setWindowIcon(QIcon(icon_pix))
    
    win = WelcomeWindow()
    win.initSystemTray()  # 初始化系统托盘
    win.show()
    sys.exit(app.exec_())