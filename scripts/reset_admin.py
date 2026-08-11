import os, sqlite3, sys
# 修复导入路径：将项目根目录加入 sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.security import security_manager

def main():
    db_path = os.path.join(BASE_DIR, 'qr_system.db')
    print('DB_PATH:', db_path)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # 检查 admin 是否存在
        cur.execute("SELECT id FROM users WHERE username=?", ('admin',))
        row = cur.fetchone()
        if not row:
            print('ADMIN_NOT_FOUND')
            conn.close()
            return
        user_id = row[0]
        # 重置密码、启用账户、清零失败次数
        new_hash = security_manager.hash_password('change_me_immediately')
        cur.execute("UPDATE users SET password_hash=?, is_active=1, failed_login_attempts=0 WHERE id=?", (new_hash, user_id))
        conn.commit()
        print('RESET_OK', user_id)
        conn.close()
    except Exception as e:
        print('RESET_ERROR:', str(e))

if __name__ == '__main__':
    main()