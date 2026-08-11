import sqlite3
import os

def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'qr_system.db')
    db_path = os.path.abspath(db_path)
    print('DB_PATH:', db_path)
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print('TABLES:', tables)
        try:
            cur.execute("SELECT id, username, password_hash, is_active, failed_login_attempts FROM users WHERE username=?", ('admin',))
            admin_row = cur.fetchone()
            print('ADMIN_ROW:', admin_row)
        except Exception as e:
            print('ADMIN_QUERY_ERROR:', str(e))
        conn.close()
    except Exception as e:
        print('DB_ERROR:', str(e))

if __name__ == '__main__':
    main()