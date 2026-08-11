@echo off
setlocal
REM 启动 JSON 自动同步守护（最小化/隐藏窗口）
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%.."

REM 如需隐藏窗口，请使用 -WindowStyle Hidden；如需可见最小化，把 Hidden 改为 Minimized
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "scripts/windows_ftp_json_watcher.ps1"

popd
endlocal
