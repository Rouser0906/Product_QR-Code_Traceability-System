param(
  [string]$TaskName = 'QRJsonyour_ftp_username',
  [string]$ProjectRoot = (Get-Location).Path,
  [switch]$Fix
)

$ErrorActionPreference = 'SilentlyContinue'

Write-Host "== QR JSON Auto-Sync Verify ==" -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot" -ForegroundColor Cyan

# Ensure log dir exists
$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'ftp_uploader.log'

# 1) Check scheduled task
$task = schtasks /Query /TN "$TaskName" 2>$null
if (-not $task) {
  Write-Host "[WARN] Scheduled task not found: $TaskName" -ForegroundColor Yellow
  if (-not $Fix) {
    Write-Host "Use -Fix to create/repair the task automatically." -ForegroundColor Yellow
  } else {
    Write-Host "[FIX] Creating task: $TaskName" -ForegroundColor Yellow
    powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot 'scripts\scheduled_tasks\setup_json_ftp_uploader.ps1')
  }
} else {
  Write-Host "[OK] Scheduled task exists: $TaskName" -ForegroundColor Green
}

# 2) Try to run the task now
schtasks /run /tn "$TaskName" | Out-Null
Start-Sleep -Seconds 2

# 3) Show status
Write-Host "\n-- Task status --" -ForegroundColor Cyan
schtasks /Query /TN "$TaskName" /V /FO LIST 2>$null | findstr /i "TaskName\|Status\|Last\|Next\|RunAs User\|Author"

# 4) Show last 50 lines of logs
Write-Host "\n-- Last 50 lines of ftp_uploader.log --" -ForegroundColor Cyan
if (Test-Path $logFile) {
  Get-Content $logFile -Tail 50
} else {
  Write-Host "No log file yet: $logFile" -ForegroundColor Yellow
}

# 5) Optional one-shot upload pass to accelerate first run
Write-Host "\n-- Optional: one-shot upload pass (skips existing) --" -ForegroundColor Cyan
$uploader = Join-Path $ProjectRoot 'scripts\windows_ftp_json_uploader.ps1'
if (Test-Path $uploader) {
  Write-Host "Running one-shot sync..." -ForegroundColor Yellow
  powershell -ExecutionPolicy Bypass -File $uploader -Once | Out-Null
  Start-Sleep -Seconds 1
  if (Test-Path $logFile) { Get-Content $logFile -Tail 50 }
} else {
  Write-Host "Uploader not found: $uploader" -ForegroundColor Red
}

Write-Host "\n== Done ==" -ForegroundColor Green
