#!/usr/bin/env powershell
# 简化版自动同步系统监控面板
param(
    [switch]$Continuous = $false,
    [int]$RefreshSeconds = 10,
    [switch]$ShowDetails = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

function Show-SyncStatus {
    Clear-Host
    Write-Host "自动同步系统监控面板" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor DarkGray
    Write-Host "更新时间: $(Get-Date)" -ForegroundColor Yellow
    Write-Host ""

    # 检查计划任务状态
    Write-Host "计划任务状态:" -ForegroundColor Yellow
    $tasks = @("EnhancedFTPUploader", "SyncGuardian")
    foreach ($taskName in $tasks) {
        try {
            $result = schtasks /query /tn "$taskName" /fo CSV 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ $taskName : 正常" -ForegroundColor Green
            } else {
                Write-Host "  ✗ $taskName : 未找到" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ✗ $taskName : 查询失败" -ForegroundColor Red
        }
    }
    Write-Host ""

    # 检查运行中的进程
    Write-Host "运行中的进程:" -ForegroundColor Yellow
    try {
        $uploaderProcs = Get-CimInstance Win32_Process | Where-Object { 
            $_.CommandLine -like "*enhanced_ftp_uploader*" -and $_.ProcessName -eq "powershell"
        }
        
        if ($uploaderProcs) {
            foreach ($proc in $uploaderProcs) {
                Write-Host "  上传进程 PID:$($proc.ProcessId)" -ForegroundColor Green
            }
        } else {
            Write-Host "  没有发现上传进程" -ForegroundColor Red
        }
    } catch {
        Write-Host "  无法查询进程信息" -ForegroundColor Red
    }
    Write-Host ""

    # 读取同步状态
    $statusFile = Join-Path $logDir "sync_status.json"
    if (Test-Path $statusFile) {
        try {
            $syncStatus = Get-Content $statusFile -Raw | ConvertFrom-Json
            Write-Host "同步状态: $($syncStatus.status)" -ForegroundColor Green
            Write-Host "最后更新: $($syncStatus.timestamp)" -ForegroundColor Gray
            Write-Host "FTP连接: $(if($syncStatus.ftp_connectivity){'正常'}else{'异常'})" -ForegroundColor $(if($syncStatus.ftp_connectivity){'Green'}else{'Red'})
        } catch {
            Write-Host "同步状态: 读取失败" -ForegroundColor Red
        }
    } else {
        Write-Host "同步状态: 状态文件不存在" -ForegroundColor Gray
    }
    Write-Host ""

    # 显示最近的日志
    Write-Host "最近日志 (最后3条):" -ForegroundColor Yellow
    $logFiles = @(
        @{Path="enhanced_uploader.log"; Name="上传器"},
        @{Path="sync_guardian.log"; Name="守护进程"}
    )
    
    foreach ($log in $logFiles) {
        $logPath = Join-Path $logDir $log.Path
        if (Test-Path $logPath) {
            Write-Host "  $($log.Name):" -ForegroundColor Cyan
            try {
                $recentLogs = Get-Content $logPath -Tail 2 -ErrorAction SilentlyContinue
                foreach ($line in $recentLogs) {
                    $color = if ($line -match "ERROR") { "Red" } 
                             elseif ($line -match "WARN") { "Yellow" }
                             elseif ($line -match "SUCCESS") { "Green" }
                             else { "White" }
                    Write-Host "    $line" -ForegroundColor $color
                }
            } catch {
                Write-Host "    无法读取日志" -ForegroundColor Red
            }
        } else {
            Write-Host "  $($log.Name): 日志文件不存在" -ForegroundColor Gray
        }
    }
    Write-Host ""

    # 显示目录状态
    Write-Host "监控目录状态:" -ForegroundColor Yellow
    $monitorDirs = @("cloud\demo_json_a", "cloud\demo_json_b")
    foreach ($dir in $monitorDirs) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (Test-Path $fullPath) {
            $fileCount = (Get-ChildItem $fullPath -Filter "*.json" -File | Measure-Object).Count
            Write-Host "  $dir : $fileCount 个文件" -ForegroundColor Green
        } else {
            Write-Host "  $dir : 目录不存在" -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "========================================" -ForegroundColor DarkGray
    
    if ($Continuous) {
        Write-Host "$RefreshSeconds 秒后自动刷新... (按 Ctrl+C 退出)" -ForegroundColor Gray
    }
}

# 主循环
do {
    Show-SyncStatus
    
    if ($Continuous) {
        Start-Sleep -Seconds $RefreshSeconds
    }
} while ($Continuous)