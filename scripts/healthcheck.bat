@echo off
setlocal EnableExtensions
set "BASE=%~1"
set "CODE=%~2"
set "COMPANY=%~3"
if "%BASE%"=="" set "BASE=https://your-company-domain.com"
if "%COMPANY%"=="" set "COMPANY=hs"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0healthcheck.ps1" -BaseUrl "%BASE%" -Code "%CODE%" -Company "%COMPANY%" -Insecure
endlocal
