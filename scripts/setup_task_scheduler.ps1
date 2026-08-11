# Setup JSON Auto Sync using Task Scheduler (More Reliable than Windows Service)

param(
    [switch]$Install,
    [switch]$Remove,
    [switch]$Start,
    [switch]$Stop
)

$TaskName = "QRJsonAutoSync"
$ScriptPath = Join-Path $PSScriptRoot "ultimate_sync_guardian.ps1"
$LogPath = Join-Path (Split-Path $PSScriptRoot -Parent) "auto_sync\logs"

function Install-SyncTask {
    Write-Host "Installing JSON Auto Sync as Scheduled Task..." -ForegroundColor Yellow
    
    try {
        # Remove existing task if exists
        try {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        } catch {}
        
        # Create action
        $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$ScriptPath`""
        
        # Create trigger (at startup)
        $trigger = New-ScheduledTaskTrigger -AtStartup
        
        # Create settings
        $settings = New-ScheduledTaskSettingsSet -DontStopOnIdleEnd -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
        
        # Create principal (run as SYSTEM)
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        
        # Register task
        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Auto sync JSON files to FTP server"
        
        Write-Host "Task installed successfully!" -ForegroundColor Green
        
        # Start the task
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "Task started!" -ForegroundColor Green
        
        return $true
    } catch {
        Write-Host "Failed to install task: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Remove-SyncTask {
    Write-Host "Removing JSON Auto Sync Task..." -ForegroundColor Yellow
    
    try {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Task removed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to remove task: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-SyncTask {
    Write-Host "Starting JSON Auto Sync Task..." -ForegroundColor Yellow
    
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "Task started!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to start task: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-SyncTask {
    Write-Host "Stopping JSON Auto Sync Task..." -ForegroundColor Yellow
    
    try {
        Stop-ScheduledTask -TaskName $TaskName
        Write-Host "Task stopped!" -ForegroundColor Green
    } catch {
        Write-Host "Failed to stop task: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Get-TaskStatus {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "Task Status: $($task.State)" -ForegroundColor $(if($task.State -eq 'Running') {'Green'} else {'Yellow'})
            
            # Get last run info
            $info = Get-ScheduledTaskInfo -TaskName $TaskName -ErrorAction SilentlyContinue
            if ($info) {
                Write-Host "Last Run: $($info.LastRunTime)" -ForegroundColor Cyan
                Write-Host "Last Result: $($info.LastTaskResult)" -ForegroundColor $(if($info.LastTaskResult -eq 0) {'Green'} else {'Red'})
                Write-Host "Next Run: $($info.NextRunTime)" -ForegroundColor Cyan
            }
            return $task
        } else {
            Write-Host "Task not found" -ForegroundColor Gray
            return $null
        }
    } catch {
        Write-Host "Cannot get task status: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# Main logic
Write-Host "======== JSON Auto Sync Task Manager ========" -ForegroundColor Cyan
Write-Host ""

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: Guardian script not found: $ScriptPath" -ForegroundColor Red
    exit 1
}

# Ensure log directory exists
if (-not (Test-Path $LogPath)) {
    New-Item -ItemType Directory -Force -Path $LogPath | Out-Null
}

Write-Host "Current Status:" -ForegroundColor White
$currentTask = Get-TaskStatus
Write-Host ""

if ($Install) {
    Install-SyncTask
} elseif ($Remove) {
    Remove-SyncTask
} elseif ($Start) {
    Start-SyncTask
} elseif ($Stop) {
    Stop-SyncTask
} else {
    # Interactive menu
    Write-Host "Select an option:" -ForegroundColor White
    Write-Host "1. Install Task" -ForegroundColor Green
    Write-Host "2. Remove Task" -ForegroundColor Red
    Write-Host "3. Start Task" -ForegroundColor Cyan
    Write-Host "4. Stop Task" -ForegroundColor Yellow
    Write-Host "5. Check Status" -ForegroundColor Gray
    Write-Host "0. Exit" -ForegroundColor White
    Write-Host ""
    
    do {
        Write-Host "Enter option (0-5): " -ForegroundColor White -NoNewline
        $choice = Read-Host
        
        switch ($choice) {
            "1" { Install-SyncTask; break }
            "2" { Remove-SyncTask; break }
            "3" { Start-SyncTask; break }
            "4" { Stop-SyncTask; break }
            "5" { Get-TaskStatus | Out-Null; break }
            "0" { Write-Host "Exiting..." -ForegroundColor Gray; break }
            default { Write-Host "Invalid option" -ForegroundColor Red; continue }
        }
        
        if ($choice -ne "0" -and $choice -ne "5") {
            Write-Host ""
            Write-Host "Current Status:" -ForegroundColor White
            Get-TaskStatus | Out-Null
        }
        
    } while ($choice -ne "0")
}

Write-Host ""
Write-Host "Task Scheduler is more reliable than Windows Service for PowerShell scripts!" -ForegroundColor Green