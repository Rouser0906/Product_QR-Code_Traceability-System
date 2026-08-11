@echo off
setlocal
REM 以管理员身份启动 PowerShell 并执行安装脚本
set SCRIPT_DIR=%~dp0
set PS1=%SCRIPT_DIR%install_service_admin.ps1

powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process PowerShell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%PS1%""'"

endlocal
