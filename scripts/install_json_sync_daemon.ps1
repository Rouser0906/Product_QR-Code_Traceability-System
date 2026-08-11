# Install JSON Auto Sync Daemon - Ensure local *.JSON files auto sync to server
# Core requirement: New JSON files in *\cloud\demo_json_a and *\cloud\demo_json_b must auto upload to server directories

param(
  [string]$TaskName = 'JSON_Auto_Sync_Daemon'
)

$ErrorActionPreference = 'Stop'

try {
  Write-Host "Installing JSON Auto Sync Daemon..." -ForegroundColor Green
  
  $projectRoot = (Get-Location).Path
  $scriptPath = Join-Path $projectRoot "scripts\windows_ftp_json_watcher.ps1"
  
  if (-not (Test-Path $scriptPath)) {
    throw "Script not found: $scriptPath"
  }
  
  # Remove old tasks
  Write-Host "Cleaning old tasks..." -ForegroundColor Yellow
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
  
  # Register SYSTEM account startup task (most robust solution)
  Write-Host "Registering SYSTEM level daemon task..." -ForegroundColor Yellow
  $cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
  
  # Create task
  schtasks /Create /TN $TaskName /TR $cmd /SC ONSTART /RL HIGHEST /RU SYSTEM /F | Out-Null
  
  # Start immediately
  Write-Host "Starting daemon process..." -ForegroundColor Yellow
  schtasks /Run /TN $TaskName | Out-Null
  
  Start-Sleep -Seconds 3
  
  # Verify status
  $taskInfo = schtasks /Query /TN $TaskName /V /FO CSV | ConvertFrom-Csv
  $state = $taskInfo.'Status'
  
  Write-Host "Installation completed!" -ForegroundColor Green
  Write-Host "Task Name: $TaskName" -ForegroundColor White
  Write-Host "Run Status: $state" -ForegroundColor White
  Write-Host "Monitor Script: $scriptPath" -ForegroundColor White
  Write-Host "Working Directory: $projectRoot" -ForegroundColor White
  
  # Show monitor paths
  $hsPath = Join-Path $projectRoot "cloud\demo_json_a"
  $zyPath = Join-Path $projectRoot "cloud\demo_json_b"
  Write-Host "Monitor Paths:" -ForegroundColor Cyan
  Write-Host "  HS JSON: $hsPath -> C:\inetpub\qr-system\companies\demo_json_a" -ForegroundColor White
  Write-Host "  ZY JSON: $zyPath -> C:\inetpub\qr-system\companies\demo_json_b" -ForegroundColor White
  
  # Create monitor directories
  New-Item -ItemType Directory -Force -Path $hsPath | Out-Null
  New-Item -ItemType Directory -Force -Path $zyPath | Out-Null
  New-Item -ItemType Directory -Force -Path "C:\inetpub\qr-system\companies\demo_json_a" -ErrorAction SilentlyContinue | Out-Null
  New-Item -ItemType Directory -Force -Path "C:\inetpub\qr-system\companies\demo_json_b" -ErrorAction SilentlyContinue | Out-Null
  
  Write-Host "Directory structure created successfully" -ForegroundColor Green
  
} catch {
  Write-Host "Installation failed: $($_.Exception.Message)" -ForegroundColor Red
  exit 1
}