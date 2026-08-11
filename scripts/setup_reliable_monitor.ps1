# Setup Reliable JSON Monitor

$TaskName = "ReliableJSONMonitor"
$ScriptPath = Join-Path $PSScriptRoot "reliable_json_monitor.ps1"

Write-Host "Setting up reliable JSON monitor..." -ForegroundColor Cyan

try {
    # Remove any existing tasks
    Get-ScheduledTask | Where-Object {$_.TaskName -like "*JSON*"} | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue
    
    # Create action - using a wrapper command to ensure proper execution
    $command = "powershell.exe"
    $arguments = "-ExecutionPolicy Bypass -WindowStyle Hidden -Command `"& '$ScriptPath'`""
    $action = New-ScheduledTaskAction -Execute $command -Argument $arguments
    
    # Create trigger (at startup and also at logon)
    $triggerStartup = New-ScheduledTaskTrigger -AtStartup
    $triggerLogon = New-ScheduledTaskTrigger -AtLogOn
    
    # Create settings with better error handling
    $settings = New-ScheduledTaskSettingsSet -DontStopOnIdleEnd -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 2) -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0)
    
    # Use current user for better permissions
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    # Register task
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger @($triggerStartup, $triggerLogon) -Settings $settings -Principal $principal -Description "Reliable JSON file monitor and uploader"
    
    Write-Host "Task registered successfully!" -ForegroundColor Green
    
    # Start the task immediately
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "Task started!" -ForegroundColor Green
    
    # Wait and check status
    Start-Sleep -Seconds 3
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host ""
    Write-Host "Task Status: $($task.State)" -ForegroundColor $(if($task.State -eq 'Running') {'Green'} else {'Yellow'})
    Write-Host "Last Result: $($info.LastTaskResult)" -ForegroundColor $(if($info.LastTaskResult -eq 0) {'Green'} else {'Red'})
    
    if ($info.LastTaskResult -eq 0) {
        Write-Host "SUCCESS: Monitor is running properly!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: Task may have issues (Result: $($info.LastTaskResult))" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "ERROR: Failed to setup task - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Reliable JSON monitor is now active!" -ForegroundColor Green
Write-Host "Check logs at: auto_sync\logs\json_monitor.log" -ForegroundColor Cyan