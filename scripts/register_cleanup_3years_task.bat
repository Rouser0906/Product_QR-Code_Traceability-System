@echo off
REM 注册“3周年清理”计划任务（SYSTEM 用户，每天 03:00）
setlocal EnableExtensions
set "TASK=QR_Cleanup_3Years"
set "SCRIPT=C:\inetpub\qr-system\companies\scripts\server_cleanup_3years.bat"

schtasks /Create /TN "%TASK%" /TR "\"%SCRIPT%\"" /SC DAILY /ST 03:00 /RU SYSTEM /F
if %ERRORLEVEL% EQU 0 (
  echo [OK] Scheduled task created: %TASK%
) else (
  echo [ERR] Failed to create scheduled task. ErrorLevel=%ERRORLEVEL%
)
endlocal
