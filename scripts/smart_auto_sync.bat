@echo off
title 智能自动同步服务
echo ========================================
echo 智能自动同步服务
echo ========================================
echo 正在启动智能同步服务...
echo - 自动检测并同步现有文件
echo - 启动实时监控服务
echo - 一键完成所有操作
echo ========================================
echo.

cd /d "C:\Projects\Demo"

echo [1/2] 正在同步现有文件...
powershell -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -Command "& { $ErrorActionPreference='SilentlyContinue'; $w=New-Object System.Net.WebClient; $w.Credentials=New-Object System.Net.NetworkCredential('your_ftp_username','[REDACTED-FTP-PASSWORD]'); $count=0; Get-ChildItem 'cloud\demo_json_a\*.json' | ForEach { try { $w.UploadFile(\"ftp://192.0.2.100/companies/demo_json_a/$($_.Name)\", $_.FullName); $count++ } catch {} }; Get-ChildItem 'cloud\demo_json_b\*.json' | ForEach { try { $w.UploadFile(\"ftp://192.0.2.100/companies/demo_json_b/$($_.Name)\", $_.FullName); $count++ } catch {} }; $w.Dispose(); Write-Host \"已同步 $count 个文件\" }"

echo [2/2] 正在启动实时监控服务...
echo 服务已启动！现在会自动监控文件变化并立即上传。
echo 按Ctrl+C可以停止服务
echo ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\auto_sync_service.ps1"

echo.
echo 服务已停止。按任意键退出...
pause >nul