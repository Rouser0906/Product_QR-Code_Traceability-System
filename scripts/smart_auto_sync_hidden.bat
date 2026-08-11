@echo off
REM 隐藏窗口启动自动同步服务
REM 解决空白PowerShell窗口问题

cd /d "%~dp0.."

REM 使用隐藏窗口启动PowerShell自动同步
powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -NoProfile -File "scripts\fixed_auto_sync.ps1"