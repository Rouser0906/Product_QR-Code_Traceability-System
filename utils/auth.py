import sqlite3
import os
import hashlib
import secrets
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from utils.security import security_manager
from utils.logger import log_security, log_user_action

class UserManager:
    """用户管理系统"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """初始化认证相关表"""
        try:
            # 使用WAL模式提高并发性能
            with sqlite3.connect(self.db_path, timeout=30) as conn:
                conn.execute('PRAGMA journal_mode=WAL;')
                conn.execute('PRAGMA synchronous=NORMAL;')
                conn.execute('PRAGMA cache_size=10000;')
                conn.execute('PRAGMA temp_store=MEMORY;')
                cursor = conn.cursor()
                
                # 用户表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    staff_id INTEGER,
                    is_active BOOLEAN DEFAULT 1,
                    failed_login_attempts INTEGER DEFAULT 0,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 角色表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS roles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        permissions TEXT, -- JSON格式的权限列表
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
            
            # 用户角色关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_by INTEGER,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
                )
            ''')
            
            # 会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # 审计日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    resource TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            ''')
            
            # 初始化默认角色
            self._init_default_roles(cursor)
            
            # 创建默认管理员用户
            self._init_default_admin(cursor)
            
            conn.commit()
            
        except Exception as e:
            print(f"初始化认证表失败: {e}")
            # 不要抛出异常，允许系统继续运行
    
    def _init_default_roles(self, cursor):
        """初始化默认角色"""
        default_roles = [
            {
                'name': 'admin',
                'description': '系统管理员，拥有所有权限',
                'permissions': json.dumps([
                    'system.manage',
                    'users.create', 'users.read', 'users.update', 'users.delete',
                    'roles.create', 'roles.read', 'roles.update', 'roles.delete',
                    'companies.*',
                    'departments.*',
                    'staff.*',
                    'products.*',
                    'qr.generate', 'qr.read', 'qr.update', 'qr.delete',
                    'reports.*',
                    'data.export', 'data.import',
                    'backup.create', 'backup.restore'
                ])
            },
            {
                'name': 'manager',
                'description': '部门经理，管理部门相关数据',
                'permissions': json.dumps([
                    'companies.read',
                    'departments.read', 'departments.update',
                    'staff.read', 'staff.create', 'staff.update',
                    'products.read', 'products.create', 'products.update',
                    'qr.generate', 'qr.read',
                    'reports.read',
                    'data.export'
                ])
            },
            {
                'name': 'operator',
                'description': '操作员，执行日常操作',
                'permissions': json.dumps([
                    'companies.read',
                    'departments.read',
                    'staff.read',
                    'products.read',
                    'qr.generate', 'qr.read',
                    'reports.read',
                    'data.export'
                ])
            },
            {
                'name': 'viewer',
                'description': '查看者，只能查看数据',
                'permissions': json.dumps([
                    'companies.read',
                    'departments.read',
                    'staff.read',
                    'products.read',
                    'qr.read',
                    'reports.read'
                ])
            },
            {
                'name': 'general_user',
                'description': '一般使用者，只能使用二维码打印功能',
                'permissions': json.dumps([
                    'qr.generate',
                    'companies.read',
                    'departments.read',
                    'staff.read',
                    'products.read'
                ])
            }
        ]
        
        for role in default_roles:
            cursor.execute(
                "INSERT OR IGNORE INTO roles (name, description, permissions) VALUES (?, ?, ?)",
                (role['name'], role['description'], role['permissions'])
            )
    
    def _init_default_admin(self, cursor):
        """创建默认管理员用户"""
        # 注意：首次登录后请立即修改密码！详见 SECURITY_SETUP.md
        username = "admin"
        password = "change_me_immediately"  # 默认密码，请在首次登录后立即修改！
        
        # 检查是否已存在管理员
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return
        
        password_hash = security_manager.hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, email) VALUES (?, ?, ?, ?)",
            (username, password_hash, "系统管理员", "admin@example.com")
        )
        
        user_id = cursor.lastrowid
        
        # 分配管理员角色
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        admin_role = cursor.fetchone()
        if admin_role:
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, admin_role[0])
            )
    
    def create_user(self, username: str, password: str, full_name: str, 
                   email: str = None, phone: str = None, roles: List[str] = None, staff_id: int = None) -> Dict[str, Any]:
        """创建新用户"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查用户名唯一性
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {'success': False, 'error': '用户名已存在'}
            
            # 不再检查邮箱唯一性
            # if email:
            #     cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            #     if cursor.fetchone():
            #         return {'success': False, 'error': '邮箱已存在'}
            
            # 创建用户
            password_hash = security_manager.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, email, phone, staff_id) VALUES (?, ?, ?, ?, ?, ?)",
                (username, password_hash, full_name, email, phone, staff_id)
            )
            
            user_id = cursor.lastrowid
            
            # 分配角色，如果没有指定角色，默认为一般使用者
            if roles:
                for role_name in roles:
                    cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
                    role = cursor.fetchone()
                    if role:
                        cursor.execute(
                            "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                            (user_id, role[0])
                        )
            else:
                # 默认分配"一般使用者"角色
                cursor.execute("SELECT id FROM roles WHERE name = 'general_user'")
                role = cursor.fetchone()
                if role:
                    cursor.execute(
                        "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                        (user_id, role[0])
                    )
            
            conn.commit()
            conn.close()
            
            log_user_action(user_id, "USER_CREATED", details={
                'username': username,
                'full_name': full_name,
                'email': email,
                'roles': roles or [],
                'staff_id': staff_id
            })
            
            return {'success': True, 'user_id': user_id}
            
        except Exception as e:
            log_security(f"创建用户失败: {str(e)}", user=username)
            return {'success': False, 'error': str(e)}
    
    def authenticate_user(self, username: str, password: str, 
                         ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """用户认证"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 获取用户信息
                cursor.execute(
                    "SELECT id, password_hash, is_active, failed_login_attempts FROM users WHERE username = ?",
                    (username,)
                )
                user = cursor.fetchone()

                if not user:
                    log_security("登录失败：用户不存在", user=username, ip_address=ip_address)
                    return {'success': False, 'error': '用户名或密码错误'}

                user_id, password_hash, is_active, failed_attempts = user

                if not is_active:
                    log_security("登录失败：用户被禁用", user=username, ip_address=ip_address)
                    return {'success': False, 'error': '账户已被禁用'}

                # 验证密码
                if not security_manager.verify_password(password, password_hash):
                    # 增加失败次数
                    new_attempts = failed_attempts + 1
                    cursor.execute(
                        "UPDATE users SET failed_login_attempts = ? WHERE id = ?",
                        (new_attempts, user_id)
                    )
                    conn.commit()

                    log_security("登录失败：密码错误", user=username, 
                               ip_address=ip_address, details={'failed_attempts': new_attempts})

                    if new_attempts >= 5:
                        # 锁定账户
                        cursor.execute(
                            "UPDATE users SET is_active = 0 WHERE id = ?",
                            (user_id,)
                        )
                        conn.commit()
                        log_security("账户被锁定：失败次数过多", user=username, ip_address=ip_address)

                    return {'success': False, 'error': '用户名或密码错误'}

                # 重置失败次数
                cursor.execute(
                    "UPDATE users SET failed_login_attempts = 0, last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )

                # 创建会话
                session_token = security_manager.generate_secure_token()
                expires_at = datetime.now() + timedelta(hours=24)

                cursor.execute(
                    "INSERT INTO sessions (user_id, session_token, ip_address, user_agent, expires_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, session_token, ip_address, user_agent, expires_at)
                )

                conn.commit()
            
            # 暂时注释掉日志记录以避免阻塞
            # log_user_action(username, "USER_LOGIN", ip_address=ip_address)
            print(f"用户 {username} 登录成功 (日志记录已跳过)")
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'session_token': session_token,
                'expires_at': expires_at
            }
            
        except Exception as e:
            # 确保连接关闭
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            log_security(f"认证失败: {str(e)}", user=username, ip_address=ip_address)
            return {'success': False, 'error': str(e)}
    
    def validate_session(self, session_token: str) -> Dict[str, Any]:
        """验证会话"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """SELECT s.user_id, s.expires_at, u.username, u.full_name, u.is_active
                       FROM sessions s
                       JOIN users u ON s.user_id = u.id
                       WHERE s.session_token = ? AND s.is_active = 1""",
                    (session_token,)
                )

                session = cursor.fetchone()

                if not session:
                    return {'valid': False, 'error': '会话不存在'}

                user_id, expires_at, username, full_name, is_active = session

                if not is_active:
                    return {'valid': False, 'error': '用户已被禁用'}

                if datetime.fromisoformat(expires_at) < datetime.now():
                    # 会话过期
                    cursor.execute(
                        "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
                        (session_token,)
                    )
                    conn.commit()
                    return {'valid': False, 'error': '会话已过期'}

            return {
                'valid': True,
                'user_id': user_id,
                'username': username,
                'full_name': full_name
            }
            
        except Exception as e:
            # 确保连接关闭
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            log_security(f"会话验证失败: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def logout_user(self, session_token: str) -> bool:
        """用户登出"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE sessions SET is_active = 0 WHERE session_token = ?",
                (session_token,)
            )
            
            conn.commit()
            conn.close()
            
            log_user_action(None, "USER_LOGOUT", details={'session_token': session_token})
            return True
            
        except Exception as e:
            # 确保连接关闭
            try:
                if 'conn' in locals():
                    conn.close()
            except:
                pass
            log_security(f"登出失败: {str(e)}")
            return False
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT r.permissions
                   FROM roles r
                   JOIN user_roles ur ON r.id = ur.role_id
                   WHERE ur.user_id = ?""",
                (user_id,)
            )
            
            permissions = set()
            for (permissions_json,) in cursor.fetchall():
                if permissions_json:
                    role_permissions = json.loads(permissions_json)
                    permissions.update(role_permissions)
            
            conn.close()
            return list(permissions)
            
        except Exception as e:
            log_security(f"获取用户权限失败: {str(e)}", user_id=user_id)
            return []
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """检查用户是否有特定权限"""
        permissions = self.get_user_permissions(user_id)
        
        # 支持通配符权限
        for perm in permissions:
            if perm == permission or (perm.endswith('.*') and permission.startswith(perm[:-2])):
                return True
        
        return False
    
    def get_user_roles(self, user_id: int) -> List[str]:
        """获取用户角色列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """SELECT r.name
                   FROM roles r
                   JOIN user_roles ur ON r.id = ur.role_id
                   WHERE ur.user_id = ?""",
                (user_id,)
            )
            
            roles = [row[0] for row in cursor.fetchall()]
            conn.close()
            return roles
            
        except Exception as e:
            log_security(f"获取用户角色失败: {str(e)}", user_id=user_id)
            return []
    
    def get_role_permissions(self, role_name: str) -> List[str]:
        """获取角色权限列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT permissions FROM roles WHERE name = ?",
                (role_name,)
            )
            
            result = cursor.fetchone()
            if result and result[0]:
                permissions = json.loads(result[0])
                conn.close()
                return permissions
            
            conn.close()
            return []
            
        except Exception as e:
            log_security(f"获取角色权限失败: {str(e)}")
            return []
    
    def check_permission(self, session_token: str, permission: str) -> bool:
        """检查会话权限"""
        session = self.validate_session(session_token)
        if not session['valid']:
            return False
        
        return self.has_permission(session['user_id'], permission)
    
    def log_user_action(self, user_id: int, action: str, resource: str = None, 
                       resource_id: str = None, details: Dict = None, 
                       ip_address: str = None, user_agent: str = None):
        """记录用户操作"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """INSERT INTO audit_log (user_id, action, resource, resource_id, 
                                       details, ip_address, user_agent)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, action, resource, resource_id, 
                 json.dumps(details) if details else None, 
                 ip_address, user_agent)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            log_security(f"记录用户操作失败: {str(e)}")
    
    def get_audit_logs(self, user_id: int = None, action: str = None, 
                      start_date: datetime = None, end_date: datetime = None,
                      limit: int = 1000) -> List[Dict[str, Any]]:
        """获取审计日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """SELECT al.*, u.username, u.full_name
                      FROM audit_log al
                      LEFT JOIN users u ON al.user_id = u.id
                      WHERE 1=1"""
            params = []
            
            if user_id:
                query += " AND al.user_id = ?"
                params.append(user_id)
            
            if action:
                query += " AND al.action = ?"
                params.append(action)
            
            if start_date:
                query += " AND al.timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND al.timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY al.timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'id': row[0],
                    'user_id': row[1],
                    'action': row[2],
                    'resource': row[3],
                    'resource_id': row[4],
                    'details': json.loads(row[5]) if row[5] else None,
                    'ip_address': row[6],
                    'user_agent': row[7],
                    'timestamp': row[8],
                    'username': row[9],
                    'full_name': row[10]
                })
            
            conn.close()
            return logs
            
        except Exception as e:
            log_security(f"获取审计日志失败: {str(e)}")
            return []

# 延迟初始化auth_manager
_auth_manager = None

def get_database_path():
    """获取数据库文件路径，兼容EXE和源码环境"""
    import sys
    
    if getattr(sys, 'frozen', False):
        # EXE环境：数据库在可执行文件同目录
        application_path = os.path.dirname(sys.executable)
        db_path = os.path.join(application_path, 'qr_system.db')
    else:
        # 源码环境：数据库在项目根目录
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qr_system.db')
    
    # 如果数据库不存在，尝试其他可能位置
    if not os.path.exists(db_path):
        # 尝试当前工作目录
        alt_path = os.path.join(os.getcwd(), 'qr_system.db')
        if os.path.exists(alt_path):
            db_path = alt_path
        else:
            # 尝试脚本所在目录
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path2 = os.path.join(os.path.dirname(script_dir), 'qr_system.db')
            if os.path.exists(alt_path2):
                db_path = alt_path2
    
    return db_path

def get_auth_manager():
    """获取auth_manager实例，使用延迟初始化"""
    global _auth_manager
    if _auth_manager is None:
        db_path = get_database_path()
        _auth_manager = UserManager(db_path)
    return _auth_manager

# 向后兼容性 - 在首次访问时初始化
class _AuthManagerProxy:
    def __getattr__(self, name):
        return getattr(get_auth_manager(), name)

auth_manager = _AuthManagerProxy()