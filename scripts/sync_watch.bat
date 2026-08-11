@echo off
REM 启动监控模式，持续监控并同步
echo ========================================
echo 启动自动同步监控模式
echo ========================================
echo 监控目录: C:\Projects\Demo\cloud\demo_json_a
echo 监控目录: C:\Projects\Demo\cloud\demo_json_b
echo 同步间隔: 30秒
echo 按 Ctrl+C 停止监控
echo ========================================
echo.

cd /d "C:\Projects\Demo"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\auto_sync_to_server.ps1" -Mode "watch" -WatchMode -IntervalSeconds 30

echo.
echo 监控已停止！按任意键退出...
pause >nul