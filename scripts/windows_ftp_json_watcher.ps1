param(
  [string]$FtpHost = 'scan.example.com',
  [int]$FtpPort = 21,
  [string]$Username = 'your_ftp_username',
  [string]$Password = '[REDACTED-FTP-PASSWORD]',
  [string]$LocalA = '',  # 自动检测项目根\cloud\demo_json_a
  [string]$LocalB = '',  # 自动检测项目根\cloud\demo_json_b
  [string]$RemoteHS = '/companies/demo_json_a',
  [string]$RemoteZY = '/companies/demo_json_b',
  [int]$StabilizeMs = 600,
  [int]$DebounceMs = 1200,
  [int]$RescanMinutes = 5
)

$ErrorActionPreference = 'SilentlyContinue'

# 固定到项目根并准备日志目录
try {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
  $ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
  Set-Location $ProjectRoot
} catch {
  $ProjectRoot = (Get-Location).Path
}

# 自动检测本地监控目录
if (-not $LocalA) { $LocalA = Join-Path $ProjectRoot 'cloud\demo_json_a' }
if (-not $LocalB) { $LocalB = Join-Path $ProjectRoot 'cloud\demo_json_b' }

$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'ftp_uploader.log'

# 创建本地监控目录
New-Item -ItemType Directory -Force -Path $LocalA | Out-Null
New-Item -ItemType Directory -Force -Path $LocalB | Out-Null

function Write-Log($msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts WATCHER: $msg" | Out-File -FilePath $logFile -Encoding utf8 -Append
}

function Upload-JsonFile([string]$fullPath) {
  try {
    if (-not (Test-Path $fullPath)) { return }

    # 稳定检测：等待文件大小稳定
    $size1 = (Get-Item $fullPath).Length
    Start-Sleep -Milliseconds $StabilizeMs
    $size2 = (Get-Item $fullPath).Length
    if ($size1 -ne $size2) {
      Start-Sleep -Milliseconds $StabilizeMs
    }

    $name = [System.IO.Path]::GetFileName($fullPath)
    $dir  = [System.IO.Path]::GetDirectoryName($fullPath)
    # 按父目录判断上传目标，确保 cloud/demo_json_a 与 cloud/demo_json_b 下的任何 *.json 都被秒传
    $isHS = $dir -match '\\demo_json_a$'
    $isZY = $dir -match '\\demo_json_b$'
    if (-not ($isHS -or $isZY)) { Write-Log "IGNORE not under demo_json_a/demo_json_b: $fullPath"; return }

    $remoteDir = if ($isHS) { $RemoteHS } else { $RemoteZY }
    $remoteUrl = "ftp://$FtpHost`:$FtpPort$remoteDir/$name"

    # 先检查是否存在：用 SIZE/LIST 兼容方式（忽略失败）
    try {
      $chk = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost`:$FtpPort$remoteDir/$name")
      $chk.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
      $chk.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
      $chk.UsePassive = $true
      $chk.UseBinary = $true
      $chk.Proxy = $null
      $resp = $chk.GetResponse()
      if ($resp) { $resp.Close() }
      Write-Log "SKIP exists: ${remoteDir}/$name"
      return
    } catch { }

    # 上传到真正的FTP服务器
    $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
    $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
    $req.UsePassive = $true
    $req.UseBinary = $true
    $req.Proxy = $null
    $bytes = [System.IO.File]::ReadAllBytes($fullPath)
    $req.ContentLength = $bytes.Length
    $stream = $req.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Close()
    $response = $req.GetResponse()
    $response.Close()
    Write-Log "UPLOAD OK: $fullPath -> ${remoteDir}/$name"
  } catch {
    Write-Log "UPLOAD FAIL: $fullPath -> ${remoteDir}/$name ; $($_.Exception.Message)"
  }
}

function New-Watcher([string]$path) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
  $fw = New-Object System.IO.FileSystemWatcher
  $fw.Path = $path
  # 使用通配，回调中按扩展名判断，避免大小写或匹配问题
  $fw.Filter = '*.*'
  $fw.IncludeSubdirectories = $false
  # 强化变更通知，确保文件创建/写入触发
  $fw.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::Size
  $fw.EnableRaisingEvents = $true

  $debounce = @{}
  $action = {
    param($src, $eventArgs)
    $fp = $eventArgs.FullPath
    $now = Get-Date
    # 简单防抖
    if ($debounce.ContainsKey($fp)) {
      if (([DateTime]$debounce[$fp].AddMilliseconds($DebounceMs)) -gt $now) { return }
    }
    $debounce[$fp] = $now
    Write-Log "Detected: $fp"
    $ext = [System.IO.Path]::GetExtension($fp).ToLower()
    if ($ext -ne '.json') { return }
    Upload-JsonFile -fullPath $fp
  }

  Register-ObjectEvent -InputObject $fw -EventName Created -Action $action | Out-Null
  Register-ObjectEvent -InputObject $fw -EventName Changed -Action $action | Out-Null
  return $fw
}

Write-Log "File watcher starting. A=$LocalA B=$LocalB RemoteHS=$RemoteHS RemoteZY=$RemoteZY FTP=$FtpHost`:$FtpPort"
$w1 = New-Watcher -path $LocalA
$w2 = New-Watcher -path $LocalB

# 保持进程常驻
while ($true) {
  Start-Sleep -Seconds 2
}