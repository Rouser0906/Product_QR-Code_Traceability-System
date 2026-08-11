@echo off
REM 注册“每小时项目备份”计划任务（SYSTEM 用户，每小时执行一次）
setlocal EnableExtensions
set "TASK=Project_Hourly_Backup"
set "SCRIPT=%~dp0hourly_project_backup.bat"

schtasks /Create /TN "%TASK%" /TR "\"%SCRIPT%\"" /SC HOURLY /MO 1 /RU SYSTEM /F
if %ERRORLEVEL% EQU 0 (
  echo [OK] Scheduled task created: %TASK%
) else (
  echo [ERR] Failed to create scheduled task. ErrorLevel=%ERRORLEVEL%
)
endlocal
