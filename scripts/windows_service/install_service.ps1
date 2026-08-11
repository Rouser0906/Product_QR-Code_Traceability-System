param(
  [string]$ServiceName = 'QRJsonAutoSync',
  [string]$PythonExe = 'python',
  [string]$ServiceScript = 'scripts/windows_service/auto_sync_win_service.py'
)

$ErrorActionPreference = 'SilentlyContinue'

Write-Output 'Installing pywin32 (if missing)...'
try { & $PythonExe -m pip install pywin32 | Out-Null } catch { Write-Output 'pip install pywin32 failed, please ensure internet access.' }

Write-Output "Installing Windows service: $ServiceName"
& $PythonExe $ServiceScript install

Write-Output "Starting service: $ServiceName"
& $PythonExe $ServiceScript start

Write-Output 'Done.'