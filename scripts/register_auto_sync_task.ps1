param(
  [string]$TaskName = 'QR_AutoSync_Service',
  [string]$PythonExe = 'python',
  [string]# [DEPRECATED] 内置 Python 自启动守护已停用，改为 Windows 计划任务
  $ScriptPath = 'scripts/auto_sync_daemon.py'
)

$ErrorActionPreference = 'SilentlyContinue'
$taskAction = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath -WorkingDirectory (Get-Location).Path
$trigger1 = New-ScheduledTaskTrigger -AtLogOn
$trigger2 = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 72)

# Register or update task
try {
  if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
  }
  Register-ScheduledTask -TaskName $TaskName -Action $taskAction -Trigger $trigger1,$trigger2 -Settings $settings -Description 'Auto start QR JSON FTP sync daemon' | Out-Null
  Write-Output "Task '$TaskName' registered."
} catch {
  Write-Output "Failed to register task: $($_.Exception.Message)"
}

# Start task immediately
try {
  Start-ScheduledTask -TaskName $TaskName | Out-Null
  Write-Output "Task '$TaskName' started."
} catch {
  Write-Output "Failed to start task: $($_.Exception.Message)"
}
