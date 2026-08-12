#!/usr/bin/env powershell
# 告警监控仪表板 - 实时显示告警状态
param(
    [switch]$Continuous = $false,
    [int]$RefreshSeconds = 30,
    [switch]$ShowHistory = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

function Show-AlertDashboard {
    Clear-Host
    Write-Host "🔔 自动同步系统告警监控仪表板" -ForegroundColor Cyan
    Write-Host "=================================" -ForegroundColor DarkGray
    Write-Host "📅 更新时间: $(Get-Date)" -ForegroundColor Yellow
    Write-Host ""

    # 检查告警监控服务状态
    Write-Host "📋 监控服务状态:" -ForegroundColor Yellow
    $alertTask = schtasks /query /tn "AlertMonitor" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ 告警监控任务: 运行中" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 告警监控任务: 未安装" -ForegroundColor Red
    }

    # 检查系统健康状态
    Write-Host "🔍 系统健康检查:" -ForegroundColor Yellow
    
    # 1. 检查进程状态
    $procs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -like "*windows_ftp_json_uploader*" -or
        $_.CommandLine -like "*high_performance_uploader*"
    }
    $procStatus = if ($procs.Count -gt 0) { "正常 ($($procs.Count)个)" } else { "异常" }
    $procColor = if ($procs.Count -gt 0) { "Green" } else { "Red" }
    Write-Host "  📊 上传进程: $procStatus" -ForegroundColor $procColor

    # 2. 检查日志活跃度
    $logFile = Join-Path $logDir "ftp_uploader.log"
    if (Test-Path $logFile) {
        $lastWrite = (Get-Item $logFile).LastWriteTime
        $age = ((Get-Date) - $lastWrite).TotalMinutes
        $logStatus = if ($age -lt 10) { "活跃" } elseif ($age -lt 30) { "缓慢" } else { "停滞" }
        $logColor = if ($age -lt 10) { "Green" } elseif ($age -lt 30) { "Yellow" } else { "Red" }
        Write-Host "  📄 日志活跃度: $logStatus ($([math]::Round($age, 1))分钟前)" -ForegroundColor $logColor
    } else {
        Write-Host "  📄 日志活跃度: 无日志文件" -ForegroundColor Red
    }

    # 3. 检查磁盘空间
    try {
        $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        $spaceStatus = if ($freeSpaceGB -gt 5) { "充足" } elseif ($freeSpaceGB -gt 1) { "一般" } else { "不足" }
        $spaceColor = if ($freeSpaceGB -gt 5) { "Green" } elseif ($freeSpaceGB -gt 1) { "Yellow" } else { "Red" }
        Write-Host "  💾 磁盘空间: $spaceStatus (${freeSpaceGB}GB)" -ForegroundColor $spaceColor
    } catch {
        Write-Host "  💾 磁盘空间: 检查失败" -ForegroundColor Red
    }

    # 4. 检查FTP连接
    try {
        $uri = "ftp://scan.example.com:21"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $req.Credentials = New-Object System.Net.NetworkCredential("your_ftp_username", "[REDACTED-FTP-PASSWORD]")
        $req.Timeout = 5000
        $req.UsePassive = $true
        $req.Proxy = $null
        $resp = $req.GetResponse()
        $resp.Close()
        Write-Host "  🌐 FTP连接: 正常" -ForegroundColor Green
    } catch {
        Write-Host "  🌐 FTP连接: 异常" -ForegroundColor Red
    }

    # 5. 检查文件队列
    $aCount = if (Test-Path "cloud\demo_json_a") { (Get-ChildItem "cloud\demo_json_a" -Filter "*.json").Count } else { 0 }
    $bCount = if (Test-Path "cloud\demo_json_b") { (Get-ChildItem "cloud\demo_json_b" -Filter "*.json").Count } else { 0 }
    $totalQueue = $aCount + $bCount
    $queueStatus = if ($totalQueue -lt 50) { "正常" } elseif ($totalQueue -lt 100) { "较高" } else { "过高" }
    $queueColor = if ($totalQueue -lt 50) { "Green" } elseif ($totalQueue -lt 100) { "Yellow" } else { "Red" }
    Write-Host "  📁 文件队列: $queueStatus ($totalQueue个)" -ForegroundColor $queueColor

    Write-Host ""

    # 显示告警历史
    $alertHistoryFile = Join-Path $logDir "alert_history.json"
    if (Test-Path $alertHistoryFile) {
        try {
            $history = Get-Content $alertHistoryFile -Raw | ConvertFrom-Json
            $recentAlerts = $history | Where-Object { 
                ([DateTime]::Parse($_.timestamp) -gt (Get-Date).AddHours(-24)) 
            }
            
            Write-Host "🚨 最近24小时告警 ($($recentAlerts.Count)次):" -ForegroundColor Yellow
            if ($recentAlerts.Count -eq 0) {
                Write-Host "  ✅ 无告警记录" -ForegroundColor Green
            } else {
                $recentAlerts | Select-Object -Last 5 | ForEach-Object {
                    $color = switch($_.severity) {
                        "high" { "Red" }
                        "medium" { "Yellow" }
                        default { "White" }
                    }
                    $icon = switch($_.severity) {
                        "high" { "🔴" }
                        "medium" { "🟡" }
                        default { "⚪" }
                    }
                    Write-Host "  $icon $($_.timestamp) [$($_.type)] $($_.message)" -ForegroundColor $color
                }
            }
        } catch {
            Write-Host "  ⚠️  告警历史读取失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "🚨 告警历史: 无记录文件" -ForegroundColor Gray
    }

    Write-Host ""
    Write-Host "=================================" -ForegroundColor DarkGray
    
    if ($Continuous) {
        Write-Host "⏰ $RefreshSeconds 秒后自动刷新... (按 Ctrl+C 退出)" -ForegroundColor Gray
    }
}

# 主循环
do {
    Show-AlertDashboard
    
    if ($Continuous) {
        Start-Sleep -Seconds $RefreshSeconds
    }
} while ($Continuous)