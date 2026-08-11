# -*- coding: utf-8 -*-
"""
统一的运行时路径修复工具（兼容源码与PyInstaller EXE）
使用 ensure_runtime_paths() 在程序启动与模块动态导入前调用，
统一修正工作目录与 sys.path，保证 modules 与 utils 可被稳定导入。
"""
import os
import sys
from typing import Tuple

def _detect_base_dir() -> Tuple[str, bool]:
    """返回(base_dir, is_exe)。
    - EXE 情况优先使用 _MEIPASS（PyInstaller临时目录）；
    - 源码情况使用当前文件上上级目录（项目根）。
    """
    if getattr(sys, 'frozen', False):  # PyInstaller
        # 强制使用 _MEIPASS，确保能找到打包的modules和utils
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return meipass, True
        # 如果没有_MEIPASS，回退到exe目录
        exe_dir = os.path.dirname(sys.executable)
        return exe_dir, True
    # 源码环境：runtime_paths.py -> utils -> project_root
    proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return proj_root, False

def ensure_runtime_paths(chdir: bool = True) -> str:
    """修复运行时路径，返回最终 base_dir。
    - 将 base_dir、base_dir/modules、base_dir/utils 插到 sys.path 前列。
    - 可选将 CWD 切到 base_dir，避免对话框/线程改变 CWD 导致导入失败。
    """
    base_dir, _ = _detect_base_dir()
    insert_paths = [
        base_dir,
        os.path.join(base_dir, 'modules'),
        os.path.join(base_dir, 'utils'),
    ]
    # 去重并插入到最前
    for p in reversed(insert_paths):
        if os.path.isdir(p):
            try:
                if p in sys.path:
                    sys.path.remove(p)
                sys.path.insert(0, p)
            except Exception:
                pass
    if chdir:
        try:
            os.chdir(base_dir)
        except Exception:
            pass
    return base_dir

if __name__ == '__main__':
    bd = ensure_runtime_paths()
    print('runtime_paths ensured, base_dir =', bd)
