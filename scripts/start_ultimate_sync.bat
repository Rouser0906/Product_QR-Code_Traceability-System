@echo off
chcp 65001 >nul
title 终极JSON文件同步守护程序

echo ============================================
echo     终极JSON文件同步守护程序
echo ============================================
echo.
echo 监控目录: C:\Projects\Demo\cloud\demo_json_a
echo 监控目录: C:\Projects\Demo\cloud\demo_json_b
echo 目标服务器: scan.example.com
echo.
echo 功能特点:
echo [√] 实时文件监控
echo [√] 定时扫描备份
echo [√] 自动重试机制
echo [√] 上传验证
echo [√] 详细日志记录
echo [√] 断线重连
echo.
echo 按任意键启动监控程序...
pause >nul

cd /d "%~dp0\.."
powershell -NoExit -ExecutionPolicy Bypass -File "scripts\ultimate_sync_guardian.ps1"