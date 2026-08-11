@echo off
title 修复并启动二维码系统
echo ========================================
echo      二维码系统 - 修复并启动
echo ========================================
echo.

echo 正在检查系统环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装或未添加到PATH
    echo 请安装Python并添加到系统PATH
    pause
    exit /b 1
)

echo ✅ Python 环境正常
echo.

echo 正在检查数据库文件...
if not exist "qr_system.db" (
    echo ❌ 数据库文件 qr_system.db 不存在
    echo 请确保数据库文件在当前目录
    pause
    exit /b 1
)

echo ✅ 数据库文件存在
echo.

echo 正在启动系统（安全模式）...
echo 如果系统闪退，将显示详细错误信息
echo.

python safe_start.py

echo.
if errorlevel 1 (
    echo ❌ 系统启动失败
    echo 请联系技术支持或查看错误信息
) else (
    echo ✅ 系统已正常退出
)

echo.
pause