# 简化版告警监控系统
param(
    [switch]$Install = $false,
    [switch]$Test = $false,
    [switch]$Status = $false,
    [switch]$Run = $false
)

$ProjectRoot = $PWD.Path
$logDir = Join-Path $ProjectRoot "auto_sync\logs"

function Write-AlertLog($message, $level = "INFO") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$level] $message"
    
    $color = switch ($level) {
        "ALERT" { "Magenta" }
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "Cyan" }
    }
    
    Write-Host $logMessage -ForegroundColor $color
    
    # 写入日志文件
    $alertLog = Join-Path $logDir "simple_alerts.log"
    $logMessage | Out-File -FilePath $alertLog -Encoding utf8 -Append
}

function Send-SystemAlert($alertType, $message) {
    try {
        # 创建Windows事件日志
        $eventSource = "AutoSyncAlert"
        if (-not [System.Diagnostics.EventLog]::SourceExists($eventSource)) {
            [System.Diagnostics.EventLog]::CreateEventSource($eventSource, "Application")
        }
        
        Write-EventLog -LogName Application -Source $eventSource -EventId 1001 -EntryType Warning -Message "[$alertType] $message"
        Write-AlertLog "已发送系统告警: $alertType" "SUCCESS"
    } catch {
        Write-AlertLog "发送系统告警失败: $($_.Exception.Message)" "ERROR"
    }
}

function Send-SoundAlert {
    try {
        # 发出声音告警
        [Console]::Beep(1000, 500)
        Start-Sleep -Milliseconds 200
        [Console]::Beep(1200, 300)
        Write-AlertLog "已发送声音告警" "SUCCESS"
    } catch {
        Write-AlertLog "发送声音告警失败" "WARN"
    }
}

function Test-ProcessAlert {
    $procs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -like "*windows_ftp_json_uploader*" -or
        $_.CommandLine -like "*high_performance_uploader*"
    }
    
    if ($procs.Count -eq 0) {
        $message = "上传进程停止运行，当前进程数: 0"
        Write-AlertLog $message "ALERT"
        Send-SystemAlert "ProcessDown" $message
        Send-SoundAlert
        return $true
    }
    
    return $false
}

function Test-LogAlert {
    $logFiles = @("ftp_uploader.log", "high_perf_uploader.log", "enhanced_uploader.log")
    $anyActive = $false
    
    foreach ($logFile in $logFiles) {
        $logPath = Join-Path $logDir $logFile
        if (Test-Path $logPath) {
            $lastWrite = (Get-Item $logPath).LastWriteTime
            $age = ((Get-Date) - $lastWrite).TotalMinutes
            
            if ($age -le 15) {  # 15分钟内有活动
                $anyActive = $true
                break
            }
        }
    }
    
    if (-not $anyActive) {
        $message = "所有日志文件超过15分钟无更新"
        Write-AlertLog $message "ALERT"
        Send-SystemAlert "LogStale" $message
        return $true
    }
    
    return $false
}

function Test-DiskAlert {
    try {
        $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        
        if ($freeSpaceGB -lt 2) {  # 低于2GB告警
            $message = "磁盘空间不足: 剩余 ${freeSpaceGB}GB"
            Write-AlertLog $message "ALERT"
            Send-SystemAlert "DiskLow" $message
            Send-SoundAlert
            return $true
        }
        
        return $false
    } catch {
        Write-AlertLog "检查磁盘空间失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-FtpAlert {
    try {
        $uri = "ftp://scan.example.com:21"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $req.Credentials = New-Object System.Net.NetworkCredential("your_ftp_username", "[REDACTED-FTP-PASSWORD]")
        $req.Timeout = 8000
        $req.UsePassive = $true
        $req.Proxy = $null
        
        $resp = $req.GetResponse()
        $resp.Close()
        return $false  # 连接成功
    } catch {
        $message = "FTP服务器连接失败: $($_.Exception.Message)"
        Write-AlertLog $message "ALERT"
        Send-SystemAlert "FtpDown" $message
        Send-SoundAlert
        return $true
    }
}

function Test-QueueAlert {
    $aCount = if (Test-Path "cloud\demo_json_a") { 
        (Get-ChildItem "cloud\demo_json_a" -Filter "*.json" | Where-Object { 
            $_.LastWriteTime -gt (Get-Date).AddHours(-2) 
        }).Count 
    } else { 0 }
    
    $bCount = if (Test-Path "cloud\demo_json_b") { 
        (Get-ChildItem "cloud\demo_json_b" -Filter "*.json" | Where-Object { 
            $_.LastWriteTime -gt (Get-Date).AddHours(-2) 
        }).Count 
    } else { 0 }
    
    $totalQueue = $aCount + $bCount
    
    if ($totalQueue -gt 150) {  # 超过150个文件告警
        $message = "文件队列过长: $totalQueue 个文件 (A:$aCount, B:$bCount)"
        Write-AlertLog $message "ALERT"
        Send-SystemAlert "QueueHigh" $message
        return $true
    }
    
    return $false
}

function Run-AlertMonitoring {
    Write-AlertLog "启动告警监控..." "INFO"
    
    $checkCount = 0
    while ($true) {
        $checkCount++
        Write-AlertLog "开始第 $checkCount 次监控检查" "INFO"
        
        $alertsTriggered = 0
        
        try {
            if (Test-ProcessAlert) { $alertsTriggered++ }
            if (Test-LogAlert) { $alertsTriggered++ }
            if (Test-DiskAlert) { $alertsTriggered++ }
            if (Test-FtpAlert) { $alertsTriggered++ }
            if (Test-QueueAlert) { $alertsTriggered++ }
            
            if ($alertsTriggered -eq 0) {
                Write-AlertLog "第 $checkCount 次检查完成，系统正常" "INFO"
            } else {
                Write-AlertLog "第 $checkCount 次检查完成，触发 $alertsTriggered 个告警" "WARN"
            }
        } catch {
            Write-AlertLog "监控检查异常: $($_.Exception.Message)" "ERROR"
        }
        
        # 等待60秒
        Start-Sleep -Seconds 60
    }
}

function Install-AlertService {
    Write-AlertLog "安装告警监控服务..." "INFO"
    
    # 创建监控任务
    $scriptPath = $MyInvocation.MyCommand.Definition
    $taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`" -Run"
    
    # 删除旧任务
    schtasks /delete /tn "SimpleAlertMonitor" /f 2>$null | Out-Null
    
    # 创建新任务
    $result = schtasks /create /tn "SimpleAlertMonitor" /sc minute /mo 1 /tr "$taskCommand" /ru "SYSTEM" /rl HIGHEST /f
    
    if ($LASTEXITCODE -eq 0) {
        Write-AlertLog "告警监控任务创建成功" "SUCCESS"
        schtasks /run /tn "SimpleAlertMonitor" | Out-Null
        Write-AlertLog "告警监控任务已启动" "SUCCESS"
        
        # 发送测试告警
        Send-SystemAlert "ServiceInstalled" "简单告警监控服务已安装并启动"
        return $true
    } else {
        Write-AlertLog "告警监控任务创建失败" "ERROR"
        return $false
    }
}

function Test-AllAlerts {
    Write-AlertLog "开始告警系统测试..." "INFO"
    
    # 测试系统事件
    Send-SystemAlert "TestAlert" "这是一个测试告警"
    
    # 测试声音告警
    Send-SoundAlert
    
    # 测试各种检查
    Write-AlertLog "测试进程检查..." "INFO"
    Test-ProcessAlert | Out-Null
    
    Write-AlertLog "测试日志检查..." "INFO"
    Test-LogAlert | Out-Null
    
    Write-AlertLog "测试磁盘检查..." "INFO"
    Test-DiskAlert | Out-Null
    
    Write-AlertLog "测试FTP检查..." "INFO"
    Test-FtpAlert | Out-Null
    
    Write-AlertLog "测试队列检查..." "INFO"
    Test-QueueAlert | Out-Null
    
    Write-AlertLog "告警系统测试完成" "SUCCESS"
}

function Show-AlertStatus {
    Write-Host "告警监控系统状态" -ForegroundColor Cyan
    Write-Host "=================" -ForegroundColor DarkGray
    
    # 检查监控任务
    $alertTask = schtasks /query /tn "SimpleAlertMonitor" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "监控任务: 运行中" -ForegroundColor Green
    } else {
        Write-Host "监控任务: 未安装" -ForegroundColor Red
    }
    
    # 检查告警日志
    $alertLogFile = Join-Path $logDir "simple_alerts.log"
    if (Test-Path $alertLogFile) {
        $recentAlerts = Get-Content $alertLogFile -Tail 10 | Where-Object { $_ -match "ALERT" }
        Write-Host "最近告警: $($recentAlerts.Count) 次" -ForegroundColor $(if($recentAlerts.Count -eq 0){'Green'}else{'Yellow'})
        
        if ($recentAlerts.Count -gt 0) {
            Write-Host "最新告警:" -ForegroundColor Yellow
            $recentAlerts | Select-Object -Last 3 | ForEach-Object {
                Write-Host "  $_" -ForegroundColor Red
            }
        }
    } else {
        Write-Host "告警日志: 无记录" -ForegroundColor Gray
    }
    
    # 显示系统状态
    Write-Host ""
    Write-Host "当前系统状态:" -ForegroundColor Yellow
    
    # 进程状态
    $procs = Get-CimInstance Win32_Process | Where-Object { 
        $_.CommandLine -like "*windows_ftp_json_uploader*" 
    }
    Write-Host "  上传进程: $($procs.Count) 个" -ForegroundColor $(if($procs.Count -gt 0){'Green'}else{'Red'})
    
    # 磁盘空间
    try {
        $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        Write-Host "  磁盘空间: ${freeSpaceGB}GB" -ForegroundColor $(if($freeSpaceGB -gt 2){'Green'}else{'Red'})
    } catch {
        Write-Host "  磁盘空间: 检查失败" -ForegroundColor Red
    }
    
    # 文件队列
    $aCount = if (Test-Path "cloud\demo_json_a") { (Get-ChildItem "cloud\demo_json_a" -Filter "*.json").Count } else { 0 }
    $bCount = if (Test-Path "cloud\demo_json_b") { (Get-ChildItem "cloud\demo_json_b" -Filter "*.json").Count } else { 0 }
    $totalQueue = $aCount + $bCount
    Write-Host "  文件队列: $totalQueue 个" -ForegroundColor $(if($totalQueue -lt 100){'Green'}elseif($totalQueue -lt 150){'Yellow'}else{'Red'})
}

# 主逻辑
if ($Install) {
    Install-AlertService
} elseif ($Test) {
    Test-AllAlerts
} elseif ($Status) {
    Show-AlertStatus
} elseif ($Run) {
    Run-AlertMonitoring
} else {
    Write-Host "简单告警监控系统" -ForegroundColor Cyan
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  -Install  安装告警监控服务" -ForegroundColor White
    Write-Host "  -Test     测试所有告警功能" -ForegroundColor White
    Write-Host "  -Status   查看告警系统状态" -ForegroundColor White
    Write-Host "  -Run      运行监控循环" -ForegroundColor White
}