import sys, os

# 修复路径：将项目根目录加入 sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def safe_import(name):
    try:
        mod = __import__(name)
        return True, getattr(mod, '__version__', 'unknown')
    except Exception as e:
        return False, str(e)

results = {}
packages = [
    ('PyQt5', 'PyQt5'),
    ('qrcode', 'qrcode'),
    ('PIL', 'PIL'),
    ('netifaces', 'netifaces'),
    ('dotenv', 'dotenv'),
    ('watchdog', 'watchdog'),
]

for label, pkg in packages:
    ok, info = safe_import(pkg)
    results[label] = (ok, info)

# 验证核心模块导入（加入修复后的路径）
core_ok = True
core_errors = []
try:
    import welcome, main_system
except Exception as e:
    core_ok = False
    core_errors.append(str(e))

print('DEP_CHECK')
for k, v in results.items():
    print(f'{k}:', 'OK' if v[0] else 'FAIL', '|', v[1])
print('CORE_IMPORT:', 'OK' if core_ok else 'FAIL', '|', '; '.join(core_errors) if core_errors else '')

# 额外打印 PyQt5 组件可用性
try:
    from PyQt5.QtWidgets import QApplication
    print('PyQt5.QtWidgets: OK')
except Exception as e:
    print('PyQt5.QtWidgets: FAIL |', str(e))