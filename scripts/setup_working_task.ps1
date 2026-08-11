# Setup Working File Watcher as Scheduled Task

$TaskName = "JSONFileWatcher"
$ScriptPath = Join-Path $PSScriptRoot "working_file_watcher.ps1"

Write-Host "Setting up reliable JSON file watcher..." -ForegroundColor Cyan

try {
    # Remove existing task if exists
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    
    # Create action
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
    
    # Create trigger (at startup)
    $trigger = New-ScheduledTaskTrigger -AtStartup
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet -DontStopOnIdleEnd -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -RunOnlyIfNetworkAvailable
    
    # Create principal (run as current user with highest privileges)
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    # Register task
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Monitor and auto-upload JSON files to FTP server"
    
    Write-Host "✓ Task installed successfully!" -ForegroundColor Green
    
    # Start the task
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "✓ Task started!" -ForegroundColor Green
    
    # Show status
    Start-Sleep -Seconds 2
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host ""
    Write-Host "Task Status: $($task.State)" -ForegroundColor $(if($task.State -eq 'Running') {'Green'} else {'Yellow'})
    Write-Host "Last Run: $($info.LastRunTime)" -ForegroundColor Cyan
    
} catch {
    Write-Host "✗ Failed to setup task: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "JSON File Watcher is now active!" -ForegroundColor Green
Write-Host "It will automatically upload any new JSON files to the server." -ForegroundColor White