@echo off
:: 健康检查：验证 web.config、API、JSON 与 CORS/MIME
:: 用法示例：
::   0_run_healthcheck.bat https://your-company-domain.com HS-DEMO-000008726 hs
::   0_run_healthcheck.bat https://your-company-domain.com ZY-DEMO-000000015 zy
set BASE=%~1
set CODE=%~2
set COMPANY=%~3
if "%BASE%"=="" set BASE=https://your-company-domain.com
if "%COMPANY%"=="" set COMPANY=hs
call "%~dp0scripts\healthcheck.bat" "%BASE%" "%CODE%" "%COMPANY%"