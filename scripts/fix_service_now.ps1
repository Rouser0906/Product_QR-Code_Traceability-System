# Quick Fix for Service Issues

Write-Host "=== Fixing Service Issues ===" -ForegroundColor Cyan

# Stop and remove existing problematic service
Write-Host "1. Removing existing service..." -ForegroundColor Yellow
try {
    Stop-Service -Name "QRJsonAutoSync" -Force -ErrorAction SilentlyContinue
    & sc.exe delete "QRJsonAutoSync"
    Write-Host "   Old service removed" -ForegroundColor Green
} catch {
    Write-Host "   Service removal skipped" -ForegroundColor Yellow
}

# Create a simple batch wrapper for the PowerShell script
$wrapperPath = Join-Path $PSScriptRoot "sync_service_wrapper.bat"
$psScript = Join-Path $PSScriptRoot "ultimate_sync_guardian.ps1"

$wrapperContent = @"
@echo off
cd /d "$((Split-Path $PSScriptRoot -Parent))"
powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File "$psScript"
"@

Write-Host "2. Creating service wrapper..." -ForegroundColor Yellow
$wrapperContent | Out-File -FilePath $wrapperPath -Encoding ASCII
Write-Host "   Wrapper created: $wrapperPath" -ForegroundColor Green

# Install service with the wrapper
Write-Host "3. Installing service with wrapper..." -ForegroundColor Yellow
$servicePath = "`"$wrapperPath`""
& sc.exe create "QRJsonAutoSync" binPath= $servicePath DisplayName= "QR JSON Auto Sync Service" start= auto

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Service installed successfully" -ForegroundColor Green
    
    # Set service description and recovery
    & sc.exe description "QRJsonAutoSync" "Automatically sync JSON files to FTP server"
    & sc.exe failure "QRJsonAutoSync" reset= 86400 actions= restart/5000/restart/10000/restart/30000
    
    # Try to start the service
    Write-Host "4. Starting service..." -ForegroundColor Yellow
    & sc.exe start "QRJsonAutoSync"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Service started successfully!" -ForegroundColor Green
        
        Start-Sleep -Seconds 3
        $service = Get-Service -Name "QRJsonAutoSync"
        Write-Host "   Final status: $($service.Status)" -ForegroundColor $(if($service.Status -eq 'Running') {'Green'} else {'Red'})
    } else {
        Write-Host "   Service start failed, but installation successful" -ForegroundColor Yellow
        Write-Host "   Try manual start: services.msc" -ForegroundColor Gray
    }
} else {
    Write-Host "   Service installation failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Alternative: Manual Start ===" -ForegroundColor Cyan
Write-Host "If service doesn't work, you can run manually:" -ForegroundColor White
Write-Host "   .\scripts\start_ultimate_sync.bat" -ForegroundColor Gray