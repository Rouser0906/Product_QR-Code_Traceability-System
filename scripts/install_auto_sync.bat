@echo off
title 安装自动同步服务
echo ========================================
echo 安装自动同步服务到系统启动项
echo ========================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SCRIPT_PATH=%~dp0smart_auto_sync.bat"
set "SHORTCUT_PATH=%STARTUP_DIR%\自动同步JSON文件.lnk"

echo 正在创建启动快捷方式...

powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%SCRIPT_PATH%'; $Shortcut.WorkingDirectory = '%~dp0'; $Shortcut.WindowStyle = 7; $Shortcut.Description = '自动同步JSON文件到服务器'; $Shortcut.Save()"

if exist "%SHORTCUT_PATH%" (
    echo ? 安装成功！
    echo.
    echo 现在每次开机都会自动启动同步服务。
    echo 快捷方式已创建在: %SHORTCUT_PATH%
    echo.
    echo 您也可以随时双击 smart_auto_sync.bat 手动启动服务。
) else (
    echo ? 安装失败！请检查权限。
)

echo.
echo 按任意键退出...
pause >nul