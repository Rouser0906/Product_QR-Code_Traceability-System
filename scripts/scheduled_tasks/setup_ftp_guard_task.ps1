param(
  [string]$TaskName = 'QRJsonFtpGuard',
  [string]$ProjectRoot = (Get-Location).Path
)

$guard = Join-Path $ProjectRoot 'scripts\guard_ftp_uploader.ps1'
if (-not (Test-Path $guard)) { Write-Host "缺少 $guard"; exit 1 }

schtasks /delete /tn "$TaskName" /f 2>$null | Out-Null

# 每5分钟检查一次，看门狗
schtasks /create /tn "$TaskName" /sc minute /mo 5 /ru "SYSTEM" /rl HIGHEST /tr "powershell -ExecutionPolicy Bypass -File `"$guard`"" /f
if ($LASTEXITCODE -ne 0) { Write-Host "创建看门狗任务失败" -ForegroundColor Red; exit 1 }

schtasks /run /tn "$TaskName"
Write-Host "✅ 已创建并启动看门狗任务：$TaskName" -ForegroundColor Green
