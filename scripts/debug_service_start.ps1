# Debug Service Start Issues

$ServiceName = "QRJsonAutoSync"
$ScriptPath = Join-Path $PSScriptRoot "ultimate_sync_guardian.ps1"

Write-Host "=== Service Start Debug ===" -ForegroundColor Cyan
Write-Host ""

# Check if script exists
Write-Host "1. Checking guardian script:" -ForegroundColor Yellow
if (Test-Path $ScriptPath) {
    Write-Host "   [OK] Script exists: $ScriptPath" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Script not found: $ScriptPath" -ForegroundColor Red
    Write-Host "   This is why the service cannot start!" -ForegroundColor Red
    exit 1
}

# Check PowerShell execution policy
Write-Host ""
Write-Host "2. Checking PowerShell execution policy:" -ForegroundColor Yellow
$policy = Get-ExecutionPolicy
Write-Host "   Current policy: $policy" -ForegroundColor $(if($policy -eq 'Restricted') {'Red'} else {'Green'})

if ($policy -eq 'Restricted') {
    Write-Host "   [WARNING] Execution policy is restricted!" -ForegroundColor Red
    Write-Host "   Run as admin: Set-ExecutionPolicy RemoteSigned" -ForegroundColor Yellow
}

# Check service status
Write-Host ""
Write-Host "3. Checking service status:" -ForegroundColor Yellow
try {
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Host "   Status: $($service.Status)" -ForegroundColor $(if($service.Status -eq 'Running') {'Green'} else {'Yellow'})
        Write-Host "   Start Type: $($service.StartType)" -ForegroundColor Cyan
        
        # Try to start if stopped
        if ($service.Status -ne 'Running') {
            Write-Host ""
            Write-Host "4. Attempting to start service:" -ForegroundColor Yellow
            try {
                Start-Service -Name $ServiceName
                Start-Sleep -Seconds 3
                $service.Refresh()
                Write-Host "   New Status: $($service.Status)" -ForegroundColor $(if($service.Status -eq 'Running') {'Green'} else {'Red'})
            } catch {
                Write-Host "   [ERROR] Failed to start: $($_.Exception.Message)" -ForegroundColor Red
                
                # Check Windows Event Log for more details
                Write-Host ""
                Write-Host "5. Checking Windows Event Log:" -ForegroundColor Yellow
                try {
                    $events = Get-WinEvent -FilterHashtable @{LogName='System'; ID=7034,7031,7024; StartTime=(Get-Date).AddHours(-1)} -MaxEvents 5 -ErrorAction SilentlyContinue
                    foreach ($event in $events) {
                        if ($event.Message -like "*$ServiceName*") {
                            Write-Host "   Event: $($event.TimeCreated) - $($event.LevelDisplayName)" -ForegroundColor Red
                            Write-Host "   Message: $($event.Message)" -ForegroundColor Gray
                        }
                    }
                } catch {
                    Write-Host "   Cannot access event log" -ForegroundColor Yellow
                }
            }
        }
    } else {
        Write-Host "   [ERROR] Service not found!" -ForegroundColor Red
    }
} catch {
    Write-Host "   [ERROR] Cannot check service: $($_.Exception.Message)" -ForegroundColor Red
}

# Test manual script execution
Write-Host ""
Write-Host "6. Testing manual script execution:" -ForegroundColor Yellow
try {
    $testOutput = & powershell -ExecutionPolicy Bypass -WindowStyle Hidden -Command "& '$ScriptPath'; Start-Sleep 2; exit 0" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   [OK] Script can execute manually" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Script execution failed" -ForegroundColor Red
        Write-Host "   Output: $testOutput" -ForegroundColor Gray
    }
} catch {
    Write-Host "   [ERROR] Cannot test script: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Recommendations ===" -ForegroundColor Cyan

if (-not (Test-Path $ScriptPath)) {
    Write-Host "1. Create the missing guardian script" -ForegroundColor Yellow
} else {
    Write-Host "1. Try running the guardian script manually first" -ForegroundColor Yellow
}

Write-Host "2. Check PowerShell execution policy: Set-ExecutionPolicy RemoteSigned" -ForegroundColor Yellow
Write-Host "3. Ensure FTP credentials are correct" -ForegroundColor Yellow
Write-Host "4. Check network connectivity to scan.example.com" -ForegroundColor Yellow