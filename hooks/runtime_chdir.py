# -*- coding: utf-8 -*-
"""
PyInstaller runtime hook: set CWD to executable directory and expose base paths.
This helps legacy code using relative paths (assets, cloud, etc.).
"""
import os, sys
try:
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
    else:
        exe_dir = os.path.dirname(os.path.abspath(__file__))
        exe_dir = os.path.abspath(os.path.join(exe_dir, '..'))
    os.chdir(exe_dir)
    os.environ['APP_BASE_DIR'] = exe_dir
    # Common resource dirs
    internal_dir = os.path.join(exe_dir, '_internal')
    assets_dir = os.path.join(exe_dir, 'assets')
    if not os.path.isdir(assets_dir):
        # fallback to _internal/assets
        assets_dir = os.path.join(internal_dir, 'assets')
    os.environ['ASSETS_DIR'] = assets_dir
except Exception:
    pass
