# -*- mode: python ; coding: utf-8 -*-


from PyInstaller.utils.hooks import collect_data_files

qt_image_plugins = collect_data_files('PyQt5', includes=['Qt/plugins/imageformats/*'])

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # 核心资源
        ('assets', 'assets'),
        ('config/*.json', 'config'),
        # 仅收集 auto_sync 的代码与配置，排除 logs 等
        ('auto_sync/*.py', 'auto_sync'),
        ('auto_sync/*.json', 'auto_sync'),
        # PyQt5 图像插件（确保 QPixmap 能加载 PNG/JPEG）
        *qt_image_plugins,
        # 脚本白名单
        ('scripts/windows_ftp_json_uploader.ps1', 'scripts'),
        # 附属文档（输出到根目录）
        ('docs/系统使用说明书.md', '.'),
        ('docs/系统简介.txt', '.'),
        ('docs/readme.md', '.'),
        ('docs/版本号更新说明书.txt', '.'),
        ('share.md', '.'),
        # 数据库（若需要）
        ('qr_system.db', '.'),
    ],
    hiddenimports=[
        # PyQt5核心与打印
        'PyQt5.QtWidgets','PyQt5.QtCore','PyQt5.QtGui','PyQt5.QtPrintSupport',
        # QRCode 与 PIL
        'qrcode','qrcode.main','qrcode.image','qrcode.image.pil','qrcode.constants','qrcode.util',
        'PIL','PIL.Image','PIL.ImageDraw','PIL.ImageFont',
        # 项目核心模块（确保收集）
        'modules.qr_print_widget','main_system','welcome','utils.auth','utils.permissions',
        # 自动同步核心
        'auto_sync.auto_sync_service','auto_sync.file_watcher','auto_sync.event_queue',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/runtime_chdir.py'],
    excludes=['PyQt6','PySide2','PySide6','tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PT-QRC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PT-QRC'
)
