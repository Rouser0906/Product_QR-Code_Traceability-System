@echo off
:: 健康检查：验证 web.config、API、JSON 与 CORS/MIME
:: 用法示例：
::   0_run_healthcheck.bat https://your-company-domain.com A-DEMO-000008726 a
::   0_run_healthcheck.bat https://your-company-domain.com B-DEMO-000000015 b
set BASE=%~1
set CODE=%~2
set COMPANY=%~3
if "%BASE%"=="" set BASE=https://your-company-domain.com
if "%COMPANY%"=="" set COMPANY=a
call "%~dp0scripts\healthcheck.bat" "%BASE%" "%CODE%" "%COMPANY%"