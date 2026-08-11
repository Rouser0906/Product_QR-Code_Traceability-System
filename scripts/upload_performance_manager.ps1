#!/usr/bin/env powershell
# 上传性能管理器 - 智能切换和监控不同的上传策略
param(
    [ValidateSet("Standard", "HighPerf", "Turbo", "Auto")]
    [string]$Mode = "Auto",
    [switch]$Monitor = $false,
    [switch]$Install = $false,
    [switch]$Status = $false,
    [switch]$Stop = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

# 性能模式配置
$PerformanceModes = @{
    Standard = @{
        Script = "windows_ftp_json_uploader.ps1"
        Args = ""
        Description = "标准模式 - 稳定可靠，单线程上传"
        Concurrent = 1
        Interval = 15
        MaxRetry = 5
    }
    HighPerf = @{
        Script = "high_performance_uploader.ps1"
        Args = "-MaxConcurrent 3 -BatchSize 20 -IntervalSeconds 10"
        Description = "高性能模式 - 并发上传，优化速度"
        Concurrent = 3
        Interval = 10
        MaxRetry = 3
    }
    Turbo = @{
        Script = "high_performance_uploader.ps1"
        Args = "-MaxConcurrent 5 -BatchSize 50 -IntervalSeconds 5 -FastMode"
        Description = "极速模式 - 最大并发，跳过检查"
        Concurrent = 5
        Interval = 5
        MaxRetry = 2
    }
}

function Write-Log($msg, $level = "INFO") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $logMsg = "$ts [$level] MANAGER: $msg"
    
    $color = switch($level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    Write-Host $logMsg -ForegroundColor $color
    
    $managerLog = Join-Path $logDir "performance_manager.log"
    $logMsg | Out-File -FilePath $managerLog -Encoding utf8 -Append
}

function Get-SystemLoad {
    try {
        # 检查CPU使用率
        $cpu = Get-CimInstance -ClassName Win32_Processor | 
               Measure-Object -Property LoadPercentage -Average | 
               Select-Object -ExpandProperty Average
        
        # 检查内存使用率
        $mem = Get-CimInstance -ClassName Win32_OperatingSystem
        $memUsed = (($mem.TotalVisibleMemorySize - $mem.FreePhysicalMemory) / $mem.TotalVisibleMemorySize) * 100
        
        # 检查网络活跃度
        $netstat = netstat -e 2>$null
        $networkActive = if ($netstat) { $true } else { $false }
        
        return @{
            CPU = [math]::Round($cpu, 1)
            Memory = [math]::Round($memUsed, 1)
            NetworkActive = $networkActive
        }
    } catch {
        return @{ CPU = 0; Memory = 0; NetworkActive = $false }
    }
}

function Get-UploadQueueSize {
    $aCount = if (Test-Path "cloud\demo_json_a") { 
        (Get-ChildItem "cloud\demo_json_a" -Filter "*.json" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }).Count 
    } else { 0 }
    
    $zyCount = if (Test-Path "cloud\demo_json_b") { 
        (Get-ChildItem "cloud\demo_json_b" -Filter "*.json" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }).Count 
    } else { 0 }
    
    return $aCount + $zyCount
}

function Get-UploadPerformance {
    try {
        $perfLogFile = Join-Path $logDir "upload_performance.log"
        if (-not (Test-Path $perfLogFile)) { return @{} }
        
        $recentLogs = Get-Content $perfLogFile -Tail 100 | Where-Object { $_ -match "upload_success" }
        
        if ($recentLogs.Count -eq 0) { return @{} }
        
        $speeds = @()
        foreach ($log in $recentLogs) {
            $parts = $log.Split(',')
            if ($parts.Length -ge 5) {
                $speed = [double]$parts[4]
                if ($speed -gt 0) { $speeds += $speed }
            }
        }
        
        if ($speeds.Count -eq 0) { return @{} }
        
        return @{
            AvgSpeed = [math]::Round(($speeds | Measure-Object -Average).Average, 2)
            MaxSpeed = [math]::Round(($speeds | Measure-Object -Maximum).Maximum, 2)
            RecentUploads = $recentLogs.Count
        }
    } catch {
        return @{}
    }
}

function Select-OptimalMode {
    $systemLoad = Get-SystemLoad
    $queueSize = Get-UploadQueueSize
    $performance = Get-UploadPerformance
    
    Write-Log "系统负载: CPU=$($systemLoad.CPU)%, 内存=$($systemLoad.Memory)%, 队列=$queueSize" "INFO"
    
    # 智能模式选择逻辑
    if ($systemLoad.CPU -gt 80 -or $systemLoad.Memory -gt 85) {
        $selectedMode = "Standard"
        $reason = "系统负载过高"
    } elseif ($queueSize -gt 50) {
        $selectedMode = "Turbo"
        $reason = "队列文件过多"
    } elseif ($queueSize -gt 10) {
        $selectedMode = "HighPerf"
        $reason = "队列文件适中"
    } else {
        $selectedMode = "Standard"
        $reason = "队列文件较少"
    }
    
    Write-Log "选择模式: $selectedMode ($reason)" "INFO"
    return $selectedMode
}

function Stop-AllUploaders {
    Write-Log "停止所有上传进程..." "INFO"
    
    $uploadProcs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -like "*windows_ftp_json_uploader*" -or
        $_.CommandLine -like "*high_performance_uploader*"
    }
    
    foreach ($proc in $uploadProcs) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Log "已停止进程: PID $($proc.ProcessId)" "SUCCESS"
        } catch {
            Write-Log "停止进程失败: PID $($proc.ProcessId)" "WARN"
        }
    }
    
    # 停止相关计划任务
    $tasks = @("SyncMonitor", "OptimizedSyncGuard", "PerformanceUploader")
    foreach ($taskName in $tasks) {
        try {
            schtasks /end /tn "$taskName" 2>$null | Out-Null
        } catch {}
    }
    
    Start-Sleep -Seconds 2
    Write-Log "所有上传进程已停止" "SUCCESS"
}

function Start-UploaderWithMode($modeName) {
    $config = $PerformanceModes[$modeName]
    if (-not $config) {
        Write-Log "无效的模式: $modeName" "ERROR"
        return $false
    }
    
    Write-Log "启动上传器: $modeName - $($config.Description)" "INFO"
    
    $scriptPath = Join-Path $ProjectRoot "scripts\$($config.Script)"
    if (-not (Test-Path $scriptPath)) {
        Write-Log "上传脚本不存在: $($config.Script)" "ERROR"
        return $false
    }
    
    try {
        $args = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" $($config.Args)"
        $proc = Start-Process -FilePath "powershell.exe" -ArgumentList $args -WindowStyle Hidden -PassThru
        
        Write-Log "上传器已启动: PID $($proc.Id), 模式: $modeName" "SUCCESS"
        
        # 创建对应的监控任务
        $taskName = "PerformanceUploader_$modeName"
        $guardScript = Join-Path $ProjectRoot "scripts\guard_ftp_uploader.ps1"
        
        schtasks /delete /tn "$taskName" /f 2>$null | Out-Null
        $result = schtasks /create /tn "$taskName" /sc minute /mo $($config.Interval / 5) /tr "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$guardScript`"" /ru "SYSTEM" /rl HIGHEST /f
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "监控任务已创建: $taskName" "SUCCESS"
        }
        
        return $true
    } catch {
        Write-Log "启动上传器失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-CurrentStatus {
    Write-Host "🚀 上传性能管理器状态" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor DarkGray
    
    # 检查运行中的上传进程
    $standardProcs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*windows_ftp_json_uploader*" }
    $perfProcs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*high_performance_uploader*" }
    
    Write-Host "📊 运行状态:" -ForegroundColor Yellow
    Write-Host "  标准上传器: $($standardProcs.Count) 个进程" -ForegroundColor $(if($standardProcs.Count -gt 0){'Green'}else{'Gray'})
    Write-Host "  高性能上传器: $($perfProcs.Count) 个进程" -ForegroundColor $(if($perfProcs.Count -gt 0){'Green'}else{'Gray'})
    
    # 系统负载
    $load = Get-SystemLoad
    Write-Host "💻 系统负载:" -ForegroundColor Yellow
    Write-Host "  CPU: $($load.CPU)%" -ForegroundColor $(if($load.CPU -lt 70){'Green'}elseif($load.CPU -lt 85){'Yellow'}else{'Red'})
    Write-Host "  内存: $($load.Memory)%" -ForegroundColor $(if($load.Memory -lt 70){'Green'}elseif($load.Memory -lt 85){'Yellow'}else{'Red'})
    
    # 队列状态
    $queueSize = Get-UploadQueueSize
    Write-Host "📁 待上传队列: $queueSize 个文件" -ForegroundColor $(if($queueSize -lt 10){'Green'}elseif($queueSize -lt 50){'Yellow'}else{'Red'})
    
    # 性能统计
    $perf = Get-UploadPerformance
    if ($perf.Count -gt 0) {
        Write-Host "⚡ 最近性能:" -ForegroundColor Yellow
        Write-Host "  平均速度: $($perf.AvgSpeed) KB/s" -ForegroundColor Green
        Write-Host "  最高速度: $($perf.MaxSpeed) KB/s" -ForegroundColor Green
        Write-Host "  最近上传: $($perf.RecentUploads) 个文件" -ForegroundColor Green
    }
    
    # 建议的模式
    if ($Mode -eq "Auto") {
        $suggested = Select-OptimalMode
        Write-Host "🎯 建议模式: $suggested" -ForegroundColor Cyan
    }
    
    Write-Host ""
}

function Install-PerformanceSystem {
    Write-Log "安装高性能上传系统..." "INFO"
    
    # 停止现有进程
    Stop-AllUploaders
    
    # 选择最优模式
    $selectedMode = if ($Mode -eq "Auto") { Select-OptimalMode } else { $Mode }
    
    # 启动上传器
    $success = Start-UploaderWithMode $selectedMode
    
    if ($success) {
        Write-Log "高性能上传系统安装成功，模式: $selectedMode" "SUCCESS"
        Start-Sleep -Seconds 3
        Show-CurrentStatus
    } else {
        Write-Log "高性能上传系统安装失败" "ERROR"
    }
}

function Start-PerformanceMonitoring {
    Write-Log "启动性能监控..." "INFO"
    
    $monitorCount = 0
    while ($true) {
        $monitorCount++
        Clear-Host
        
        Write-Host "🔄 上传性能实时监控 - 第 $monitorCount 次检查" -ForegroundColor Cyan
        Write-Host "时间: $(Get-Date)" -ForegroundColor Yellow
        Write-Host ""
        
        Show-CurrentStatus
        
        # 智能模式切换检查
        if ($Mode -eq "Auto") {
            $currentProcs = Get-CimInstance Win32_Process | Where-Object { 
                $_.CommandLine -like "*windows_ftp_json_uploader*" -or
                $_.CommandLine -like "*high_performance_uploader*"
            }
            
            if ($currentProcs.Count -eq 0) {
                Write-Log "检测到上传进程停止，自动重启..." "WARN"
                $optimalMode = Select-OptimalMode
                Start-UploaderWithMode $optimalMode
            }
        }
        
        Write-Host "⏰ 30秒后刷新... (按 Ctrl+C 退出)" -ForegroundColor Gray
        Start-Sleep -Seconds 30
    }
}

# 主逻辑
Write-Log "上传性能管理器启动" "INFO"

if ($Stop) {
    Stop-AllUploaders
} elseif ($Install) {
    Install-PerformanceSystem
} elseif ($Monitor) {
    Start-PerformanceMonitoring
} elseif ($Status) {
    Show-CurrentStatus
} else {
    Write-Host "🚀 上传性能管理器" -ForegroundColor Cyan
    Write-Host "================" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "📋 可用模式:" -ForegroundColor Yellow
    foreach ($mode in $PerformanceModes.Keys) {
        $config = $PerformanceModes[$mode]
        Write-Host "  $mode : $($config.Description)" -ForegroundColor White
        Write-Host "          并发=$($config.Concurrent), 间隔=$($config.Interval)s" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "🛠️  使用方法:" -ForegroundColor Yellow
    Write-Host "  安装系统: .\scripts\upload_performance_manager.ps1 -Install -Mode HighPerf" -ForegroundColor White
    Write-Host "  查看状态: .\scripts\upload_performance_manager.ps1 -Status" -ForegroundColor White
    Write-Host "  实时监控: .\scripts\upload_performance_manager.ps1 -Monitor" -ForegroundColor White
    Write-Host "  停止所有: .\scripts\upload_performance_manager.ps1 -Stop" -ForegroundColor White
    Write-Host "  智能模式: .\scripts\upload_performance_manager.ps1 -Install -Mode Auto" -ForegroundColor White
    Write-Host ""
}