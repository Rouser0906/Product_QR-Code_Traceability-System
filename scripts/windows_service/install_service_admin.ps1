# QRJsonAutoSync Windows 服务一键安装脚本（需以管理员身份运行）
param(
    [string]$Python = "python"
)

function Assert-Admin {
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        Write-Host "❌ 需要以管理员身份运行此脚本" -ForegroundColor Red
        Write-Host "请右键 PowerShell → 以管理员身份运行，然后执行：" -ForegroundColor Yellow
        Write-Host "PowerShell -ExecutionPolicy Bypass -File scripts\\windows_service\\install_service_admin.ps1" -ForegroundColor Cyan
        exit 1
    }
}

Assert-Admin

# 切换到项目根目录（脚本所在目录的两级上级）
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $ProjectRoot
Write-Host "📂 项目目录: $ProjectRoot" -ForegroundColor Cyan

# 准备日志目录
New-Item -ItemType Directory -Force -Path "auto_sync\\logs" | Out-Null

# 安装依赖（若已安装会自动跳过）
Write-Host "📦 检查/安装依赖：pywin32, watchdog" -ForegroundColor Yellow
try {
    & $Python -m pip install --upgrade pip | Out-Null
    & $Python -m pip install pywin32 watchdog | Out-Null
} catch { Write-Host "⚠️ 依赖安装发生警告：$($_.Exception.Message)" -ForegroundColor Yellow }

# 停止并删除旧服务
Write-Host "🛑 停止并删除旧服务（如存在）..." -ForegroundColor Yellow
try { Stop-Service -Name "QRJsonAutoSync" -Force -ErrorAction SilentlyContinue } catch {}
try { & $Python scripts\windows_service\auto_sync_win_service.py remove | Out-Null } catch {}
try { sc.exe delete QRJsonAutoSync | Out-Null } catch {}
Start-Sleep -Seconds 1

# 安装新服务
Write-Host "🛠️ 正在安装服务..." -ForegroundColor Yellow
& $Python scripts\windows_service\auto_sync_win_service.py install
if ($LASTEXITCODE -ne 0) { Write-Host "❌ 服务安装失败" -ForegroundColor Red; exit 1 }

# 配置开机自启动
Write-Host "⚙️ 设置服务开机自启动..." -ForegroundColor Yellow
Set-Service -Name "QRJsonAutoSync" -StartupType Automatic

# 配置失败自动重启（三次，每次5秒后尝试）
Write-Host "🔁 配置服务失败自动重启策略..." -ForegroundColor Yellow
sc.exe failure QRJsonAutoSync reset= 60 actions= restart/5000/restart/5000/restart/5000 | Out-Null

# 启动服务
Write-Host "🚀 启动服务..." -ForegroundColor Yellow
& $Python scripts\windows_service\auto_sync_win_service.py start
Start-Sleep -Seconds 5

# 显示服务状态
$svc = Get-Service -Name "QRJsonAutoSync" -ErrorAction SilentlyContinue
if ($null -eq $svc) {
    Write-Host "❌ 未找到服务 QRJsonAutoSync" -ForegroundColor Red
    exit 1
}
Write-Host ("📊 服务状态: {0} / 启动类型: {1}" -f $svc.Status, $svc.StartType) -ForegroundColor Green

# 输出服务日志与业务日志尾部
Write-Host "\n🧾 最近日志（auto_sync_win_service.log 若无则显示 auto_sync.log）" -ForegroundColor Yellow
$svcLog = "auto_sync\\logs\\auto_sync_win_service.log"
$bizLog = "auto_sync\\logs\\auto_sync.log"
if (Test-Path $svcLog) { Get-Content $svcLog -Tail 50 } elseif (Test-Path $bizLog) { Get-Content $bizLog -Tail 50 } else { Write-Host "(暂无日志生成)" }

Write-Host "\n✅ 安装与启动流程已完成。如果状态非 Running，请将上面日志发我排查。" -ForegroundColor Green
