@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: 一键服务器端清理与初始化部署脚本（管理员运行）
:: 功能：
::   1) 删除历史/错误目录
::   2) 创建目标目录结构
::   3) 拷贝核心文件（若已在同一目录执行，可用 xcopy/robocopy 按需调整）
::   4) 设置 JSON MIME（依赖 web.config 已内置）
::   5) 重启 IIS

:: [可调参数] 项目源目录（如果脚本与 web.config / api / config 在同一目录，可将 SRC 设置为当前目录）
set "SRC=%~dp0..\"

:: 目标站点根目录
set "DST_ROOT=C:\inetpub\qr-system"
set "DST_COMP=%DST_ROOT%\companies"

:: 1) 删除历史/错误目录
if exist "%DST_COMP%\company_a\data" (
  echo [CLEAN] Removing %DST_COMP%\company_a\data
  rmdir /s /q "%DST_COMP%\company_a\data"
)
if exist "%DST_COMP%\company_b\data" (
  echo [CLEAN] Removing %DST_COMP%\company_b\data
  rmdir /s /q "%DST_COMP%\company_b\data"
)
if exist "%DST_COMP%\companies" (
  echo [CLEAN] Removing duplicated path %DST_COMP%\companies
  rmdir /s /q "%DST_COMP%\companies"
)
if exist "%DST_ROOT%\data\qr" (
  echo [CLEAN] Removing legacy path %DST_ROOT%\data\qr
  rmdir /s /q "%DST_ROOT%\data\qr"
)

:: 2) 创建目标目录
if not exist "%DST_COMP%\demo_json_a" mkdir "%DST_COMP%\demo_json_a"
if not exist "%DST_COMP%\demo_json_b" mkdir "%DST_COMP%\demo_json_b"
if not exist "%DST_COMP%\scripts" mkdir "%DST_COMP%\scripts"
if not exist "%DST_COMP%\_logs" mkdir "%DST_COMP%\_logs"

:: 3) 拷贝核心文件（按需修改源目录）
:: 确保目标子目录存在
if not exist "%DST_ROOT%\api" mkdir "%DST_ROOT%\api"
if not exist "%DST_ROOT%\config" mkdir "%DST_ROOT%\config"

:: 将仓库中的 web.config、api、config、展示页 拷贝至 IIS 站点
xcopy /y /f "%SRC%web.config" "%DST_ROOT%\" >nul 2>&1
xcopy /y /f "%SRC%qr\index.html" "%DST_ROOT%\index.html" >nul 2>&1
xcopy /y /f "%SRC%api\get_product_data.php" "%DST_ROOT%\api\" >nul 2>&1
xcopy /y /f "%SRC%config\performance_config.php" "%DST_ROOT%\config\" >nul 2>&1
xcopy /y /f "%SRC%scripts\server_cleanup_3years.ps1" "%DST_COMP%\scripts\" >nul 2>&1

:: 4) 重启 IIS
if exist "%windir%\system32\inetsrv\appcmd.exe" (
  echo [IIS] Recycling default app pool (if needed)...
  iisreset
) else (
  echo [WARN] IIS command-line tool not found. Please restart IIS manually.
)

echo.
echo [DONE] Server setup and cleanup completed.
echo Target root: %DST_ROOT%
echo JSON dirs : %DST_COMP%\demo_json_a , %DST_COMP%\demo_json_b
echo.
endlocal
