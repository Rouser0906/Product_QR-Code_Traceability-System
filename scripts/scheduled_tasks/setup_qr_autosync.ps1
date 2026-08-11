# 以管理员身份运行本脚本：创建并启动计划任务，常驻运行 QR 自动同步
param(
  [string]$PythonPath = "C:\\Python313\\pythonw.exe",
  [string]$ProjectRoot = "C:\\Projects\\Demo",
  [string]$TaskName = "QRJsonAutoSync"
)

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    Write-Host "❌ 需要以管理员身份运行此脚本" -ForegroundColor Red
    exit 1
  }
}

Assert-Admin

$runPy = $PythonPath
if (-not (Test-Path $runPy)) {
  Write-Host "⚠️ 未找到 $runPy ，改用 python.exe 前台模式" -ForegroundColor Yellow
  $runPy = "C:\\Python313\\python.exe"
}

$scriptPath = Join-Path $ProjectRoot "scripts\\run_auto_sync.py"
if (-not (Test-Path $scriptPath)) {
  Write-Host "❌ 未找到脚本：$scriptPath" -ForegroundColor Red
  exit 1
}

# 创建日志目录
New-Item -ItemType Directory -Force -Path (Join-Path $ProjectRoot "auto_sync\\logs") | Out-Null

# 先删除旧任务（忽略不存在的错误）
schtasks /delete /tn "$TaskName" /f 2>$null | Out-Null

# 注册计划任务：开机触发，SYSTEM 账户，最高权限
$tr = ('"{0}" "{1}"' -f $runPy, $scriptPath)
schtasks /create /tn "$TaskName" /sc onstart /ru "SYSTEM" /rl HIGHEST /tr $tr /f
if ($LASTEXITCODE -ne 0) {
  Write-Host "❌ 创建计划任务失败（请检查路径与权限）" -ForegroundColor Red
  exit 1
}

# 立即运行一次
schtasks /run /tn "$TaskName"

Write-Host ("✅ 计划任务已创建并启动：{0}" -f $TaskName) -ForegroundColor Green
Write-Host ("📂 项目目录：{0}" -f $ProjectRoot) -ForegroundColor Cyan

# 打印日志查看指引
$logPath = Join-Path $ProjectRoot "auto_sync\\logs\\auto_sync.log"
Write-Host "🧾 日志查看命令：" -ForegroundColor Yellow
Write-Host ("Get-Content `"{0}`" -Tail 100" -f $logPath) -ForegroundColor Yellow
