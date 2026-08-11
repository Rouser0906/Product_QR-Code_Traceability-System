@echo off
REM 强制同步所有文件（包括已存在的文件）
echo ========================================
echo 强制同步所有JSON文件到服务器
echo ========================================
echo 警告：这将重新上传所有文件，包括已存在的文件
echo.
set /p confirm=确定要继续吗？(Y/N): 
if /i "%confirm%" neq "Y" (
    echo 操作已取消
    pause
    exit /b
)

echo.
echo 开始强制同步...

cd /d "C:\Projects\Demo"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\auto_sync_to_server.ps1" -Mode "force"

echo.
echo 强制同步完成！按任意键退出...
pause >nul