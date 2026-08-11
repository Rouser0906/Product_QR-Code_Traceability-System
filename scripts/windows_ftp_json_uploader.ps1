param(
  [string]$FtpHost = 'scan.example.com',
  [int]$FtpPort = 21,
  [string]$FtpUser = 'your_ftp_username',
  [string]$FtpPass = '[REDACTED-FTP-PASSWORD]',
  [string[]]$LocalACandidates = @('cloud/demo_json_a','companies/demo_json_a'),
  [string[]]$LocalBCandidates = @('cloud/demo_json_b','companies/demo_json_b'),
  [string[]]$RemoteACandidates = @('/companies/demo_json_a'),
  [string[]]$RemoteBCandidates = @('/companies/demo_json_b'),
  [int]$IntervalSeconds = 15,
  [switch]$Once = $false,
  [int]$MaxRetry = 5,
  [int]$RetryDelayMs = 1000
)

$ErrorActionPreference = 'SilentlyContinue'

# Ensure we operate from project root regardless of task's working directory
try {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
  # scripts directory -> project root is parent
  $ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
  Set-Location $ProjectRoot
} catch {
  # Fallback to current location if resolution fails
  $ProjectRoot = (Get-Location).Path
}

$root = $ProjectRoot
$logDir = Join-Path $root 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'ftp_uploader.log'

function Write-Log($msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts $msg" | Out-File -FilePath $logFile -Encoding utf8 -Append
}
function Write-Alert($msg) {
  try {
    $alertFile = Join-Path $logDir 'alerts.log'
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$ts ALERT: $msg" | Out-File -FilePath $alertFile -Encoding utf8 -Append
    try { [Console]::Beep(800, 200) } catch {}
    try { (New-Object -ComObject WScript.Shell).Popup($msg, 2, 'FTP Uploader Alert', 0x0) | Out-Null } catch {}
  } catch {}
}

function Resolve-LocalDir([string[]]$candidates, [string]$root) {
  foreach ($cand in $candidates) {
    $p = if ([System.IO.Path]::IsPathRooted($cand)) { $cand } else { Join-Path $root $cand }
    if (Test-Path $p) { return $p }
  }
  # none exists: create first under root
  $first = if ([System.IO.Path]::IsPathRooted($candidates[0])) { $candidates[0] } else { Join-Path $root $candidates[0] }
  New-Item -ItemType Directory -Force -Path $first | Out-Null
  return $first
}

function Test-FtpConnectivity() {
  try {
    $uri = "ftp://${FtpHost}:${FtpPort}/"
    $req = [System.Net.FtpWebRequest]::Create($uri)
    $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
    $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
    $req.UseBinary = $true
    $req.UsePassive = $true
    $req.Proxy = $null
    $resp = $req.GetResponse(); $resp.Close()
    return $true
  } catch {
    Write-Log "FTP connectivity test failed: $($_.Exception.Message)"
    Write-Alert "FTP connectivity failed: $($_.Exception.Message)"
    return $false
  }
}

function Ensure-RemoteDirExists([string]$remoteDir) {
  try {
    $p = $remoteDir.Replace('\\','/')
    if (-not $p.StartsWith('/')) { $p = '/' + $p }
    $parts = $p.Trim('/') -split '/'
    $current = ''
    foreach ($part in $parts) {
      $current = "$current/$part"
      try {
        $uri = "ftp://${FtpHost}:${FtpPort}$current"
        $mk = [System.Net.FtpWebRequest]::Create($uri)
        $mk.Method = [System.Net.WebRequestMethods+Ftp]::MakeDirectory
        $mk.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $mk.UseBinary = $true
        $mk.UsePassive = $true
        $mk.Proxy = $null
        $resp = $mk.GetResponse(); $resp.Close()
        Write-Log "Created remote dir: $current"
      } catch {
        # ignore if exists (550) or permission denied when already present
      }
    }
    return $p
  } catch {
    Write-Log "Ensure-RemoteDirExists failed for ${remoteDir}: $($_.Exception.Message)"
    return $null
  }
}

function Select-RemoteDir([string[]]$candidates) {
  foreach ($cand in $candidates) {
    $ok = Ensure-RemoteDirExists -remoteDir $cand
    if ($ok) { return $ok }
  }
  return $candidates[0]
}

function Write-Log($msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts $msg" | Out-File -FilePath $logFile -Encoding utf8 -Append
}

function Test-RemoteExists($remotePath) {
  try {
    $uri = "ftp://${FtpHost}:${FtpPort}$remotePath"
    $req = [System.Net.FtpWebRequest]::Create($uri)
    $req.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
    $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
    $req.UseBinary = $true
    $req.UsePassive = $true
    $req.Proxy = $null
    $resp = $req.GetResponse()
    $resp.Close()
    return $true
  } catch {
    return $false
  }
}

function Invoke-UploadFile($localPath, $remoteDir) {
  $fileName = [System.IO.Path]::GetFileName($localPath)
  $remoteFile = "$remoteDir/$fileName".Replace('//','/')
  # 跳过已存在（不覆盖）
  if (Test-RemoteExists $remoteFile) {
    Write-Log "SKIP exists: $remoteFile"
    return $true
  }
  $attempt = 0
  $delay = [double]$RetryDelayMs
  while ($attempt -lt [Math]::Max(1, $MaxRetry)) {
    try {
      $uri = "ftp://${FtpHost}:${FtpPort}$remoteFile"
      $req = [System.Net.FtpWebRequest]::Create($uri)
      $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
      $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
      $req.UseBinary = $true
      $req.UsePassive = $true
      $req.Proxy = $null
      $bytes = [System.IO.File]::ReadAllBytes($localPath)
      $req.ContentLength = $bytes.Length
      $stream = $req.GetRequestStream()
      $stream.Write($bytes, 0, $bytes.Length)
      $stream.Close()
      $resp = $req.GetResponse()
      $resp.Close()
      Write-Log "UPLOAD OK: $localPath -> $remoteFile"
      return $true
    } catch {
      $attempt++
      $err = $_.Exception.Message
      Write-Log "UPLOAD RETRY[$attempt/$MaxRetry]: $localPath -> $remoteFile error=$err"
      if ($attempt -ge $MaxRetry) {
        Write-Log "UPLOAD FAIL: $localPath -> $remoteDir  error=$err"
        Write-Alert "Upload failed after $MaxRetry attempts: $fileName ($err)"
        return $false
      }
      Start-Sleep -Milliseconds [int][Math]::Min($delay, 10000)
      $delay = $delay * 1.7
    }
  }
  return $false
}

function Sync-Dir($localDir, $remoteDir, $filter='*.json') {
  if (-not (Test-Path $localDir)) { return }
  Get-ChildItem -Path $localDir -Filter $filter -File | Sort-Object LastWriteTime -Descending | ForEach-Object {
    $p = $_.FullName
    try {
      # 仅在文件稳定后再传（大小连续两次一致）
      $s1 = (Get-Item $p).Length
      Start-Sleep -Milliseconds 300
      $s2 = (Get-Item $p).Length
      if ($s1 -ne $s2) { return }
      Invoke-UploadFile -localPath $p -remoteDir $remoteDir | Out-Null
    } catch { }
  }
}

# Resolve local/remote dirs from candidates
$LocalA = Resolve-LocalDir -candidates $LocalACandidates -root $root
$LocalB = Resolve-LocalDir -candidates $LocalBCandidates -root $root
$RemoteHS = Select-RemoteDir -candidates $RemoteACandidates
$RemoteZY = Select-RemoteDir -candidates $RemoteBCandidates

Write-Log "FTP Uploader starting. Host=$FtpHost Port=$FtpPort"
Write-Log "LocalA=$LocalA LocalB=$LocalB RemoteHS=$RemoteHS RemoteZY=$RemoteZY"
$ftpOk = Test-FtpConnectivity
if (-not $ftpOk) { Write-Log "WARN: FTP connectivity test failed at startup. Will retry in loop." }

while ($true) {
  try {
    Sync-Dir -localDir $LocalA -remoteDir $RemoteHS -filter 'A-Q*.json'
    Sync-Dir -localDir $LocalB -remoteDir $RemoteZY -filter 'B-Q*.json'
  } catch {
    Write-Log "Loop error: $($_.Exception.Message)"
  }
  if ($Once) { Write-Log "Once mode enabled - exiting after single iteration"; break }
  Start-Sleep -Seconds $IntervalSeconds
}
