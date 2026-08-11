@echo off
chcp 65001 >nul
title JSON文件自动同步系统 - 一键部署

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo ❌ 需要管理员权限！
    echo.
    echo 请右键点击此文件，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

cls
echo ================================================================
echo                JSON文件自动同步系统 - 一键部署
echo ================================================================
echo.
echo 🎯 系统功能：
echo    • 实时监控本地JSON文件变化
echo    • 自动上传到云服务器
echo    • 开机自启动，24/7运行
echo    • 完善的错误重试和日志记录
echo.
echo 📁 监控目录：
echo    • C:\Projects\Demo\cloud\demo_json_a\  →  服务器demo_json_a目录
echo    • C:\Projects\Demo\cloud\demo_json_b\  →  服务器demo_json_b目录
echo.
echo 🌐 目标服务器：scan.example.com
echo.
echo ================================================================

:MENU
echo.
echo 请选择操作：
echo.
echo 1. 🚀 一键部署（推荐新用户）
echo 2. 🔧 安装同步服务
echo 3. ▶️  启动服务
echo 4. ⏹️  停止服务
echo 5. 🔄 重启服务
echo 6. 📊 检查状态
echo 7. 📋 查看日志
echo 8. 🧪 测试上传
echo 9. 🗑️  卸载服务
echo 0. 🚪 退出
echo.
set /p choice="请输入选项 (0-9): "

if "%choice%"=="1" goto FULL_DEPLOY
if "%choice%"=="2" goto INSTALL_SERVICE
if "%choice%"=="3" goto START_SERVICE
if "%choice%"=="4" goto STOP_SERVICE
if "%choice%"=="5" goto RESTART_SERVICE
if "%choice%"=="6" goto CHECK_STATUS
if "%choice%"=="7" goto VIEW_LOGS
if "%choice%"=="8" goto TEST_UPLOAD
if "%choice%"=="9" goto UNINSTALL_SERVICE
if "%choice%"=="0" goto EXIT

echo ❌ 无效选项，请重新输入
goto MENU

:FULL_DEPLOY
echo.
echo ========================================
echo           🚀 开始一键部署
echo ========================================
echo.

echo 📝 步骤1: 检查环境...
if not exist "C:\Projects\Demo\cloud\demo_json_a" (
    echo 📁 创建HS监控目录...
    mkdir "C:\Projects\Demo\cloud\demo_json_a" 2>nul
)
if not exist "C:\Projects\Demo\cloud\demo_json_b" (
    echo 📁 创建ZY监控目录...
    mkdir "C:\Projects\Demo\cloud\demo_json_b" 2>nul
)

echo 🔧 步骤2: 安装同步服务...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\install_sync_service_fixed.ps1" -Install
if %errorLevel% neq 0 (
    echo ❌ 服务安装失败！
    pause
    goto MENU
)

echo ✅ 步骤3: 验证安装...
timeout /t 3 /nobreak >nul
powershell -ExecutionPolicy Bypass -File "scripts\quick_sync_check_fixed.ps1"

echo 🧪 步骤4: 测试上传功能...
powershell -ExecutionPolicy Bypass -File "scripts\quick_sync_check_fixed.ps1" -TestUpload

echo.
echo ========================================
echo          🎉 部署完成！
echo ========================================
echo.
echo ✅ 同步服务已安装并启动
echo ✅ 监控目录已创建
echo ✅ 系统已配置为开机自启
echo.
echo 💡 提示：
echo    • 系统将自动监控JSON文件变化
echo    • 可随时使用选项6检查运行状态
echo    • 日志文件保存在auto_sync\logs目录
echo.
pause
goto MENU

:INSTALL_SERVICE
echo.
echo 🔧 安装同步服务...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\install_sync_service_fixed.ps1" -Install
pause
goto MENU

:START_SERVICE
echo.
echo ▶️ 启动服务...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\install_sync_service_fixed.ps1" -Start
pause
goto MENU

:STOP_SERVICE
echo.
echo ⏹️ 停止服务...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\install_sync_service_fixed.ps1" -Stop
pause
goto MENU

:RESTART_SERVICE
echo.
echo 🔄 重启服务...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\install_sync_service_fixed.ps1" -Restart
pause
goto MENU

:CHECK_STATUS
echo.
echo 📊 检查系统状态...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\quick_sync_check_fixed.ps1" -ShowDetails
pause
goto MENU

:VIEW_LOGS
echo.
echo 📋 查看最近日志...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\quick_sync_check_fixed.ps1" -ShowLogs
pause
goto MENU

:TEST_UPLOAD
echo.
echo 🧪 测试上传功能...
cd /d "%~dp0\.."
powershell -ExecutionPolicy Bypass -File "scripts\quick_sync_check_fixed.ps1" -TestUpload
pause
goto MENU

:UNINSTALL_SERVICE
echo.
echo ⚠️  确认卸载同步服务吗？
echo    这将停止所有自动同步功能。
echo.
set /p confirm="输入 Y 确认卸载: "
if /i "%confirm%"=="Y" (
    echo 🗑️ 卸载服务...
    cd /d "%~dp0\.."
    powershell -ExecutionPolicy Bypass -File "scripts\install_sync_service_fixed.ps1" -Uninstall
) else (
    echo 操作已取消
)
pause
goto MENU

:EXIT
echo.
echo 👋 感谢使用JSON文件自动同步系统！
echo.
echo 💡 系统将继续在后台运行，自动同步您的JSON文件。
echo    如需检查状态，请随时重新运行此程序。
echo.
timeout /t 3 /nobreak >nul
exit /b 0