@echo off
chcp 65001 >nul
title JSON文件自动上传监控程序

echo ================================================================
echo                JSON文件自动上传监控程序
echo ================================================================
echo.
echo 🎯 监控目录:
echo    HS文件: C:\Projects\Demo\cloud\demo_json_a\
echo    ZY文件: C:\Projects\Demo\cloud\demo_json_b\
echo.
echo 🌐 上传目标: scan.example.com
echo.
echo 📋 功能特点:
echo    ✓ 实时监控新文件
echo    ✓ 自动上传到FTP服务器
echo    ✓ 详细日志记录
echo    ✓ 自动重试机制
echo.
echo ================================================================
echo 监控程序正在启动...
echo 请保持此窗口打开以维持监控功能
echo 按 Ctrl+C 可停止监控
echo ================================================================
echo.

cd /d "%~dp0\.."

:RESTART
echo [%date% %time%] 启动JSON文件监控...
powershell -ExecutionPolicy Bypass -Command "& '.\scripts\simple_monitor_loop.ps1'" 2>nul

echo.
echo [%date% %time%] 监控程序已停止，5秒后自动重启...
timeout /t 5 /nobreak >nul
goto RESTART