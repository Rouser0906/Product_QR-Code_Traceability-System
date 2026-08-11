@echo off
rem 一键重启 main.py 并实时观察上传结果
chcp 65001 >nul
echo 正在停止旧服务...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo 启动 JSON 自动同步服务...
cd /d "C:\Projects\qr-system"
start "" python main.py

timeout /t 5 /nobreak >nul
echo.
echo === 实时日志（按 Ctrl+C 退出） ===
echo.
:tail
powershell -command "& {Get-Content -Path 'logs\auto_sync.log' -Tail 30 -Wait}"
goto tail