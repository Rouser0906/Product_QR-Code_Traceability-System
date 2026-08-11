@echo off
echo ========================================
echo 启动自动同步服务
echo ========================================
echo 这个服务将持续监控JSON文件变化并自动上传到服务器
echo 按Ctrl+C可以停止服务
echo ========================================
echo.

cd /d "C:\Projects\Demo"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\auto_sync_service.ps1" -Start

echo.
echo 服务已停止。按任意键退出...
pause >nul