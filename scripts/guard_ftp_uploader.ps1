param(
  [int]$StaleSeconds = 120
)

$ErrorActionPreference = 'SilentlyContinue'

# 固定到项目根
try {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
  $ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
  Set-Location $ProjectRoot
} catch {
  $ProjectRoot = (Get-Location).Path
}

$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'ftp_uploader.log'
$alertFile = Join-Path $logDir 'alerts.log'

function Write-Log($msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts GUARD: $msg" | Out-File -FilePath $logFile -Encoding utf8 -Append
}
function Write-Alert($msg) {
  try {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$ts ALERT: $msg" | Out-File -FilePath $alertFile -Encoding utf8 -Append
    try { [Console]::Beep(800, 200) } catch {}
  } catch {}
}

# 检测上传进程是否存在（按命令行匹配）
$uploaderCmdLike = '*windows_ftp_json_uploader.ps1*'
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like $uploaderCmdLike }

# 检测日志活性
$now = Get-Date
$stale = $false
if (Test-Path $logFile) {
  $lastWrite = (Get-Item $logFile).LastWriteTime
  $age = ($now - $lastWrite).TotalSeconds
  if ($age -gt $StaleSeconds) { $stale = $true }
} else {
  $stale = $true
}

# 需要重启的条件：没有进程 或 日志陈旧
if (($procs | Measure-Object).Count -eq 0 -or $stale) {
  if (($procs | Measure-Object).Count -gt 0) {
    # 尝试结束旧进程
    foreach ($p in $procs) {
      try { Stop-Process -Id $p.ProcessId -Force } catch {}
    }
    Write-Log "Detected stale; killed old uploader processes."
  } else {
    Write-Log "Uploader process not found."
  }

  # 启动新的隐藏上传进程
  $target = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
  if (-not (Test-Path $target)) { $target = (Get-Command powershell.exe).Source }
  $args = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$($ProjectRoot)\scripts\windows_ftp_json_uploader.ps1`""
  try {
    Start-Process -FilePath $target -ArgumentList $args -WindowStyle Hidden
    Write-Log "Started uploader via $target $args"
  } catch {
    Write-Alert "Failed to start uploader: $($_.Exception.Message)"
  }
} else {
  Write-Log "Healthy: uploader running and log fresh."
}