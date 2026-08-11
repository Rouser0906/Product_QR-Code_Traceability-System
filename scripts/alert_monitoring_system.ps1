#!/usr/bin/env powershell
# 自动同步系统告警监控 - 当性能异常时自动通知
param(
    [string]$AlertConfig = "auto_sync/alert_config.json",
    [switch]$TestAlerts = $false,
    [switch]$InstallService = $false,
    [switch]$CheckStatus = $false,
    [switch]$Debug = $false
)

$ErrorActionPreference = 'Continue'

# 获取项目根目录
try {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
    Set-Location $ProjectRoot
} catch {
    $ProjectRoot = (Get-Location).Path
}

$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
$alertLogFile = Join-Path $logDir 'alert_monitor.log'
$alertHistoryFile = Join-Path $logDir 'alert_history.json'

# 确保日志目录存在
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-AlertLog($msg, $level = "INFO", $alertType = "") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $logMsg = "$ts [$level] ALERT: $msg"
    
    # 写入日志文件
    $logMsg | Out-File -FilePath $alertLogFile -Encoding utf8 -Append
    
    # 控制台输出
    if ($Debug -or $level -eq "ALERT" -or $level -eq "ERROR") {
        $color = switch($level) {
            "ERROR" { "Red" }
            "ALERT" { "Magenta" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "Cyan" }
        }
        Write-Host $logMsg -ForegroundColor $color
    }
    
    # 记录告警历史
    if ($level -eq "ALERT" -and $alertType) {
        Record-AlertHistory $alertType $msg
    }
}

function Load-AlertConfig {
    try {
        $configPath = Join-Path $ProjectRoot $AlertConfig
        if (-not (Test-Path $configPath)) {
            Write-AlertLog "告警配置文件不存在，使用默认配置: $configPath" "WARN"
            return Get-DefaultAlertConfig
        }
        
        $config = Get-Content $configPath -Raw | ConvertFrom-Json
        Write-AlertLog "已加载告警配置: $configPath" "INFO"
        return $config
    } catch {
        Write-AlertLog "加载告警配置失败，使用默认配置: $($_.Exception.Message)" "ERROR"
        return Get-DefaultAlertConfig
    }
}

function Get-DefaultAlertConfig {
    return @{
        enabled = $true
        check_interval_seconds = 60
        alerts = @{
            process_down = @{
                enabled = $true
                severity = "high"
                description = "上传进程停止运行"
                threshold = 0
                notification_methods = @("system_event", "sound", "log")
            }
            log_stale = @{
                enabled = $true
                severity = "medium"
                description = "日志文件长时间无更新"
                threshold_minutes = 10
                notification_methods = @("system_event", "log")
            }
            upload_failure_rate = @{
                enabled = $true
                severity = "medium"
                description = "上传失败率过高"
                threshold_percent = 20
                sample_size = 20
                notification_methods = @("system_event", "sound")
            }
            disk_space_low = @{
                enabled = $true
                severity = "high"
                description = "磁盘空间不足"
                threshold_gb = 1
                notification_methods = @("system_event", "sound", "log")
            }
            cpu_high = @{
                enabled = $true
                severity = "low"
                description = "CPU使用率过高"
                threshold_percent = 85
                duration_seconds = 300
                notification_methods = @("log")
            }
            memory_high = @{
                enabled = $true
                severity = "medium"
                description = "内存使用率过高"
                threshold_percent = 90
                duration_seconds = 180
                notification_methods = @("system_event", "log")
            }
            ftp_connectivity = @{
                enabled = $true
                severity = "high"
                description = "FTP服务器连接失败"
                retry_attempts = 3
                notification_methods = @("system_event", "sound")
            }
            file_queue_overflow = @{
                enabled = $true
                severity = "medium"
                description = "待上传文件队列过长"
                threshold_count = 100
                notification_methods = @("system_event")
            }
        }
        notification_settings = @{
            system_event = @{
                source = "AutoSyncMonitor"
                event_id_base = 1000
            }
            sound = @{
                enabled = $true
                frequency = 1000
                duration_ms = 500
                repeat_count = 2
            }
            email = @{
                enabled = $false
                smtp_server = ""
                smtp_port = 587
                from_address = ""
                to_addresses = @()
                subject_prefix = "[AutoSync Alert]"
            }
            webhook = @{
                enabled = $false
                url = ""
                method = "POST"
                headers = @{}
            }
        }
        rate_limiting = @{
            same_alert_cooldown_minutes = 10
            max_alerts_per_hour = 20
        }
    }
}

function Record-AlertHistory($alertType, $message) {
    try {
        $history = @()
        if (Test-Path $alertHistoryFile) {
            $history = Get-Content $alertHistoryFile -Raw | ConvertFrom-Json
        }
        
        $newAlert = @{
            timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            type = $alertType
            message = $message
            severity = $script:alertConfig.alerts.$alertType.severity
        }
        
        $history += $newAlert
        
        # 保留最近100条记录
        if ($history.Count -gt 100) {
            $history = $history | Select-Object -Last 100
        }
        
        $history | ConvertTo-Json -Depth 3 | Out-File -FilePath $alertHistoryFile -Encoding utf8
    } catch {
        Write-AlertLog "记录告警历史失败: $($_.Exception.Message)" "ERROR"
    }
}

function Test-ProcessAlert {
    $config = $script:alertConfig.alerts.process_down
    if (-not $config.enabled) { return $false }
    
    try {
        $processes = Get-CimInstance Win32_Process | Where-Object { 
            $_.CommandLine -like "*windows_ftp_json_uploader*" -or
            $_.CommandLine -like "*high_performance_uploader*"
        }
        
        $processCount = $processes.Count
        if ($processCount -le $config.threshold) {
            $message = "上传进程数量异常: $processCount 个进程运行"
            Send-Alert "process_down" $message $config
            return $true
        }
        
        return $false
    } catch {
        Write-AlertLog "检查进程状态失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-LogStaleAlert {
    $config = $script:alertConfig.alerts.log_stale
    if (-not $config.enabled) { return $false }
    
    try {
        $logFiles = @("ftp_uploader.log", "high_perf_uploader.log", "enhanced_uploader.log")
        $anyActive = $false
        
        foreach ($logFile in $logFiles) {
            $logPath = Join-Path $logDir $logFile
            if (Test-Path $logPath) {
                $lastWrite = (Get-Item $logPath).LastWriteTime
                $age = ((Get-Date) - $lastWrite).TotalMinutes
                
                if ($age -le $config.threshold_minutes) {
                    $anyActive = $true
                    break
                }
            }
        }
        
        if (-not $anyActive) {
            $message = "日志文件超过 $($config.threshold_minutes) 分钟无更新"
            Send-Alert "log_stale" $message $config
            return $true
        }
        
        return $false
    } catch {
        Write-AlertLog "检查日志状态失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-UploadFailureRateAlert {
    $config = $script:alertConfig.alerts.upload_failure_rate
    if (-not $config.enabled) { return $false }
    
    try {
        $logFiles = @("ftp_uploader.log", "high_perf_uploader.log", "enhanced_uploader.log")
        $totalUploads = 0
        $failedUploads = 0
        
        foreach ($logFile in $logFiles) {
            $logPath = Join-Path $logDir $logFile
            if (Test-Path $logPath) {
                $recentLogs = Get-Content $logPath -Tail $config.sample_size -ErrorAction SilentlyContinue
                foreach ($line in $recentLogs) {
                    if ($line -match "UPLOAD OK|UPLOAD FAIL|上传成功|上传失败") {
                        $totalUploads++
                        if ($line -match "UPLOAD FAIL|上传失败") {
                            $failedUploads++
                        }
                    }
                }
            }
        }
        
        if ($totalUploads -gt 0) {
            $failureRate = ($failedUploads / $totalUploads) * 100
            if ($failureRate -gt $config.threshold_percent) {
                $message = "上传失败率过高: $([math]::Round($failureRate, 1))% ($failedUploads/$totalUploads)"
                Send-Alert "upload_failure_rate" $message $config
                return $true
            }
        }
        
        return $false
    } catch {
        Write-AlertLog "检查上传失败率失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-DiskSpaceAlert {
    $config = $script:alertConfig.alerts.disk_space_low
    if (-not $config.enabled) { return $false }
    
    try {
        $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        
        if ($freeSpaceGB -lt $config.threshold_gb) {
            $message = "磁盘空间不足: 剩余 ${freeSpaceGB}GB (阈值: $($config.threshold_gb)GB)"
            Send-Alert "disk_space_low" $message $config
            return $true
        }
        
        return $false
    } catch {
        Write-AlertLog "检查磁盘空间失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-FtpConnectivityAlert {
    $config = $script:alertConfig.alerts.ftp_connectivity
    if (-not $config.enabled) { return $false }
    
    $attempt = 0
    while ($attempt -lt $config.retry_attempts) {
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
            
            # 连接成功
            return $false
        } catch {
            $attempt++
            if ($attempt -lt $config.retry_attempts) {
                Start-Sleep -Seconds 2
            }
        }
    }
    
    # 所有重试都失败
    $message = "FTP服务器连接失败: 尝试 $($config.retry_attempts) 次均失败"
    Send-Alert "ftp_connectivity" $message $config
    return $true
}

function Test-FileQueueAlert {
    $config = $script:alertConfig.alerts.file_queue_overflow
    if (-not $config.enabled) { return $false }
    
    try {
        $aCount = if (Test-Path "cloud\demo_json_a") { 
            (Get-ChildItem "cloud\demo_json_a" -Filter "*.json" | Where-Object { 
                $_.LastWriteTime -gt (Get-Date).AddHours(-2) 
            }).Count 
        } else { 0 }
        
        $zyCount = if (Test-Path "cloud\demo_json_b") { 
            (Get-ChildItem "cloud\demo_json_b" -Filter "*.json" | Where-Object { 
                $_.LastWriteTime -gt (Get-Date).AddHours(-2) 
            }).Count 
        } else { 0 }
        
        $totalQueue = $aCount + $zyCount
        
        if ($totalQueue -gt $config.threshold_count) {
            $message = "待上传文件队列过长: $totalQueue 个文件 (A:$aCount, B:$zyCount)"
            Send-Alert "file_queue_overflow" $message $config
            return $true
        }
        
        return $false
    } catch {
        Write-AlertLog "检查文件队列失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Send-Alert($alertType, $message, $config) {
    # 检查速率限制
    if (-not (Check-RateLimit $alertType)) {
        Write-AlertLog "告警被速率限制跳过: $alertType" "INFO"
        return
    }
    
    Write-AlertLog $message "ALERT" $alertType
    
    # 执行各种通知方法
    foreach ($method in $config.notification_methods) {
        try {
            switch ($method) {
                "system_event" { Send-SystemEvent $alertType $message $config.severity }
                "sound" { Send-SoundAlert }
                "email" { Send-EmailAlert $alertType $message $config.severity }
                "webhook" { Send-WebhookAlert $alertType $message $config.severity }
                "log" { 
                    # 已经记录到日志了
                }
            }
        } catch {
            Write-AlertLog "发送告警失败 ($method): $($_.Exception.Message)" "ERROR"
        }
    }
    
    # 更新速率限制记录
    Update-RateLimit $alertType
}

function Check-RateLimit($alertType) {
    try {
        $rateLimitFile = Join-Path $logDir "rate_limit.json"
        $now = Get-Date
        $cooldownMinutes = $script:alertConfig.rate_limiting.same_alert_cooldown_minutes
        
        if (-not (Test-Path $rateLimitFile)) {
            return $true
        }
        
        $rateLimitData = Get-Content $rateLimitFile -Raw | ConvertFrom-Json
        
        # 检查同类告警冷却时间
        if ($rateLimitData.$alertType) {
            $lastAlert = [DateTime]::Parse($rateLimitData.$alertType.last_sent)
            $timeSince = ($now - $lastAlert).TotalMinutes
            
            if ($timeSince -lt $cooldownMinutes) {
                return $false
            }
        }
        
        # 检查每小时告警总数
        $hourlyCount = 0
        foreach ($type in $rateLimitData.PSObject.Properties.Name) {
            if ($rateLimitData.$type.last_sent) {
                $lastSent = [DateTime]::Parse($rateLimitData.$type.last_sent)
                if (($now - $lastSent).TotalHours -lt 1) {
                    $hourlyCount++
                }
            }
        }
        
        $maxPerHour = $script:alertConfig.rate_limiting.max_alerts_per_hour
        if ($hourlyCount -ge $maxPerHour) {
            return $false
        }
        
        return $true
    } catch {
        Write-AlertLog "检查速率限制失败: $($_.Exception.Message)" "ERROR"
        return $true  # 失败时允许发送
    }
}

function Update-RateLimit($alertType) {
    try {
        $rateLimitFile = Join-Path $logDir "rate_limit.json"
        $rateLimitData = @{}
        
        if (Test-Path $rateLimitFile) {
            $rateLimitData = Get-Content $rateLimitFile -Raw | ConvertFrom-Json -AsHashtable
        }
        
        $rateLimitData[$alertType] = @{
            last_sent = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        }
        
        $rateLimitData | ConvertTo-Json | Out-File -FilePath $rateLimitFile -Encoding utf8
    } catch {
        Write-AlertLog "更新速率限制失败: $($_.Exception.Message)" "ERROR"
    }
}

function Send-SystemEvent($alertType, $message, $severity) {
    try {
        $eventSource = $script:alertConfig.notification_settings.system_event.source
        $eventId = $script:alertConfig.notification_settings.system_event.event_id_base + 
                   (@("low", "medium", "high").IndexOf($severity) + 1)
        
        # 创建事件源（如果不存在）
        if (-not [System.Diagnostics.EventLog]::SourceExists($eventSource)) {
            [System.Diagnostics.EventLog]::CreateEventSource($eventSource, "Application")
        }
        
        $entryType = switch ($severity) {
            "high" { "Error" }
            "medium" { "Warning" }
            default { "Information" }
        }
        
        Write-EventLog -LogName Application -Source $eventSource -EventId $eventId -EntryType $entryType -Message "[$alertType] $message"
        Write-AlertLog "已发送系统事件: EventId=$eventId, Type=$entryType" "INFO"
    } catch {
        Write-AlertLog "发送系统事件失败: $($_.Exception.Message)" "ERROR"
    }
}

function Send-SoundAlert {
    try {
        $soundConfig = $script:alertConfig.notification_settings.sound
        if ($soundConfig.enabled) {
            for ($i = 0; $i -lt $soundConfig.repeat_count; $i++) {
                [Console]::Beep($soundConfig.frequency, $soundConfig.duration_ms)
                if ($i -lt $soundConfig.repeat_count - 1) {
                    Start-Sleep -Milliseconds 200
                }
            }
            Write-AlertLog "已发送声音告警" "INFO"
        }
    } catch {
        Write-AlertLog "发送声音告警失败: $($_.Exception.Message)" "ERROR"
    }
}

function Send-EmailAlert($alertType, $message, $severity) {
    try {
        $emailConfig = $script:alertConfig.notification_settings.email
        if (-not $emailConfig.enabled -or -not $emailConfig.smtp_server) {
            return
        }
        
        $subject = "$($emailConfig.subject_prefix) [$severity] $alertType"
        $body = @"
告警类型: $alertType
告警级别: $severity
告警时间: $(Get-Date)
告警信息: $message

系统信息:
- 计算机名: $env:COMPUTERNAME
- 用户名: $env:USERNAME
- 项目路径: $ProjectRoot
"@
        
        $smtpClient = New-Object System.Net.Mail.SmtpClient($emailConfig.smtp_server, $emailConfig.smtp_port)
        $smtpClient.EnableSsl = $true
        
        foreach ($toAddress in $emailConfig.to_addresses) {
            $mailMessage = New-Object System.Net.Mail.MailMessage($emailConfig.from_address, $toAddress, $subject, $body)
            $smtpClient.Send($mailMessage)
            $mailMessage.Dispose()
        }
        
        $smtpClient.Dispose()
        Write-AlertLog "已发送邮件告警到 $($emailConfig.to_addresses.Count) 个地址" "INFO"
    } catch {
        Write-AlertLog "发送邮件告警失败: $($_.Exception.Message)" "ERROR"
    }
}

function Send-WebhookAlert($alertType, $message, $severity) {
    try {
        $webhookConfig = $script:alertConfig.notification_settings.webhook
        if (-not $webhookConfig.enabled -or -not $webhookConfig.url) {
            return
        }
        
        $payload = @{
            alert_type = $alertType
            severity = $severity
            message = $message
            timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            hostname = $env:COMPUTERNAME
            project_path = $ProjectRoot
        } | ConvertTo-Json
        
        $headers = @{ "Content-Type" = "application/json" }
        foreach ($key in $webhookConfig.headers.PSObject.Properties.Name) {
            $headers[$key] = $webhookConfig.headers.$key
        }
        
        Invoke-RestMethod -Uri $webhookConfig.url -Method $webhookConfig.method -Body $payload -Headers $headers -TimeoutSec 10
        Write-AlertLog "已发送Webhook告警到 $($webhookConfig.url)" "INFO"
    } catch {
        Write-AlertLog "发送Webhook告警失败: $($_.Exception.Message)" "ERROR"
    }
}

function Run-MonitoringLoop {
    Write-AlertLog "告警监控系统启动" "INFO"
    
    $checkCount = 0
    while ($true) {
        $checkCount++
        $checkStart = Get-Date
        
        Write-AlertLog "开始第 $checkCount 次监控检查" "INFO"
        
        try {
            # 执行所有告警检查
            $alertsTriggered = 0
            
            if (Test-ProcessAlert) { $alertsTriggered++ }
            if (Test-LogStaleAlert) { $alertsTriggered++ }
            if (Test-UploadFailureRateAlert) { $alertsTriggered++ }
            if (Test-DiskSpaceAlert) { $alertsTriggered++ }
            if (Test-FtpConnectivityAlert) { $alertsTriggered++ }
            if (Test-FileQueueAlert) { $alertsTriggered++ }
            
            $checkDuration = ((Get-Date) - $checkStart).TotalSeconds
            
            if ($alertsTriggered -eq 0) {
                Write-AlertLog "第 $checkCount 次检查完成，系统正常 (耗时: $([math]::Round($checkDuration, 2))s)" "INFO"
            } else {
                Write-AlertLog "第 $checkCount 次检查完成，触发 $alertsTriggered 个告警 (耗时: $([math]::Round($checkDuration, 2))s)" "WARN"
            }
            
        } catch {
            Write-AlertLog "监控检查异常: $($_.Exception.Message)" "ERROR"
        }
        
        # 等待下次检查
        Start-Sleep -Seconds $script:alertConfig.check_interval_seconds
    }
}

function Test-AllAlerts {
    Write-AlertLog "开始告警系统测试..." "INFO"
    
    # 测试系统事件
    Send-SystemEvent "test_alert" "这是一个测试告警" "medium"
    
    # 测试声音告警
    Send-SoundAlert
    
    # 测试所有检查功能
    Write-AlertLog "测试进程检查..." "INFO"
    Test-ProcessAlert | Out-Null
    
    Write-AlertLog "测试日志检查..." "INFO"
    Test-LogStaleAlert | Out-Null
    
    Write-AlertLog "测试磁盘空间检查..." "INFO"
    Test-DiskSpaceAlert | Out-Null
    
    Write-AlertLog "测试FTP连接检查..." "INFO"
    Test-FtpConnectivityAlert | Out-Null
    
    Write-AlertLog "告警系统测试完成" "SUCCESS"
}

function Show-AlertStatus {
    Write-Host "🔔 告警监控系统状态" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor DarkGray
    
    # 检查监控任务
    $alertTask = schtasks /query /tn "AlertMonitor" 2>$null
    $taskStatus = if ($LASTEXITCODE -eq 0) { "运行中" } else { "未安装" }
    Write-Host "📋 监控任务: $taskStatus" -ForegroundColor $(if($LASTEXITCODE -eq 0){'Green'}else{'Red'})
    
    # 检查告警历史
    if (Test-Path $alertHistoryFile) {
        try {
            $history = Get-Content $alertHistoryFile -Raw | ConvertFrom-Json
            $recentAlerts = $history | Where-Object { 
                ([DateTime]::Parse($_.timestamp) -gt (Get-Date).AddHours(-24)) 
            }
            Write-Host "📊 最近24小时告警: $($recentAlerts.Count) 次" -ForegroundColor $(if($recentAlerts.Count -eq 0){'Green'}elseif($recentAlerts.Count -lt 5){'Yellow'}else{'Red'})
            
            if ($recentAlerts.Count -gt 0) {
                Write-Host "🔍 最近告警:" -ForegroundColor Yellow
                $recentAlerts | Select-Object -Last 3 | ForEach-Object {
                    $color = switch($_.severity) {
                        "high" { "Red" }
                        "medium" { "Yellow" }
                        default { "White" }
                    }
                    Write-Host "  $($_.timestamp) [$($_.severity)] $($_.type): $($_.message)" -ForegroundColor $color
                }
            }
        } catch {
            Write-Host "⚠️  告警历史读取失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "📊 告警历史: 无记录" -ForegroundColor Gray
    }
    
    # 检查配置状态
    $configLoaded = $script:alertConfig -ne $null
    Write-Host "⚙️  配置状态: $(if($configLoaded){'已加载'}else{'未加载'})" -ForegroundColor $(if($configLoaded){'Green'}else{'Red'})
    
    if ($configLoaded) {
        $enabledAlerts = ($script:alertConfig.alerts.PSObject.Properties | Where-Object { $_.Value.enabled }).Count
        $totalAlerts = $script:alertConfig.alerts.PSObject.Properties.Count
        Write-Host "🎯 启用告警: $enabledAlerts/$totalAlerts 种" -ForegroundColor Green
    }
}

function Install-AlertService {
    Write-AlertLog "安装告警监控服务..." "INFO"
    
    # 创建监控任务
    $scriptPath = Join-Path $ProjectRoot $MyInvocation.MyCommand.Definition
    $taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""
    
    # 删除旧任务
    schtasks /delete /tn "AlertMonitor" /f 2>$null | Out-Null
    
    # 创建新任务
    $result = schtasks /create /tn "AlertMonitor" /sc minute /mo 1 /tr "$taskCommand" /ru "SYSTEM" /rl HIGHEST /f
    
    if ($LASTEXITCODE -eq 0) {
        Write-AlertLog "告警监控任务创建成功" "SUCCESS"
        
        # 启动任务
        schtasks /run /tn "AlertMonitor" | Out-Null
        Write-AlertLog "告警监控任务已启动" "SUCCESS"
        
        # 发送测试告警
        Send-SystemEvent "service_installed" "告警监控服务已安装并启动" "low"
        
        return $true
    } else {
        Write-AlertLog "告警监控任务创建失败" "ERROR"
        return $false
    }
}

# 主程序逻辑
$script:alertConfig = Load-AlertConfig

if ($InstallService) {
    Install-AlertService
} elseif ($TestAlerts) {
    Test-AllAlerts
} elseif ($CheckStatus) {
    Show-AlertStatus
} else {
    # 默认运行监控循环
    if ($script:alertConfig.enabled) {
        Run-MonitoringLoop
    } else {
        Write-AlertLog "告警监控已禁用" "INFO"
    }
}