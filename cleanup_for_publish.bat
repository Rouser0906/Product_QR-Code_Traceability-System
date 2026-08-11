@echo off
REM 发布前清理脚本 - Windows批处理版本
REM 调用PowerShell脚本执行清理

echo ========================================
echo   项目发布前清理脚本
echo ========================================
echo.

set SCRIPT_DIR=%~dp0

REM 检查是否传入了参数
if "%1"=="--dry-run" (
    echo 运行模拟模式...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%cleanup_for_publish.ps1" -DryRun
) else if "%1"=="--keep-legacy" (
    echo 保留遗留代码目录...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%cleanup_for_publish.ps1" -KeepLegacy
) else if "%1"=="--help" (
    echo 使用方法:
    echo   cleanup_for_publish.bat           执行完整清理
    echo   cleanup_for_publish.bat --dry-run 模拟运行，不实际删除
    echo   cleanup_for_publish.bat --keep-legacy 保留遗留代码目录
    echo   cleanup_for_publish.bat --help    显示此帮助信息
) else (
    echo 开始执行清理...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%cleanup_for_publish.ps1"
)

echo.
pause
