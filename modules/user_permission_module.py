from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                           QHBoxLayout, QTableWidget, QTableWidgetItem, 
                           QHeaderView, QMessageBox, QDialog, QFormLayout, 
                           QLineEdit, QComboBox, QDialogButtonBox, QFileDialog,
                           QDateEdit, QCheckBox, QFrame, QGridLayout)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDate
import sqlite3
import os
import csv
from datetime import datetime
from utils.auth import auth_manager
from utils.export_import_simple import export_manager
from utils.permissions import has_permission
import sys

class UserPermissionModule(QWidget):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.initUI()

    def get_all_staff(self):
        """获取所有员工信息"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, employee_id FROM staff ORDER BY id")
            staff_list = cursor.fetchall()
            conn.close()
            return staff_list
        except Exception as e:
            print(f"获取员工信息失败: {e}")
            return []

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # 标题
        title = QLabel("用户权限管理")
        title.setFont(QFont("Microsoft YaHei", 22, QFont.Bold))
        title.setStyleSheet("color: #228b22; border: none; background: transparent; padding: 12px 0 18px 0;")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # 操作按钮区域
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(16)

        self.addBtn = QPushButton("新增用户")
        self.addBtn.setFixedWidth(100)
        self.addBtn.setFont(QFont("Microsoft YaHei", 12))
        self.addBtn.clicked.connect(self.add_user)
        btnLayout.addWidget(self.addBtn)

        self.editBtn = QPushButton("编辑用户")
        self.editBtn.setFixedWidth(100)
        self.editBtn.setFont(QFont("Microsoft YaHei", 12))
        self.editBtn.clicked.connect(self.edit_user)
        btnLayout.addWidget(self.editBtn)

        self.deleteBtn = QPushButton("删除用户")
        self.deleteBtn.setFixedWidth(100)
        self.deleteBtn.setFont(QFont("Microsoft YaHei", 12))
        self.deleteBtn.clicked.connect(self.delete_user)
        btnLayout.addWidget(self.deleteBtn)

        # 导入导出按钮
        self.importBtn = QPushButton("整体上传")
        self.importBtn.setFixedWidth(100)
        self.importBtn.setFont(QFont("Microsoft YaHei", 12))
        self.importBtn.clicked.connect(self.import_users)
        btnLayout.addWidget(self.importBtn)

        self.exportBtn = QPushButton("下载")
        self.exportBtn.setFixedWidth(100)
        self.exportBtn.setFont(QFont("Microsoft YaHei", 12))
        self.exportBtn.clicked.connect(self.export_users)
        btnLayout.addWidget(self.exportBtn)

        self.resetPasswordBtn = QPushButton("重置密码")
        self.resetPasswordBtn.setFixedWidth(100)
        self.resetPasswordBtn.setFont(QFont("Microsoft YaHei", 12))
        self.resetPasswordBtn.clicked.connect(self.reset_password)
        btnLayout.addWidget(self.resetPasswordBtn)

        self.templateBtn = QPushButton("上传格式下载")
        self.templateBtn.setFixedWidth(120)
        self.templateBtn.setFont(QFont("Microsoft YaHei", 12))
        self.templateBtn.clicked.connect(self.download_template)
        btnLayout.addWidget(self.templateBtn)

        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 搜索功能
        searchLayout = QHBoxLayout()
        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("搜索用户姓名或工号...")
        self.searchEdit.setStyleSheet("border: 1.5px solid #1976d2; border-radius: 6px; padding: 4px 8px;")
        self.searchEdit.textChanged.connect(self.search_users)
        searchLayout.addWidget(self.searchEdit)

        self.searchBtn = QPushButton("搜索")
        self.searchBtn.clicked.connect(self.search_users)
        searchLayout.addWidget(self.searchBtn)
        layout.addLayout(searchLayout)

        # 数据表格
        self.table = QTableWidget(0, 6)
        self.table.setShowGrid(True)  # 显示网格线
        self.table.setHorizontalHeaderLabels([
            "用户姓名", "员工工号", "系统操作权限", "系统权限名", "用户开通时间", "用户状态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
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
        self.table.setShowGrid(True)  # 显示网格线
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        self.refresh_table()

    def setup_permissions(self, user):
        """设置权限控制"""
        self.current_user = user or {}
        
        # 检查查看权限
        can_view = has_permission(user, "users.view")
        if not can_view:
            self.setEnabled(False)
            return
            
        # 检查创建权限
        can_create = has_permission(user, "users.create")
        self.addBtn.setEnabled(can_create)
        if not can_create:
            self.addBtn.setToolTip("您没有新增用户的权限")
            
        # 检查修改权限
        can_update = has_permission(user, "users.update")
        self.editBtn.setEnabled(can_update)
        if not can_update:
            self.editBtn.setToolTip("您没有编辑用户的权限")
            
        # 检查删除权限
        can_delete = has_permission(user, "users.delete")
        self.deleteBtn.setEnabled(can_delete)
        if not can_delete:
            self.deleteBtn.setToolTip("您没有删除用户的权限")
            
        # 检查导入权限
        can_import = has_permission(user, "users.import")
        self.importBtn.setEnabled(can_import)
        if not can_import:
            self.importBtn.setToolTip("您没有导入用户的权限")
            
        # 检查导出权限
        can_export = has_permission(user, "users.export")
        self.exportBtn.setEnabled(can_export)
        if not can_export:
            self.exportBtn.setToolTip("您没有导出用户的权限")
            
        # 检查重置密码权限
        can_reset_password = has_permission(user, "users.reset_password")
        self.resetPasswordBtn.setEnabled(can_reset_password)
        if not can_reset_password:
            self.resetPasswordBtn.setToolTip("您没有重置用户密码的权限")
            
        # 检查下载模板权限
        can_download_template = has_permission(user, "users.download_template")
        self.templateBtn.setEnabled(can_download_template)
        if not can_download_template:
            self.templateBtn.setToolTip("您没有下载用户模板的权限")
            
        print(f"用户权限管理模块权限设置完成 - 用户: {user.get('username', 'unknown')}, 查看: {can_view}, 新增: {can_create}, 编辑: {can_update}, 删除: {can_delete}, 导入: {can_import}, 导出: {can_export}, 重置密码: {can_reset_password}, 下载模板: {can_download_template}")

    def refresh_table(self):
        """刷新用户列表"""
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.full_name, u.username, s.employee_id, 
                       GROUP_CONCAT(r.name) as roles, u.created_at, u.is_active
                FROM users u
                LEFT JOIN staff s ON u.staff_id = s.id
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                GROUP BY u.id, u.full_name, u.username, s.employee_id, u.created_at, u.is_active
                ORDER BY u.created_at DESC
            """)
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                # 用户姓名
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row[1] or "")))
                # 员工工号
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row[3] or row[2] or "")))
                # 员工职级（从角色转换）- 确保实时反映最新角色
                current_roles = str(row[4] or "")
                role_name = self._get_role_level(current_roles)
                self.table.setItem(row_idx, 2, QTableWidgetItem(role_name))
                # 系统权限名
                permissions = current_roles if current_roles else "无权限"
                self.table.setItem(row_idx, 3, QTableWidgetItem(permissions))
                # 用户开通时间
                created_date = str(row[5] or "")[:10]
                self.table.setItem(row_idx, 4, QTableWidgetItem(created_date))
                # 用户状态
                status = "启用" if row[6] else "禁用"
                self.table.setItem(row_idx, 5, QTableWidgetItem(status))
                
            conn.close()
            
        except Exception as e:
            # 确保连接关闭
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            QMessageBox.critical(self, "错误", f"刷新用户列表失败: {e}")

    def _get_role_level(self, roles_str):
        """将角色转换为职级"""
        if not roles_str:
            return "系统浏览者"
        
        roles = roles_str.split(',')
        if 'admin' in roles:
            return "系统管理员"
        elif 'manager' in roles:
            return "部门经理"
        elif 'operator' in roles:
            return "系统操作员"
        elif 'viewer' in roles or 'general_user' in roles:
            return "系统浏览者"
        else:
            return "系统浏览者"

    def add_user(self):
        """添加用户"""
        dialog = UserDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            user_data = dialog.get_data()
            try:
                # 准备用户创建参数
                create_params = {
                    'username': user_data['employee_id'],
                    'password': user_data['password'],
                    'full_name': user_data['full_name'],
                    'email': user_data.get('email'),
                    'roles': [user_data['role']]
                }
                
                # 如果有员工ID则添加到参数中
                if 'staff_id' in user_data:
                    create_params['staff_id'] = user_data['staff_id']
                
                result = auth_manager.create_user(**create_params)
                
                if result['success']:
                    QMessageBox.information(self, "成功", "用户添加成功！")
                    self.refresh_table()
                else:
                    QMessageBox.warning(self, "失败", f"添加用户失败: {result['error']}")
                    
            except Exception as e:
                QMessageBox.warning(self, "失败", f"添加用户失败: {str(e)}")

    def edit_user(self):
        """编辑用户"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要编辑的用户！")
            return

        # 获取用户ID
        employee_id = self.table.item(row, 1).text()
        
        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
            cursor = conn.cursor()
            
            # 修复：通过员工工号或用户名查找用户
            cursor.execute("""
                SELECT u.id, u.full_name, u.username, u.email, u.is_active, s.employee_id, GROUP_CONCAT(r.name) as roles 
                FROM users u 
                LEFT JOIN staff s ON u.staff_id = s.id 
                LEFT JOIN user_roles ur ON u.id = ur.user_id 
                LEFT JOIN roles r ON ur.role_id = r.id 
                WHERE u.username = ? OR s.employee_id = ?
                GROUP BY u.id
            """, (employee_id, employee_id))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data:
                # 设置当前角色
                current_role = "普通员工"  # 默认值
                if user_data[6]:
                    roles = user_data[6].split(',')
                    if 'admin' in roles:
                        current_role = "系统管理员"
                    elif 'manager' in roles:
                        current_role = "部门经理"
                    elif 'operator' in roles:
                        current_role = "操作员"
                    elif 'viewer' in roles or 'general_user' in roles:
                        current_role = "普通员工"
                
                dialog = UserDialog(self, is_edit=True, user_data={
                    'id': user_data[0],
                    'full_name': user_data[1],
                    'employee_id': user_data[2],  # 用户名作为员工工号
                    'email': user_data[3],
                    'is_active': bool(user_data[4]) if user_data[4] is not None else True,
                    'current_role': current_role
                })
                
                if dialog.exec_() == QDialog.Accepted:
                    updated_data = dialog.get_data()
                    try:
                        # 更新用户信息
                        conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
                        cursor = conn.cursor()
                        
                        # 更新用户基本信息
                        cursor.execute(
                            "UPDATE users SET full_name = ?, email = ?, is_active = ? WHERE id = ?",
                            (updated_data['full_name'], updated_data['email'], updated_data['is_active'], user_data[0])
                        )
                        
                        # 删除现有角色
                        cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_data[0],))
                        
                        # 添加新角色 - 增加调试和错误处理
                        if updated_data.get('role'):
                            cursor.execute("SELECT id FROM roles WHERE name = ?", (updated_data['role'],))
                            role_result = cursor.fetchone()
                            if role_result:
                                # 确保user_id不为空
                                if user_data[0] is not None and role_result[0] is not None:
                                    cursor.execute(
                                        "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                                        (user_data[0], role_result[0])
                                    )
                                else:
                                    raise Exception(f"用户ID或角色ID为空: user_id={user_data[0]}, role_id={role_result[0]}")
                            else:
                                raise Exception(f"未找到角色: {updated_data['role']}")
                        else:
                            raise Exception("角色信息为空")
                        
                        conn.commit()
                        conn.close()
                        
                        QMessageBox.information(self, "成功", "用户信息已更新！")
                        self.refresh_table()
                        
                    except Exception as e:
                        QMessageBox.warning(self, "失败", f"更新用户失败: {str(e)}")
                    
        except Exception as e:
            QMessageBox.warning(self, "失败", f"编辑用户失败: {str(e)}")

    def delete_user(self):
        """删除用户"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的用户！")
            return

        user_name = self.table.item(row, 0).text()
        employee_id = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "确认删除", 
                                   f"确定要删除用户：{user_name}({employee_id}) 吗？", 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
                cursor = conn.cursor()
                
                # 先获取用户ID
                cursor.execute("SELECT id FROM users WHERE username = ?", (employee_id,))
                user_result = cursor.fetchone()
                
                if user_result:
                    user_id = user_result[0]
                    
                    # 删除用户的角色分配记录
                    cursor.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
                    
                    # 删除用户记录
                    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(self, "成功", "用户删除成功！")
                    self.refresh_table()
                else:
                    conn.close()
                    QMessageBox.warning(self, "失败", "未找到要删除的用户")
                
            except Exception as e:
                # 确保连接关闭
                try:
                    if 'conn' in locals():
                        conn.close()
                except:
                    pass
                QMessageBox.warning(self, "失败", f"删除用户失败: {str(e)}")

    def search_users(self):
        """搜索用户"""
        search_term = self.searchEdit.text().strip()
        if not search_term:
            self.refresh_table()
            return

        try:
            conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT u.id, u.full_name, u.username, s.employee_id, GROUP_CONCAT(r.name) as roles, 
                       u.created_at, u.is_active
                FROM users u
                LEFT JOIN staff s ON u.staff_id = s.id
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                WHERE u.full_name LIKE ? OR u.username LIKE ? OR s.employee_id LIKE ?
                GROUP BY u.id
                ORDER BY u.created_at DESC
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))
            
            for row_idx, row in enumerate(rows):
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(row[1] or "")))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(row[3] or row[2] or "")))
                role_name = self._get_role_level(str(row[4] or ""))
                self.table.setItem(row_idx, 2, QTableWidgetItem(role_name))
                permissions = str(row[4] or "无权限")
                self.table.setItem(row_idx, 3, QTableWidgetItem(permissions))
                created_date = str(row[5] or "")[:10]
                self.table.setItem(row_idx, 4, QTableWidgetItem(created_date))
                status = "启用" if row[6] else "禁用"
                self.table.setItem(row_idx, 5, QTableWidgetItem(status))
                
            conn.close()
            
        except Exception as e:
            # 确保连接关闭
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            QMessageBox.critical(self, "错误", f"搜索用户失败: {e}")

    def export_users(self):
        """导出用户数据"""
        try:
            filepath = export_manager.export_users_to_csv()
            QMessageBox.information(self, "成功", f"用户数据已导出到:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"导出用户数据失败: {str(e)}")

    def import_users(self):
        """导入用户数据"""
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self, 
                "选择用户数据文件", 
                export_manager.export_dir,
                "CSV文件 (*.csv)"
            )
            
            if filepath:
                result = export_manager.import_from_csv(filepath, 'users')
                
                if result['success']:
                    QMessageBox.information(self, "成功", 
                                          f"成功导入 {result['success_count']} 条用户数据")
                    self.refresh_table()
                else:
                    error_msg = '\n'.join(result.get('errors', [result.get('error', '未知错误')]))
                    QMessageBox.warning(self, "失败", f"导入失败:\n{error_msg}")
                    
        except Exception as e:
            QMessageBox.warning(self, "失败", f"导入用户数据失败: {str(e)}")

    def reset_password(self):
        """重置用户密码"""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要重置密码的用户！")
            return

        user_name = self.table.item(row, 0).text()
        employee_id = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "确认重置密码", 
                                   f"确定要重置用户 {user_name}({employee_id}) 的密码吗？\n\n新密码将设置为：123456\n\n请提醒用户登录后立即修改密码。", 
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                from utils.auth import auth_manager
                
                # 重置密码为123456
                new_password = "123456"
                
                conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db'))
                cursor = conn.cursor()
                
                # 获取用户ID - 修复：通过员工工号或用户名查找用户
                cursor.execute("""
                    SELECT u.id FROM users u 
                    LEFT JOIN staff s ON u.staff_id = s.id 
                    WHERE u.username = ? OR s.employee_id = ?
                """, (employee_id, employee_id))
                user_result = cursor.fetchone()
                
                if user_result:
                    user_id = user_result[0]
                    
                    # 使用auth_manager的密码更新功能
                    from utils.security import security_manager
                    new_hash = security_manager.hash_password(new_password)
                    
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (new_hash, user_id)
                    )
                    conn.commit()
                    conn.close()
                    
                    QMessageBox.information(self, "成功", f"密码重置成功！\n\n用户：{user_name}({employee_id})\n新密码：{new_password}\n\n请通知用户及时修改密码。")
                else:
                    conn.close()
                    QMessageBox.warning(self, "失败", "未找到该用户")
                    
            except Exception as e:
                # 确保连接关闭
                try:
                    if 'conn' in locals():
                        conn.close()
                except:
                    pass
                QMessageBox.warning(self, "失败", f"重置密码失败: {str(e)}")

    def download_template(self):
        """下载用户导入模板"""
        try:
            filepath = export_manager.generate_template('users', 'csv')
            QMessageBox.information(self, "成功", f"用户导入模板已生成:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"生成模板失败: {str(e)}")

class UserDialog(QDialog):
    def __init__(self, parent=None, is_edit=False, user_data=None):
        super().__init__(parent)
        self.is_edit = is_edit
        self.parent = parent  # 保存父窗口引用
        self.setWindowTitle("编辑用户" if is_edit else "新增用户")
        self.resize(400, 350)
        
        layout = QFormLayout(self)
        
        # 获取所有员工信息（仅在新增模式下）
        self.staff_list = []
        if not is_edit and parent:
            self.staff_list = parent.get_all_staff()
        
        # 用户姓名
        if self.staff_list and not is_edit:
            # 使用下拉选择员工姓名
            self.full_name_combo = QComboBox()
            self.full_name_combo.addItem("请选择员工姓名", None)
            for staff in self.staff_list:
                self.full_name_combo.addItem(f"{staff[1]} ({staff[2]})", staff)
            self.full_name_combo.currentIndexChanged.connect(self.on_staff_selected)
            self.full_name_edit = None  # 不使用文本输入框
        else:
            # 使用文本输入框
            self.full_name_edit = QLineEdit()
            self.full_name_edit.setPlaceholderText("请输入用户姓名")
            if user_data:
                self.full_name_edit.setText(user_data.get('full_name', ''))
            self.full_name_combo = None  # 不使用下拉选择
        
        # 员工工号
        if self.staff_list and not is_edit:
            # 工号将根据选择的员工自动填充
            self.employee_id_edit = QLineEdit()
            self.employee_id_edit.setPlaceholderText("员工工号将自动填充")
            self.employee_id_edit.setEnabled(False)
        else:
            self.employee_id_edit = QLineEdit()
            self.employee_id_edit.setPlaceholderText("请输入员工工号")
            if user_data:
                self.employee_id_edit.setText(user_data.get('employee_id', ''))
            if is_edit:
                self.employee_id_edit.setEnabled(False)
        
        # 密码（新增时必填）
        if not is_edit:
            self.password_edit = QLineEdit()
            self.password_edit.setPlaceholderText("请输入密码")
            self.password_edit.setEchoMode(QLineEdit.Password)
        
        # 系统操作权限
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "系统管理员",
            "部门经理", 
            "系统操作员",
            "系统浏览者"
        ])
        
        # 如果是编辑模式设置当前角色
        if user_data and 'current_role' in user_data:
            index = self.role_combo.findText(user_data['current_role'])
            if index >= 0:
                self.role_combo.setCurrentIndex(index)
        
        # 邮箱
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("请输入邮箱(可选)")
        if user_data:
            self.email_edit.setText(user_data.get('email', ''))
        
        # 用户状态
        self.status_check = QCheckBox("启用用户")
        self.status_check.setChecked(True)
        if user_data:
            is_active = user_data.get('is_active', True)
            if is_active is not None:
                self.status_check.setChecked(bool(is_active))
            else:
                self.status_check.setChecked(True)
        
        # 添加表单字段
        if self.full_name_combo:
            layout.addRow("用户姓名*", self.full_name_combo)
        else:
            layout.addRow("用户姓名*", self.full_name_edit)
        layout.addRow("员工工号*", self.employee_id_edit)
        if not is_edit:
            layout.addRow("密码*", self.password_edit)
        layout.addRow("系统操作权限*", self.role_combo)
        layout.addRow("邮箱", self.email_edit)
        layout.addRow("用户状态", self.status_check)
        
        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)
    
    def on_staff_selected(self, index):
        """当选择员工时自动填充工号"""
        if index > 0 and self.staff_list:
            selected_staff = self.staff_list[index-1]  # 第一个是"请选择"所以要减1
            self.employee_id_edit.setText(selected_staff[2])  # 填充工号
        else:
            self.employee_id_edit.setText("")  # 清空工号
    
    def get_data(self):
        """获取表单数据"""
        role_mapping = {
            "系统管理员": "admin",
            "部门经理": "manager",
            "系统操作员": "operator",
            "系统浏览者": "viewer"  # 确保数据库中存在viewer角色或改为general_user
        }
        
        # 获取用户姓名
        if self.full_name_combo:
            # 从下拉选择中获取姓名
            current_index = self.full_name_combo.currentIndex()
            if current_index > 0 and self.staff_list:
                selected_staff = self.staff_list[current_index-1]
                full_name = selected_staff[1]
                staff_id = selected_staff[0]  # 获取员工ID
            else:
                full_name = ""
                staff_id = None
        else:
            # 从文本输入框获取姓名
            full_name = self.full_name_edit.text().strip()
            staff_id = None
        
        data = {
            'full_name': full_name,
            'employee_id': self.employee_id_edit.text().strip(),
            'role': role_mapping[self.role_combo.currentText()],
            'email': self.email_edit.text().strip(),
            'is_active': self.status_check.isChecked()
        }
        
        # 如果有员工ID则添加到数据中
        if staff_id:
            data['staff_id'] = staff_id
        
        if not hasattr(self, 'password_edit'):
            data['password'] = 'default123'  # 编辑时的默认密码
        else:
            data['password'] = self.password_edit.text()
            
        return data