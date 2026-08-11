# 稳定的FTP上传守护进程 - 专门解决HS-DEMO-000010232.json上传问题
param(
  [string]$FtpHost = 'scan.example.com',
  [int]$FtpPort = 21,
  [string]$Username = 'your_ftp_username', 
  [string]$Password = '[REDACTED-FTP-PASSWORD]'
)

$ErrorActionPreference = 'Continue'

# 获取项目根目录
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$hsDir = Join-Path $ProjectRoot "cloud\demo_json_a"
$zyDir = Join-Path $ProjectRoot "cloud\demo_json_b"
$logFile = Join-Path $ProjectRoot "auto_sync\logs\ftp_uploader.log"

# 创建目录
New-Item -ItemType Directory -Force -Path $hsDir | Out-Null
New-Item -ItemType Directory -Force -Path $zyDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $logFile) | Out-Null

function Write-Log($msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts STABLE_FTP: $msg" | Out-File -FilePath $logFile -Encoding UTF8 -Append
  Write-Host "$ts $msg" -ForegroundColor Green
}

function Upload-ToFTP([string]$localFile, [string]$remoteDir) {
  try {
    if (-not (Test-Path $localFile)) { 
      Write-Log "Local file not found: $localFile"
      return $false 
    }
    
    $fileName = [System.IO.Path]::GetFileName($localFile)
    $remoteUrl = "ftp://$FtpHost`:$FtpPort$remoteDir/$fileName"
    
    Write-Log "Uploading: $localFile -> $remoteUrl"
    
    # 检查文件是否已存在
    try {
      $checkReq = [System.Net.FtpWebRequest]::Create($remoteUrl)
      $checkReq.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
      $checkReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
      $checkReq.UsePassive = $true
      $checkReq.Timeout = 10000
      $checkResp = $checkReq.GetResponse()
      $checkResp.Close()
      Write-Log "SKIP exists: $remoteUrl"
      return $true
    } catch {
      # 文件不存在，继续上传
    }
    
    # 执行FTP上传
    $uploadReq = [System.Net.FtpWebRequest]::Create($remoteUrl)
    $uploadReq.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $uploadReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
    $uploadReq.UsePassive = $true
    $uploadReq.UseBinary = $true
    $uploadReq.Timeout = 30000
    $uploadReq.Proxy = $null
    
    $fileContent = [System.IO.File]::ReadAllBytes($localFile)
    $uploadReq.ContentLength = $fileContent.Length
    
    $requestStream = $uploadReq.GetRequestStream()
    $requestStream.Write($fileContent, 0, $fileContent.Length)
    $requestStream.Close()
    
    $response = $uploadReq.GetResponse()
    Write-Log "UPLOAD SUCCESS: $fileName -> $remoteDir (Size: $($fileContent.Length) bytes)"
    $response.Close()
    return $true
    
  } catch {
    Write-Log "UPLOAD FAILED: $fileName -> $remoteDir | Error: $($_.Exception.Message)"
    return $false
  }
}

Write-Log "=== STABLE FTP UPLOADER STARTED ==="
Write-Log "FTP Server: $FtpHost`:$FtpPort"
Write-Log "Local HS Dir: $hsDir"
Write-Log "Local ZY Dir: $zyDir"

# 立即上传HS-DEMO-000010232.json（如果存在）
$targetFile = Join-Path $hsDir "HS-DEMO-000010232.json"
if (Test-Path $targetFile) {
  Write-Log "Found target file: HS-DEMO-000010232.json"
  $result = Upload-ToFTP -localFile $targetFile -remoteDir "/companies/demo_json_a"
  if ($result) {
    Write-Log "✓ HS-DEMO-000010232.json uploaded successfully to cloud server!"
  } else {
    Write-Log "✗ Failed to upload HS-DEMO-000010232.json"
  }
}

# 批量上传所有现有的JSON文件
Write-Log "Starting batch upload of existing files..."

Get-ChildItem -Path $hsDir -Filter "*.json" | ForEach-Object {
  Upload-ToFTP -localFile $_.FullName -remoteDir "/companies/demo_json_a"
  Start-Sleep -Milliseconds 500
}

Get-ChildItem -Path $zyDir -Filter "*.json" | ForEach-Object {
  Upload-ToFTP -localFile $_.FullName -remoteDir "/companies/demo_json_b"
  Start-Sleep -Milliseconds 500
}

Write-Log "Batch upload completed. Starting real-time monitoring..."

# 实时监控新文件
$watcher1 = New-Object System.IO.FileSystemWatcher
$watcher1.Path = $hsDir
$watcher1.Filter = "*.json"
$watcher1.IncludeSubdirectories = $false
$watcher1.EnableRaisingEvents = $true

$watcher2 = New-Object System.IO.FileSystemWatcher  
$watcher2.Path = $zyDir
$watcher2.Filter = "*.json"
$watcher2.IncludeSubdirectories = $false
$watcher2.EnableRaisingEvents = $true

$action = {
  param($sender, $e)
  Start-Sleep -Seconds 1  # 等待文件写入完成
  
  $remoteDir = if ($sender.Path -like "*demo_json_a*") { "/companies/demo_json_a" } else { "/companies/demo_json_b" }
  Upload-ToFTP -localFile $e.FullPath -remoteDir $remoteDir
}

Register-ObjectEvent -InputObject $watcher1 -EventName "Created" -Action $action | Out-Null
Register-ObjectEvent -InputObject $watcher1 -EventName "Changed" -Action $action | Out-Null
Register-ObjectEvent -InputObject $watcher2 -EventName "Created" -Action $action | Out-Null
Register-ObjectEvent -InputObject $watcher2 -EventName "Changed" -Action $action | Out-Null

Write-Log "Real-time monitoring active. Press Ctrl+C to stop..."

# 保持运行
try {
  while ($true) {
    Start-Sleep -Seconds 5
    # 每5分钟输出一次心跳
    if ((Get-Date).Minute % 5 -eq 0) {
      Write-Log "Heartbeat: Monitoring active"
    }
  }
} finally {
  if ($watcher1) { $watcher1.Dispose() }
  if ($watcher2) { $watcher2.Dispose() }
  Write-Log "=== STABLE FTP UPLOADER STOPPED ==="
}