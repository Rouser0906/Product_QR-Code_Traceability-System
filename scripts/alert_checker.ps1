# 简单告警检查器
param([switch]$CheckAll, [switch]$SendTest)

$ProjectRoot = $PWD.Path

function Check-SystemHealth {
    Write-Host "检查系统健康状态..." -ForegroundColor Cyan
    
    $alerts = @()
    
    # 1. 检查上传进程
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*windows_ftp_json_uploader*" }
    if ($procs.Count -eq 0) {
        $alerts += "CRITICAL: 上传进程停止运行"
        Write-Host "❌ 上传进程: 停止" -ForegroundColor Red
    } else {
        Write-Host "✅ 上传进程: $($procs.Count) 个运行中" -ForegroundColor Green
    }
    
    # 2. 检查日志活跃度
    $logFile = "auto_sync\logs\ftp_uploader.log"
    if (Test-Path $logFile) {
        $lastWrite = (Get-Item $logFile).LastWriteTime
        $age = ((Get-Date) - $lastWrite).TotalMinutes
        if ($age -gt 15) {
            $alerts += "WARNING: 日志文件 $([math]::Round($age, 1)) 分钟无更新"
            Write-Host "⚠️  日志活跃度: $([math]::Round($age, 1)) 分钟前" -ForegroundColor Yellow
        } else {
            Write-Host "✅ 日志活跃度: $([math]::Round($age, 1)) 分钟前" -ForegroundColor Green
        }
    } else {
        $alerts += "ERROR: 日志文件不存在"
        Write-Host "❌ 日志文件: 不存在" -ForegroundColor Red
    }
    
    # 3. 检查磁盘空间
    try {
        $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
        $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
        if ($freeSpaceGB -lt 2) {
            $alerts += "CRITICAL: 磁盘空间不足 ${freeSpaceGB}GB"
            Write-Host "❌ 磁盘空间: ${freeSpaceGB}GB (不足)" -ForegroundColor Red
        } else {
            Write-Host "✅ 磁盘空间: ${freeSpaceGB}GB" -ForegroundColor Green
        }
    } catch {
        $alerts += "ERROR: 无法检查磁盘空间"
        Write-Host "❌ 磁盘空间: 检查失败" -ForegroundColor Red
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
        Write-Host "✅ FTP连接: 正常" -ForegroundColor Green
    } catch {
        $alerts += "CRITICAL: FTP服务器连接失败"
        Write-Host "❌ FTP连接: 失败" -ForegroundColor Red
    }
    
    # 5. 检查文件队列
    $aCount = if (Test-Path "cloud\demo_json_a") { (Get-ChildItem "cloud\demo_json_a" -Filter "*.json").Count } else { 0 }
    $zyCount = if (Test-Path "cloud\demo_json_b") { (Get-ChildItem "cloud\demo_json_b" -Filter "*.json").Count } else { 0 }
    $totalQueue = $aCount + $zyCount
    
    if ($totalQueue -gt 200) {
        $alerts += "WARNING: 文件队列过长 $totalQueue 个文件"
        Write-Host "⚠️  文件队列: $totalQueue 个 (过多)" -ForegroundColor Yellow
    } else {
        Write-Host "✅ 文件队列: $totalQueue 个" -ForegroundColor Green
    }
    
    return $alerts
}

function Send-Alert($message) {
    try {
        # 发送系统事件
        Write-EventLog -LogName Application -Source "AutoSyncAlert" -EventId 1002 -EntryType Warning -Message $message
        
        # 发送声音提醒
        [Console]::Beep(1000, 500)
        Start-Sleep -Milliseconds 200
        [Console]::Beep(1200, 300)
        
        Write-Host "🔔 已发送告警: $message" -ForegroundColor Magenta
        
        # 记录到告警日志
        $alertLog = "auto_sync\logs\alerts.log"
        "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $message" | Out-File -FilePath $alertLog -Encoding utf8 -Append
        
    } catch {
        Write-Host "❌ 发送告警失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 主逻辑
if ($SendTest) {
    Send-Alert "测试告警 - 告警系统正常工作"
} elseif ($CheckAll) {
    $alerts = Check-SystemHealth
    
    if ($alerts.Count -gt 0) {
        Write-Host ""
        Write-Host "⚠️  发现 $($alerts.Count) 个问题:" -ForegroundColor Yellow
        foreach ($alert in $alerts) {
            Send-Alert $alert
        }
    } else {
        Write-Host ""
        Write-Host "✅ 系统健康，无告警" -ForegroundColor Green
    }
} else {
    Write-Host "告警检查器" -ForegroundColor Cyan
    Write-Host "使用方法:" -ForegroundColor Yellow
    Write-Host "  -CheckAll   检查所有项目并发送告警" -ForegroundColor White
    Write-Host "  -SendTest   发送测试告警" -ForegroundColor White
}