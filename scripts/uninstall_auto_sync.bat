@echo off
title 卸载自动同步服务
echo ========================================
echo 卸载自动同步服务
echo ========================================
echo.

set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\自动同步JSON文件.lnk"

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo ✓ 已从开机启动项中移除自动同步服务
) else (
    echo ℹ 开机启动项中没有找到自动同步服务
)

echo.
echo 卸载完成！
echo 按任意键退出...
pause >nul