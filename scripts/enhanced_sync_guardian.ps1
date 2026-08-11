#!/usr/bin/env powershell
# 增强版自动同步守护进程 - 提供更强的稳定性和监控能力
param(
    [int]$StaleSeconds = 120,
    [int]$MaxProcesses = 3,
    [int]$HealthCheckInterval = 30,
    [string]$ConfigFile = "auto_sync/enhanced_config.json",
    [switch]$Debug = $false
)

$ErrorActionPreference = 'Stop'

# 获取项目根目录
try {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
    Set-Location $ProjectRoot
} catch {
    $ProjectRoot = (Get-Location).Path
}

# 创建日志目录
$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$logFile = Join-Path $logDir 'sync_guardian.log'
$alertFile = Join-Path $logDir 'alerts.log'
$statusFile = Join-Path $logDir 'sync_status.json'
$metricsFile = Join-Path $logDir 'sync_metrics.json'

function Write-Log($msg, $level = "INFO") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    $logMsg = "$ts [$level] GUARDIAN: $msg"
    $logMsg | Out-File -FilePath $logFile -Encoding utf8 -Append
    if ($Debug -or $level -eq "ERROR") {
        Write-Host $logMsg -ForegroundColor $(if($level -eq "ERROR"){"Red"}elseif($level -eq "WARN"){"Yellow"}else{"Green"})
    }
}

function Write-Alert($msg) {
    try {
        $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        "$ts ALERT: $msg" | Out-File -FilePath $alertFile -Encoding utf8 -Append
        Write-Log $msg "ERROR"
        # 可选声音提醒
        try { [Console]::Beep(1000, 500) } catch {}
    } catch {}
}

function Get-UploaderProcesses() {
    try {
        $processes = Get-CimInstance Win32_Process | Where-Object { 
            $_.CommandLine -like "*windows_ftp_json_uploader.ps1*" -and
            $_.ProcessName -eq "powershell"
        }
        return $processes
    } catch {
        Write-Log "获取上传进程失败: $($_.Exception.Message)" "ERROR"
        return @()
    }
}

function Test-LogHealth($logPath, $maxAgeSeconds) {
    if (-not (Test-Path $logPath)) {
        return $false
    }
    
    try {
        $lastWrite = (Get-Item $logPath).LastWriteTime
        $age = ((Get-Date) - $lastWrite).TotalSeconds
        return $age -le $maxAgeSeconds
    } catch {
        return $false
    }
}

function Test-FtpConnectivity() {
    try {
        $uri = "ftp://scan.example.com:21"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $req.Credentials = New-Object System.Net.NetworkCredential("your_ftp_username", "[REDACTED-FTP-PASSWORD]")
        $req.Timeout = 10000  # 10秒超时
        $req.UsePassive = $true
        $req.Proxy = $null
        
        $resp = $req.GetResponse()
        $resp.Close()
        return $true
    } catch {
        Write-Log "FTP连接测试失败: $($_.Exception.Message)" "WARN"
        return $false
    }
}

function Stop-UploaderProcesses($processes) {
    foreach ($proc in $processes) {
        try {
            Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Log "已终止进程 $($proc.ProcessId)"
        } catch {
            Write-Log "终止进程 $($proc.ProcessId) 失败: $($_.Exception.Message)" "WARN"
        }
    }
    Start-Sleep -Seconds 2  # 等待进程完全退出
}

function Start-UploaderProcess() {
    try {
        $psPath = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
        if (-not (Test-Path $psPath)) { 
            $psPath = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source 
        }
        
        $scriptPath = Join-Path $ProjectRoot 'scripts\windows_ftp_json_uploader.ps1'
        $args = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$scriptPath`""
        
        $proc = Start-Process -FilePath $psPath -ArgumentList $args -WindowStyle Hidden -PassThru
        Write-Log "已启动新的上传进程 (PID: $($proc.Id))"
        return $proc
    } catch {
        Write-Alert "启动上传进程失败: $($_.Exception.Message)"
        return $null
    }
}

function Update-SyncStatus($status) {
    try {
        $statusData = @{
            timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
            status = $status
            processes = @(Get-UploaderProcesses | ForEach-Object { @{id=$_.ProcessId; startTime=$_.CreationDate} })
            ftp_connectivity = Test-FtpConnectivity
            log_health = Test-LogHealth (Join-Path $logDir 'ftp_uploader.log') $StaleSeconds
        }
        $statusData | ConvertTo-Json -Depth 3 | Out-File -FilePath $statusFile -Encoding utf8
    } catch {
        Write-Log "更新状态失败: $($_.Exception.Message)" "WARN"
    }
}

function Update-Metrics($action) {
    try {
        $metricsData = @{}
        if (Test-Path $metricsFile) {
            $metricsData = Get-Content $metricsFile -Raw | ConvertFrom-Json -AsHashtable
        }
        
        if (-not $metricsData.ContainsKey($action)) {
            $metricsData[$action] = 0
        }
        $metricsData[$action]++
        $metricsData["last_$action"] = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        
        $metricsData | ConvertTo-Json | Out-File -FilePath $metricsFile -Encoding utf8
    } catch {
        Write-Log "更新指标失败: $($_.Exception.Message)" "WARN"
    }
}

function Test-SystemHealth() {
    $issues = @()
    
    # 检查磁盘空间
    $drive = Get-PSDrive -Name (Split-Path $ProjectRoot -Qualifier).TrimEnd(':')
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeSpaceGB -lt 1) {
        $issues += "磁盘空间不足: ${freeSpaceGB}GB"
    }
    
    # 检查关键目录
    $criticalDirs = @("cloud\demo_json_a", "cloud\demo_json_b", "auto_sync\logs")
    foreach ($dir in $criticalDirs) {
        $fullPath = Join-Path $ProjectRoot $dir
        if (-not (Test-Path $fullPath)) {
            $issues += "关键目录缺失: $dir"
        }
    }
    
    # 检查网络连接
    if (-not (Test-FtpConnectivity)) {
        $issues += "FTP连接失败"
    }
    
    return $issues
}

# 主监控逻辑
Write-Log "增强版同步守护进程启动 (PID: $PID)"
Write-Log "配置: StaleSeconds=$StaleSeconds, MaxProcesses=$MaxProcesses, HealthCheckInterval=$HealthCheckInterval"

# 系统健康检查
$healthIssues = Test-SystemHealth
if ($healthIssues.Count -gt 0) {
    Write-Alert "系统健康检查发现问题: $($healthIssues -join '; ')"
}

# 获取当前上传进程
$currentProcesses = Get-UploaderProcesses
$processCount = $currentProcesses.Count

Write-Log "发现 $processCount 个上传进程"

# 检查日志健康状态
$uploaderLogPath = Join-Path $logDir 'ftp_uploader.log'
$logHealthy = Test-LogHealth $uploaderLogPath $StaleSeconds

Write-Log "日志健康状态: $(if($logHealthy){'正常'}else{'异常'})"

# 决定是否需要重启
$needRestart = $false
$restartReason = ""

if ($processCount -eq 0) {
    $needRestart = $true
    $restartReason = "没有运行的上传进程"
} elseif ($processCount -gt $MaxProcesses) {
    $needRestart = $true
    $restartReason = "上传进程过多 ($processCount > $MaxProcesses)"
} elseif (-not $logHealthy) {
    $needRestart = $true
    $restartReason = "日志不活跃 (超过 $StaleSeconds 秒)"
}

if ($needRestart) {
    Write-Log "需要重启: $restartReason"
    Update-Metrics "restart_triggered"
    
    # 停止所有现有进程
    if ($processCount -gt 0) {
        Write-Log "正在停止 $processCount 个现有进程..."
        Stop-UploaderProcesses $currentProcesses
        Update-Metrics "processes_stopped"
    }
    
    # 启动新进程
    $newProcess = Start-UploaderProcess
    if ($newProcess) {
        Update-Metrics "process_started"
        Update-SyncStatus "restarted"
        Write-Log "同步服务已重启"
    } else {
        Update-SyncStatus "failed"
        Write-Alert "同步服务重启失败"
    }
} else {
    Write-Log "同步服务运行正常"
    Update-Metrics "health_check_passed"
    Update-SyncStatus "healthy"
}

Write-Log "守护进程检查完成"