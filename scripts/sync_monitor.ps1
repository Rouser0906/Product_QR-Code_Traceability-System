#!/usr/bin/env powershell
# 自动同步系统监控面板
param(
    [switch]$Continuous = $false,
    [int]$RefreshSeconds = 10,
    [switch]$ShowDetails = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

function Get-ColoredStatus($status) {
    switch ($status.ToLower()) {
        "healthy" { return @{Text="🟢 正常"; Color="Green"} }
        "restarted" { return @{Text="🟡 已重启"; Color="Yellow"} }
        "failed" { return @{Text="🔴 失败"; Color="Red"} }
        default { return @{Text="⚪ 未知"; Color="Gray"} }
    }
}

function Show-SyncStatus {
    Clear-Host
    Write-Host "🔄 自动同步系统监控面板" -ForegroundColor Cyan
    Write-Host "=" * 60 -ForegroundColor DarkGray
    Write-Host "📅 更新时间: $(Get-Date)" -ForegroundColor Yellow
    Write-Host ""

    # 检查计划任务状态
    Write-Host "📋 计划任务状态:" -ForegroundColor Yellow
    $tasks = @("EnhancedFTPUploader", "SyncGuardian")
    foreach ($taskName in $tasks) {
        try {
            $taskInfo = schtasks /query /tn "$taskName" /fo CSV 2>$null | ConvertFrom-Csv
            if ($taskInfo) {
                $status = $taskInfo.Status
                $lastRun = $taskInfo.'Last Run Time'
                $nextRun = $taskInfo.'Next Run Time'
                $statusColor = if ($status -eq "Running") { "Green" } elseif ($status -eq "Ready") { "Yellow" } else { "Red" }
                Write-Host "  ✓ $taskName : $status" -ForegroundColor $statusColor
                if ($ShowDetails) {
                    Write-Host "    上次运行: $lastRun" -ForegroundColor Gray
                    Write-Host "    下次运行: $nextRun" -ForegroundColor Gray
                }
            } else {
                Write-Host "  ✗ $taskName : 未找到" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ✗ $taskName : 查询失败" -ForegroundColor Red
        }
    }
    Write-Host ""

    # 检查运行中的进程
    Write-Host "🔄 运行中的进程:" -ForegroundColor Yellow
    try {
        $uploaderProcs = Get-CimInstance Win32_Process | Where-Object { 
            $_.CommandLine -like "*enhanced_ftp_uploader*" -and $_.ProcessName -eq "powershell"
        }
        
        if ($uploaderProcs) {
            foreach ($proc in $uploaderProcs) {
                $startTime = $proc.CreationDate
                $runtime = if ($startTime) { ((Get-Date) - $startTime).ToString("hh\:mm\:ss") } else { "未知" }
                Write-Host "  📤 上传进程 PID:$($proc.ProcessId) (运行时间: $runtime)" -ForegroundColor Green
            }
        } else {
            Write-Host "  ⚠️  没有发现上传进程" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ❌ 无法查询进程信息" -ForegroundColor Red
    }
    Write-Host ""

    # 读取同步状态
    $statusFile = Join-Path $logDir "sync_status.json"
    if (Test-Path $statusFile) {
        try {
            $syncStatus = Get-Content $statusFile -Raw | ConvertFrom-Json
            $statusInfo = Get-ColoredStatus $syncStatus.status
            Write-Host "📊 同步状态: $($statusInfo.Text)" -ForegroundColor $statusInfo.Color
            Write-Host "   最后更新: $($syncStatus.timestamp)" -ForegroundColor Gray
            Write-Host "   FTP连接: $(if($syncStatus.ftp_connectivity){'🟢 正常'}else{'🔴 异常'})" -ForegroundColor $(if($syncStatus.ftp_connectivity){'Green'}else{'Red'})
            Write-Host "   日志健康: $(if($syncStatus.log_health){'🟢 正常'}else{'🔴 异常'})" -ForegroundColor $(if($syncStatus.log_health){'Green'}else{'Red'})
            
            if ($syncStatus.processes -and $syncStatus.processes.Count -gt 0) {
                Write-Host "   活跃进程: $($syncStatus.processes.Count) 个" -ForegroundColor Green
                if ($ShowDetails) {
                    foreach ($proc in $syncStatus.processes) {
                        Write-Host "     - PID:$($proc.id) 启动于:$($proc.startTime)" -ForegroundColor Gray
                    }
                }
            } else {
                Write-Host "   活跃进程: 0 个" -ForegroundColor Red
            }
        } catch {
            Write-Host "📊 同步状态: ❌ 读取失败" -ForegroundColor Red
        }
    } else {
        Write-Host "📊 同步状态: ⚪ 状态文件不存在" -ForegroundColor Gray
    }
    Write-Host ""

    # 读取指标信息
    $metricsFile = Join-Path $logDir "sync_metrics.json"
    if (Test-Path $metricsFile) {
        try {
            $metrics = Get-Content $metricsFile -Raw | ConvertFrom-Json
            Write-Host "📈 运行指标:" -ForegroundColor Yellow
            if ($metrics.restart_triggered) {
                Write-Host "   重启次数: $($metrics.restart_triggered)" -ForegroundColor Yellow
                Write-Host "   最后重启: $($metrics.last_restart_triggered)" -ForegroundColor Gray
            }
            if ($metrics.process_started) {
                Write-Host "   进程启动: $($metrics.process_started) 次" -ForegroundColor Green
            }
            if ($metrics.health_check_passed) {
                Write-Host "   健康检查: $($metrics.health_check_passed) 次通过" -ForegroundColor Green
            }
        } catch {
            Write-Host "📈 运行指标: ❌ 读取失败" -ForegroundColor Red
        }
    }
    Write-Host ""

    # 显示最近的日志
    Write-Host "📄 最近日志 (最后5条):" -ForegroundColor Yellow
    $logFiles = @(
        @{Path="enhanced_uploader.log"; Name="上传器"},
        @{Path="sync_guardian.log"; Name="守护进程"}
    )
    
    foreach ($log in $logFiles) {
        $logPath = Join-Path $logDir $log.Path
        if (Test-Path $logPath) {
            Write-Host "  📋 $($log.Name):" -ForegroundColor Cyan
            try {
                $recentLogs = Get-Content $logPath -Tail 3 -ErrorAction SilentlyContinue
                foreach ($line in $recentLogs) {
                    $color = if ($line -match "\[ERROR\]") { "Red" } 
                             elseif ($line -match "\[WARN\]") { "Yellow" }
                             elseif ($line -match "\[SUCCESS\]") { "Green" }
                             else { "White" }
                    Write-Host "    $line" -ForegroundColor $color
                }
            } catch {
                Write-Host "    ❌ 无法读取日志" -ForegroundColor Red
            }
        } else {
            Write-Host "  📋 $($log.Name): 日志文件不存在" -ForegroundColor Gray
        }
    }
    Write-Host ""

    # 显示目录状态
    Write-Host "📁 监控目录状态:" -ForegroundColor Yellow
    $monitorDirs = @("cloud\demo_json_a", "cloud\demo_json_b")
    foreach ($dir in $monitorDirs) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (Test-Path $fullPath) {
            $fileCount = (Get-ChildItem $fullPath -Filter "*.json" -File | Measure-Object).Count
            $latestFile = Get-ChildItem $fullPath -Filter "*.json" -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            Write-Host "  📂 $dir : $fileCount 个文件" -ForegroundColor Green
            if ($latestFile -and $ShowDetails) {
                $age = ((Get-Date) - $latestFile.LastWriteTime).TotalMinutes
                Write-Host "    最新文件: $($latestFile.Name) (${age:F1}分钟前)" -ForegroundColor Gray
            }
        } else {
            Write-Host "  📂 $dir : 目录不存在" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor DarkGray
    
    if ($Continuous) {
        Write-Host "⏰ $RefreshSeconds 秒后自动刷新... (按 Ctrl+C 退出)" -ForegroundColor Gray
    }
}

# 主循环
do {
    Show-SyncStatus
    
    if ($Continuous) {
        Start-Sleep -Seconds $RefreshSeconds
    }
} while ($Continuous)