#!/usr/bin/env powershell
# 设置增强版自动同步系统
param(
    [string]$ProjectRoot = $PWD.Path,
    [string]$TaskNameUploader = "EnhancedFTPUploader",
    [string]$TaskNameGuardian = "SyncGuardian", 
    [switch]$Force = $false,
    [switch]$Debug = $false
)

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-ColorOutput($message, $color = "White") {
    Write-Host $message -ForegroundColor $color
}

if (-not (Test-Administrator)) {
    Write-ColorOutput "❌ 需要管理员权限运行此脚本" "Red"
    Write-ColorOutput "请右键选择'以管理员身份运行'" "Yellow"
    exit 1
}

Write-ColorOutput "🚀 设置增强版自动同步系统..." "Green"
Write-ColorOutput "📂 项目目录: $ProjectRoot" "Cyan"

# 检查必要文件
$requiredFiles = @(
    "scripts\enhanced_ftp_uploader.ps1",
    "scripts\enhanced_sync_guardian.ps1", 
    "auto_sync\enhanced_config.json"
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $ProjectRoot $file
    if (-not (Test-Path $fullPath)) {
        Write-ColorOutput "❌ 缺少必要文件: $file" "Red"
        exit 1
    }
}

Write-ColorOutput "✅ 所有必要文件检查通过" "Green"

# 创建日志目录
$logDir = Join-Path $ProjectRoot "auto_sync\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Write-ColorOutput "📁 日志目录已创建: $logDir" "Green"

# 删除旧任务
if ($Force) {
    Write-ColorOutput "🧹 清理旧的计划任务..." "Yellow"
    schtasks /delete /tn "$TaskNameUploader" /f 2>$null | Out-Null
    schtasks /delete /tn "$TaskNameGuardian" /f 2>$null | Out-Null
    schtasks /delete /tn "QRJsonAutoSync" /f 2>$null | Out-Null
    schtasks /delete /tn "FTP_JSON_Uploader_Guard" /f 2>$null | Out-Null
}

# 创建上传器计划任务
Write-ColorOutput "📋 创建FTP上传器计划任务..." "Cyan"
$uploaderScript = Join-Path $ProjectRoot "scripts\enhanced_ftp_uploader.ps1"
$uploaderArgs = if ($Debug) { "-Debug" } else { "" }
$uploaderCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$uploaderScript`" $uploaderArgs"

$createUploader = schtasks /create /tn "$TaskNameUploader" /sc onstart /delay 0000:30 /ru "SYSTEM" /rl HIGHEST /tr "$uploaderCommand" /f
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "✅ 上传器计划任务创建成功" "Green"
} else {
    Write-ColorOutput "❌ 上传器计划任务创建失败" "Red"
    exit 1
}

# 创建守护进程计划任务  
Write-ColorOutput "📋 创建守护进程计划任务..." "Cyan"
$guardianScript = Join-Path $ProjectRoot "scripts\enhanced_sync_guardian.ps1"
$guardianArgs = if ($Debug) { "-Debug" } else { "" }
$guardianCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$guardianScript`" $guardianArgs"

$createGuardian = schtasks /create /tn "$TaskNameGuardian" /sc minute /mo 5 /ru "SYSTEM" /rl HIGHEST /tr "$guardianCommand" /f
if ($LASTEXITCODE -eq 0) {
    Write-ColorOutput "✅ 守护进程计划任务创建成功" "Green"
} else {
    Write-ColorOutput "❌ 守护进程计划任务创建失败" "Red"
    exit 1
}

# 立即启动任务
Write-ColorOutput "🚀 启动计划任务..." "Cyan"
schtasks /run /tn "$TaskNameUploader" | Out-Null
Start-Sleep -Seconds 3
schtasks /run /tn "$TaskNameGuardian" | Out-Null

Write-ColorOutput "✅ 增强版自动同步系统设置完成！" "Green"
Write-ColorOutput "" 
Write-ColorOutput "📊 管理命令:" "Yellow"
Write-ColorOutput "  查看任务状态: schtasks /query /tn `"$TaskNameUploader`" /fo LIST" "White"
Write-ColorOutput "  查看守护进程: schtasks /query /tn `"$TaskNameGuardian`" /fo LIST" "White"
Write-ColorOutput "  手动运行上传: schtasks /run /tn `"$TaskNameUploader`"" "White"
Write-ColorOutput "  手动运行守护: schtasks /run /tn `"$TaskNameGuardian`"" "White"
Write-ColorOutput "  停止任务: schtasks /end /tn `"$TaskNameUploader`"" "White"
Write-ColorOutput ""
Write-ColorOutput "📋 日志文件:" "Yellow"
Write-ColorOutput "  上传日志: $logDir\enhanced_uploader.log" "White"
Write-ColorOutput "  守护日志: $logDir\sync_guardian.log" "White"
Write-ColorOutput "  状态文件: $logDir\sync_status.json" "White"
Write-ColorOutput "  指标文件: $logDir\sync_metrics.json" "White"
Write-ColorOutput ""
Write-ColorOutput "🔧 测试命令:" "Yellow"
Write-ColorOutput "  单次上传测试: .\scripts\enhanced_ftp_uploader.ps1 -Once -Debug" "White"
Write-ColorOutput "  系统监控: .\scripts\sync_monitor.ps1" "White"