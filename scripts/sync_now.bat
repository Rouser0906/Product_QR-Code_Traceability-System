@echo off
REM 立即执行一次同步
echo ========================================
echo 自动同步JSON文件到服务器
echo ========================================
echo.

cd /d "C:\Projects\Demo"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\auto_sync_to_server.ps1" -Mode "once"

echo.
echo 同步完成！按任意键退出...
pause >nul