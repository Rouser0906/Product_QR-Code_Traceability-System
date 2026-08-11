import os, sys
# 确保项目根路径在 sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sqlite3

def main():
    # 数据库可用性检查
    db_path = os.path.join(BASE_DIR, 'qr_system.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    conn.close()

    # UI 构造烟测（不显示窗口）
    app = QApplication.instance() or QApplication([])
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    import welcome
    from welcome import WelcomeWindow
    from main_system import MainSystemWindow

    w = WelcomeWindow()
    m = MainSystemWindow(current_user={'username': 'admin', 'user_id': 1})

    # 清理并退出
    del w, m
    print('UI_SMOKETEST_OK', len(tables))

if __name__ == '__main__':
    main()