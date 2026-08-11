#!/usr/bin/env powershell
# 自动同步系统故障恢复工具
param(
    [switch]$ForceReset = $false,
    [switch]$CleanLogs = $false,
    [switch]$TestMode = $false,
    [switch]$Verbose = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

function Write-Log($message, $level = "INFO") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$level] $message"
    
    $color = switch ($level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        "INFO" { "Cyan" }
        default { "White" }
    }
    
    Write-Host $logMessage -ForegroundColor $color
    
    # 写入恢复日志
    $recoveryLog = Join-Path $logDir "recovery.log"
    $logMessage | Out-File -FilePath $recoveryLog -Encoding utf8 -Append -ErrorAction SilentlyContinue
}

function Test-SystemHealth {
    Write-Log "开始系统健康检查..." "INFO"
    $issues = @()
    
    # 1. 检查关键目录
    $criticalDirs = @(
        "cloud\demo_json_a",
        "cloud\demo_json_b", 
        "auto_sync\logs",
        "scripts"
    )
    
    foreach ($dir in $criticalDirs) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (-not (Test-Path $fullPath)) {
            $issues += "关键目录缺失: $dir"
            try {
                New-Item -ItemType Directory -Force -Path $fullPath | Out-Null
                Write-Log "已创建缺失目录: $dir" "SUCCESS"
            } catch {
                Write-Log "创建目录失败: $dir - $($_.Exception.Message)" "ERROR"
            }
        }
    }
    
    # 2. 检查关键文件
    $criticalFiles = @(
        "scripts\enhanced_ftp_uploader.ps1",
        "scripts\enhanced_sync_guardian.ps1",
        "auto_sync\enhanced_config.json"
    )
    
    foreach ($file in $criticalFiles) {
        $fullPath = Join-Path $ProjectRoot $file
        if (-not (Test-Path $fullPath)) {
            $issues += "关键文件缺失: $file"
        }
    }
    
    # 3. 检查磁盘空间
    try {
        $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        if ($freeSpaceGB -lt 1) {
            $issues += "磁盘空间不足: ${freeSpaceGB}GB"
        } else {
            Write-Log "磁盘空间充足: ${freeSpaceGB}GB" "SUCCESS"
        }
    } catch {
        $issues += "无法检查磁盘空间"
    }
    
    # 4. 检查网络连接
    try {
        $result = Test-NetConnection -ComputerName "scan.example.com" -Port 21 -InformationLevel Quiet -WarningAction SilentlyContinue
        if (-not $result) {
            $issues += "FTP服务器连接失败"
        } else {
            Write-Log "FTP服务器连接正常" "SUCCESS"
        }
    } catch {
        $issues += "网络连接检查失败"
    }
    
    # 5. 检查计划任务
    $tasks = @("EnhancedFTPUploader", "SyncGuardian")
    foreach ($taskName in $tasks) {
        try {
            $task = schtasks /query /tn "$taskName" 2>$null
            if ($LASTEXITCODE -ne 0) {
                $issues += "计划任务缺失: $taskName"
            } else {
                Write-Log "计划任务正常: $taskName" "SUCCESS"
            }
        } catch {
            $issues += "无法检查计划任务: $taskName"
        }
    }
    
    return $issues
}

function Stop-AllSyncProcesses {
    Write-Log "停止所有同步相关进程..." "INFO"
    
    # 停止上传进程
    try {
        $uploaderProcs = Get-CimInstance Win32_Process | Where-Object { 
            $_.CommandLine -like "*enhanced_ftp_uploader*" -or 
            $_.CommandLine -like "*windows_ftp_json_uploader*"
        }
        
        foreach ($proc in $uploaderProcs) {
            try {
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Log "已停止上传进程: PID $($proc.ProcessId)" "SUCCESS"
            } catch {
                Write-Log "停止进程失败: PID $($proc.ProcessId)" "WARN"
            }
        }
    } catch {
        Write-Log "查询上传进程失败: $($_.Exception.Message)" "ERROR"
    }
    
    # 停止守护进程
    try {
        $guardianProcs = Get-CimInstance Win32_Process | Where-Object { 
            $_.CommandLine -like "*enhanced_sync_guardian*" -or
            $_.CommandLine -like "*guard_ftp_uploader*"
        }
        
        foreach ($proc in $guardianProcs) {
            try {
                Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
                Write-Log "已停止守护进程: PID $($proc.ProcessId)" "SUCCESS"
            } catch {
                Write-Log "停止守护进程失败: PID $($proc.ProcessId)" "WARN"
            }
        }
    } catch {
        Write-Log "查询守护进程失败: $($_.Exception.Message)" "ERROR"
    }
    
    # 等待进程完全退出
    Start-Sleep -Seconds 3
}

function Clean-LogFiles {
    if (-not $CleanLogs) { return }
    
    Write-Log "清理日志文件..." "INFO"
    
    $logFiles = Get-ChildItem -Path $logDir -Filter "*.log" -ErrorAction SilentlyContinue
    foreach ($logFile in $logFiles) {
        try {
            # 保留最近1000行
            $content = Get-Content $logFile.FullName -Tail 1000 -ErrorAction SilentlyContinue
            if ($content) {
                $content | Out-File -FilePath $logFile.FullName -Encoding utf8
                Write-Log "已清理日志文件: $($logFile.Name)" "SUCCESS"
            }
        } catch {
            Write-Log "清理日志文件失败: $($logFile.Name)" "WARN"
        }
    }
    
    # 清理状态文件
    $statusFiles = @("sync_status.json", "sync_metrics.json")
    foreach ($file in $statusFiles) {
        $fullPath = Join-Path $logDir $file
        if (Test-Path $fullPath) {
            try {
                Remove-Item $fullPath -Force
                Write-Log "已清理状态文件: $file" "SUCCESS"
            } catch {
                Write-Log "清理状态文件失败: $file" "WARN"
            }
        }
    }
}

function Repair-ScheduledTasks {
    Write-Log "修复计划任务..." "INFO"
    
    if ($ForceReset) {
        # 删除所有相关的旧任务
        $oldTasks = @("EnhancedFTPUploader", "SyncGuardian", "QRJsonAutoSync", "FTP_JSON_Uploader_Guard")
        foreach ($taskName in $oldTasks) {
            try {
                schtasks /delete /tn "$taskName" /f 2>$null | Out-Null
                Write-Log "已删除旧任务: $taskName" "INFO"
            } catch {
                # 忽略不存在的任务
            }
        }
    }
    
    # 重新创建任务
    try {
        & (Join-Path $ProjectRoot "scripts\setup_enhanced_sync.ps1") -Force
        Write-Log "计划任务修复完成" "SUCCESS"
    } catch {
        Write-Log "计划任务修复失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
    
    return $true
}

function Test-Upload {
    Write-Log "测试文件上传功能..." "INFO"
    
    try {
        # 创建测试文件
        $testFile = Join-Path $logDir "upload_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        $testContent = @{
            test = $true
            timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            pid = $PID
        } | ConvertTo-Json
        
        $testContent | Out-File -FilePath $testFile -Encoding utf8
        
        # 运行单次上传测试
        $testScript = Join-Path $ProjectRoot "scripts\enhanced_ftp_uploader.ps1"
        if (Test-Path $testScript) {
            & $testScript -Once -Debug
            Write-Log "上传测试完成" "SUCCESS"
        } else {
            Write-Log "上传脚本不存在" "ERROR"
            return $false
        }
        
        # 清理测试文件
        if (Test-Path $testFile) {
            Remove-Item $testFile -Force -ErrorAction SilentlyContinue
        }
        
        return $true
    } catch {
        Write-Log "上传测试失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-RecoveryReport($issues, $success) {
    Write-Host ""
    Write-Host "🔧 自动同步系统恢复报告" -ForegroundColor Cyan
    Write-Host "=" * 50 -ForegroundColor DarkGray
    
    if ($issues.Count -eq 0) {
        Write-Host "✅ 系统健康，无需修复" -ForegroundColor Green
    } else {
        Write-Host "⚠️  发现的问题:" -ForegroundColor Yellow
        foreach ($issue in $issues) {
            Write-Host "  • $issue" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "🔨 执行的修复操作:" -ForegroundColor Yellow
    Write-Host "  • 停止所有同步进程: ✅" -ForegroundColor Green
    
    if ($CleanLogs) {
        Write-Host "  • 清理日志文件: ✅" -ForegroundColor Green
    }
    
    if ($ForceReset -or $issues.Count -gt 0) {
        Write-Host "  • 修复计划任务: $(if($success){'✅'}else{'❌'})" -ForegroundColor $(if($success){'Green'}else{'Red'})
    }
    
    if ($TestMode) {
        Write-Host "  • 上传功能测试: $(if($success){'✅'}else{'❌'})" -ForegroundColor $(if($success){'Green'}else{'Red'})
    }
    
    Write-Host ""
    Write-Host "📋 后续建议:" -ForegroundColor Yellow
    Write-Host "  • 运行监控面板: .\scripts\sync_monitor.ps1" -ForegroundColor White
    Write-Host "  • 查看实时日志: Get-Content auto_sync\logs\enhanced_uploader.log -Wait" -ForegroundColor White
    Write-Host "  • 检查计划任务: schtasks /query /tn EnhancedFTPUploader" -ForegroundColor White
    Write-Host ""
}

# 主恢复流程
Write-Log "启动自动同步系统故障恢复工具" "INFO"
Write-Log "参数: ForceReset=$ForceReset, CleanLogs=$CleanLogs, TestMode=$TestMode" "INFO"

# 1. 系统健康检查
$healthIssues = Test-SystemHealth

# 2. 停止所有相关进程
Stop-AllSyncProcesses

# 3. 清理日志（如果请求）
Clean-LogFiles

# 4. 修复计划任务（如果有问题或强制重置）
$taskRepairSuccess = $true
if ($ForceReset -or ($healthIssues | Where-Object { $_ -like "*计划任务*" })) {
    $taskRepairSuccess = Repair-ScheduledTasks
}

# 5. 测试上传功能（如果请求）
$uploadTestSuccess = $true
if ($TestMode) {
    $uploadTestSuccess = Test-Upload
}

# 6. 显示恢复报告
Show-RecoveryReport $healthIssues ($taskRepairSuccess -and $uploadTestSuccess)

Write-Log "故障恢复工具执行完成" "INFO"