# Install Scheduled Task: 本地JSON文件自动同步到服务器守护进程
param(
  [string]$TaskName = 'JSON_FTP_Watcher',
  [string]$ScriptRelPath = 'scripts/windows_ftp_json_watcher.ps1'
)

$ErrorActionPreference = 'Stop'

try {
  $projectRoot = (Get-Location).Path
  $scriptPath = Join-Path $projectRoot $ScriptRelPath
  if (-not (Test-Path $scriptPath)) {
    throw "Script not found: $scriptPath"
  }
  
  # Remove existing task
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
  
  # Task action: run PowerShell hidden
  $psArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $psArgs -WorkingDirectory $projectRoot

  # Triggers: at startup + at logon
  $t1 = New-ScheduledTaskTrigger -AtStartup
  $t2 = New-ScheduledTaskTrigger -AtLogOn

  # Settings: start when available, restart on failure, long time limit
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 7)

  # Run as current user with highest privileges
  $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

  # Register and start
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $t1,$t2 -Settings $settings -Principal $principal -Description '本地JSON文件自动同步到C:\inetpub\qr-system\companies目录' | Out-Null
  Start-ScheduledTask -TaskName $TaskName

  Start-Sleep -Seconds 2
  $task = Get-ScheduledTask -TaskName $TaskName
  $info = Get-ScheduledTaskInfo -TaskName $TaskName

  Write-Output "Task '$TaskName' installed and started."
  Write-Output ("State: {0} | LastRun: {1} | NextRun: {2}" -f $task.State, $info.LastRunTime, $info.NextRunTime)
  Write-Output "Action: powershell.exe $psArgs"
  Write-Output "WorkingDir: $projectRoot"
} catch {
  Write-Output ("Install failed: {0}" -f $_.Exception.Message)
  exit 1
}
