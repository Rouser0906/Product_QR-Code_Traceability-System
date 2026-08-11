param(
  [string]$TaskName = "QRJsonyour_ftp_username",
  [string]$ProjectRoot = (Get-Location).Path,
  [string]$Uploader = "scripts\windows_ftp_json_uploader.ps1"
)

$uploaderPath = Join-Path $ProjectRoot $Uploader
if (-not (Test-Path $uploaderPath)) { Write-Host "缺少 $uploaderPath"; exit 1 }

# 删除旧任务
schtasks /delete /tn "$TaskName" /f 2>$null | Out-Null

# 以 SYSTEM 账户开机启动，不弹窗
schtasks /create /tn "$TaskName" /sc onstart /ru "SYSTEM" /rl HIGHEST /tr "powershell -ExecutionPolicy Bypass -File `"$uploaderPath`"" /f
if ($LASTEXITCODE -ne 0) { Write-Host "创建计划任务失败" -ForegroundColor Red; exit 1 }

# 立即运行
schtasks /run /tn "$TaskName"
Write-Host "✅ 已创建并启动计划任务：$TaskName" -ForegroundColor Green
