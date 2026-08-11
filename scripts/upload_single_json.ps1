param(
  [Parameter(Mandatory=$true)][string]$FilePath,
  [ValidateSet('hs','zy')][string]$Company = 'hs',
  [string]$FtpHost = 'scan.example.com',
  [int]$FtpPort = 21,
  [string]$FtpUser = 'your_ftp_username',
  [string]$FtpPass = '[REDACTED-FTP-PASSWORD]'
)

$ErrorActionPreference = 'SilentlyContinue'

try {
  $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
  $ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
  Set-Location $ProjectRoot
} catch { $ProjectRoot = (Get-Location).Path }

$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'ftp_uploader.log'

function Write-Log($msg) {
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  "$ts [FORCE] $msg" | Out-File -FilePath $logFile -Encoding utf8 -Append
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
        $resp = $mk.GetResponse(); $resp.Close()
      } catch { }
    }
    return $p
  } catch { return $null }
}

function Invoke-UploadFile($localPath, $remoteDir) {
  try {
    $fileName = [System.IO.Path]::GetFileName($localPath)
    $remoteFile = "$remoteDir/$fileName".Replace('//','/')
    $uri = "ftp://${FtpHost}:${FtpPort}$remoteFile"
    $req = [System.Net.FtpWebRequest]::Create($uri)
    $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
    $req.UseBinary = $true
    $req.UsePassive = $true
    $bytes = [System.IO.File]::ReadAllBytes($localPath)
    $req.ContentLength = $bytes.Length
    $stream = $req.GetRequestStream()
    $stream.Write($bytes, 0, $bytes.Length)
    $stream.Close()
    $resp = $req.GetResponse(); $resp.Close()
    Write-Log "UPLOAD OK: $localPath -> $remoteFile"
    return $true
  } catch {
    Write-Log "UPLOAD FAIL: $localPath -> $remoteDir  error=$($_.Exception.Message)"
    return $false
  }
}

if (-not (Test-Path $FilePath)) { Write-Host "文件不存在: $FilePath" -ForegroundColor Red; exit 1 }
$remoteDir = if ($Company -eq 'hs') { '/companies/demo_json_a' } else { '/companies/demo_json_b' }
$remoteDir = Ensure-RemoteDirExists -remoteDir $remoteDir

$ok = Invoke-UploadFile -localPath $FilePath -remoteDir $remoteDir
if ($ok) { Write-Host "✅ 上传成功" -ForegroundColor Green } else { Write-Host "❌ 上传失败" -ForegroundColor Red; exit 1 }
