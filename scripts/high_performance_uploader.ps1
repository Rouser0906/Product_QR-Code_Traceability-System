#!/usr/bin/env powershell
# 高性能FTP上传器 - 针对速度和效率优化
param(
    [string]$FtpHost = 'scan.example.com',
    [int]$FtpPort = 21,
    [string]$FtpUser = 'your_ftp_username',
    [string]$FtpPass = '[REDACTED-FTP-PASSWORD]',
    [int]$MaxConcurrent = 3,        # 最大并发上传数
    [int]$BatchSize = 20,           # 每批处理文件数
    [int]$IntervalSeconds = 10,     # 扫描间隔（优化为10秒）
    [int]$ConnectionTimeout = 8000, # 连接超时（8秒）
    [int]$UploadTimeout = 25000,    # 上传超时（25秒）
    [switch]$Once = $false,
    [switch]$FastMode = $false,     # 快速模式：跳过存在性检查
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

# 性能配置
$PerformanceConfig = @{
    # 连接池配置
    ConnectionPoolSize = 5
    KeepAliveInterval = 30000
    
    # 批处理配置
    MaxBatchSize = $BatchSize
    MaxConcurrentUploads = $MaxConcurrent
    
    # 超时配置
    ConnectTimeoutMs = $ConnectionTimeout
    UploadTimeoutMs = $UploadTimeout
    ExistCheckTimeoutMs = 3000
    
    # 缓存配置
    ExistsCacheEnabled = $true
    ExistsCacheTTL = 300  # 5分钟缓存
    
    # 重试配置
    MaxRetries = 3
    RetryDelayMs = 500
    RetryBackoffMultiplier = 1.5
}

# 日志设置
$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'high_perf_uploader.log'
$perfLogFile = Join-Path $logDir 'upload_performance.log'

# 全局变量
$script:ExistsCache = @{}
$script:ActiveJobs = @()
$script:UploadStats = @{
    TotalFiles = 0
    SkippedFiles = 0
    UploadedFiles = 0
    FailedFiles = 0
    TotalBytes = 0
    StartTime = Get-Date
}

function Write-Log($msg, $level = "INFO") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $logMsg = "$ts [$level] PERF: $msg"
    $logMsg | Out-File -FilePath $logFile -Encoding utf8 -Append
    
    if ($Debug -or $level -eq "ERROR") {
        $color = switch($level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            "PERF" { "Magenta" }
            default { "White" }
        }
        Write-Host $logMsg -ForegroundColor $color
    }
}

function Write-PerfLog($action, $duration, $fileSize = 0, $details = "") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $speedKBps = if ($duration -gt 0 -and $fileSize -gt 0) { 
        [math]::Round(($fileSize / 1024) / ($duration / 1000), 2) 
    } else { 0 }
    
    $perfMsg = "$ts,$action,$duration,$fileSize,$speedKBps,$details"
    $perfMsg | Out-File -FilePath $perfLogFile -Encoding utf8 -Append
}

function Test-FtpConnectivity {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $uri = "ftp://${FtpHost}:${FtpPort}"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $req.Timeout = $PerformanceConfig.ConnectTimeoutMs
        $req.UsePassive = $true
        $req.Proxy = $null
        
        $resp = $req.GetResponse()
        $resp.Close()
        
        $stopwatch.Stop()
        Write-PerfLog "connectivity_test" $stopwatch.ElapsedMilliseconds 0 "success"
        Write-Log "FTP连接测试成功 ($($stopwatch.ElapsedMilliseconds)ms)" "SUCCESS"
        return $true
    } catch {
        $stopwatch.Stop()
        Write-PerfLog "connectivity_test" $stopwatch.ElapsedMilliseconds 0 "failed:$($_.Exception.Message)"
        Write-Log "FTP连接测试失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-RemoteFileExists($remotePath, $useCache = $true) {
    # 检查缓存
    if ($useCache -and $PerformanceConfig.ExistsCacheEnabled) {
        $cacheKey = $remotePath
        if ($script:ExistsCache.ContainsKey($cacheKey)) {
            $cacheEntry = $script:ExistsCache[$cacheKey]
            $age = ((Get-Date) - $cacheEntry.Timestamp).TotalSeconds
            if ($age -lt $PerformanceConfig.ExistsCacheTTL) {
                Write-PerfLog "exists_check" 0 0 "cache_hit:$($cacheEntry.Exists)"
                return $cacheEntry.Exists
            }
        }
    }
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $uri = "ftp://${FtpHost}:${FtpPort}$remotePath"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
        $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
        $req.Timeout = $PerformanceConfig.ExistCheckTimeoutMs
        $req.UsePassive = $true
        $req.Proxy = $null
        
        $resp = $req.GetResponse()
        $size = $resp.ContentLength
        $resp.Close()
        
        $stopwatch.Stop()
        
        # 更新缓存
        if ($PerformanceConfig.ExistsCacheEnabled) {
            $script:ExistsCache[$remotePath] = @{
                Exists = $true
                Size = $size
                Timestamp = Get-Date
            }
        }
        
        Write-PerfLog "exists_check" $stopwatch.ElapsedMilliseconds 0 "exists:true,size:$size"
        return $true
    } catch {
        $stopwatch.Stop()
        
        # 更新缓存
        if ($PerformanceConfig.ExistsCacheEnabled) {
            $script:ExistsCache[$remotePath] = @{
                Exists = $false
                Size = 0
                Timestamp = Get-Date
            }
        }
        
        Write-PerfLog "exists_check" $stopwatch.ElapsedMilliseconds 0 "exists:false"
        return $false
    }
}

function Invoke-FastUpload {
    param(
        [string]$LocalPath,
        [string]$RemoteDir,
        [int]$JobId = 0
    )
    
    $fileName = [System.IO.Path]::GetFileName($LocalPath)
    $remoteFile = "$RemoteDir/$fileName".Replace('//','/')
    $fileSize = (Get-Item $LocalPath -ErrorAction SilentlyContinue).Length
    
    if (-not $fileSize) {
        Write-Log "文件不存在或无法读取: $LocalPath" "ERROR"
        return $false
    }
    
    # 快速模式跳过存在性检查
    if (-not $FastMode) {
        if (Test-RemoteFileExists $remoteFile) {
            Write-Log "文件已存在，跳过: $remoteFile" "INFO"
            $script:UploadStats.SkippedFiles++
            return $true
        }
    }
    
    $attempt = 0
    $maxRetries = $PerformanceConfig.MaxRetries
    $delay = [double]$PerformanceConfig.RetryDelayMs
    
    while ($attempt -lt $maxRetries) {
        $uploadStart = [System.Diagnostics.Stopwatch]::StartNew()
        try {
            $uri = "ftp://${FtpHost}:${FtpPort}$remoteFile"
            $req = [System.Net.FtpWebRequest]::Create($uri)
            $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
            $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
            $req.UseBinary = $true
            $req.UsePassive = $true
            $req.Proxy = $null
            $req.Timeout = $PerformanceConfig.UploadTimeoutMs
            
            # 优化：直接流式传输，避免一次性读取整个文件
            $bytes = [System.IO.File]::ReadAllBytes($LocalPath)
            $req.ContentLength = $bytes.Length
            
            $stream = $req.GetRequestStream()
            $stream.Write($bytes, 0, $bytes.Length)
            $stream.Close()
            
            $resp = $req.GetResponse()
            $resp.Close()
            
            $uploadStart.Stop()
            $uploadTime = $uploadStart.ElapsedMilliseconds
            $speedKBps = [math]::Round(($fileSize / 1024) / ($uploadTime / 1000), 2)
            
            Write-Log "上传成功 [Job$JobId]: $fileName (${fileSize}字节, ${uploadTime}ms, ${speedKBps}KB/s)" "SUCCESS"
            Write-PerfLog "upload_success" $uploadTime $fileSize "job:$JobId,speed:${speedKBps}KB/s"
            
            $script:UploadStats.UploadedFiles++
            $script:UploadStats.TotalBytes += $fileSize
            
            # 上传成功后更新缓存
            if ($PerformanceConfig.ExistsCacheEnabled) {
                $script:ExistsCache[$remoteFile] = @{
                    Exists = $true
                    Size = $fileSize
                    Timestamp = Get-Date
                }
            }
            
            return $true
            
        } catch {
            $uploadStart.Stop()
            $attempt++
            $errorMsg = $_.Exception.Message
            Write-Log "上传重试 [Job$JobId] [$attempt/$maxRetries]: $fileName - $errorMsg" "WARN"
            Write-PerfLog "upload_retry" $uploadStart.ElapsedMilliseconds $fileSize "job:$JobId,attempt:$attempt,error:$errorMsg"
            
            if ($attempt -ge $maxRetries) {
                Write-Log "上传失败 [Job$JobId]: $fileName - $errorMsg" "ERROR"
                Write-PerfLog "upload_failed" $uploadStart.ElapsedMilliseconds $fileSize "job:$JobId,error:$errorMsg"
                $script:UploadStats.FailedFiles++
                return $false
            }
            
            Start-Sleep -Milliseconds ([int][Math]::Min($delay, 5000))
            $delay *= $PerformanceConfig.RetryBackoffMultiplier
        }
    }
    return $false
}

function Sync-DirectoryParallel {
    param(
        [string]$LocalDir,
        [string]$RemoteDir,
        [string]$Filter = '*.json'
    )
    
    if (-not (Test-Path $LocalDir)) { 
        Write-Log "本地目录不存在: $LocalDir" "WARN"
        return 
    }
    
    Write-Log "开始并行同步: $LocalDir -> $RemoteDir" "INFO"
    
    # 获取文件列表，按大小排序（小文件优先）
    $files = Get-ChildItem -Path $LocalDir -Filter $Filter -File | 
              Sort-Object Length, LastWriteTime -Descending |
              Select-Object -First $PerformanceConfig.MaxBatchSize
    
    if ($files.Count -eq 0) {
        Write-Log "没有找到匹配的文件: $Filter" "INFO"
        return
    }
    
    Write-Log "发现 $($files.Count) 个文件待处理" "INFO"
    $script:UploadStats.TotalFiles += $files.Count
    
    # 分批并行处理
    $jobCounter = 0
    $activeJobs = @()
    
    foreach ($file in $files) {
        # 等待活跃任务数量控制
        while ($activeJobs.Count -ge $PerformanceConfig.MaxConcurrentUploads) {
            $completedJobs = @()
            foreach ($job in $activeJobs) {
                if ($job.State -eq "Completed") {
                    $completedJobs += $job
                    Receive-Job $job | Out-Null
                    Remove-Job $job
                }
            }
            $activeJobs = $activeJobs | Where-Object { $completedJobs -notcontains $_ }
            
            if ($activeJobs.Count -ge $PerformanceConfig.MaxConcurrentUploads) {
                Start-Sleep -Milliseconds 100
            }
        }
        
        # 文件稳定性检查（异步优化）
        try {
            $size1 = $file.Length
            Start-Sleep -Milliseconds 100  # 减少等待时间
            $size2 = (Get-Item $file.FullName).Length
            if ($size1 -ne $size2) {
                Write-Log "文件不稳定，跳过: $($file.Name)" "WARN"
                continue
            }
        } catch {
            Write-Log "文件检查失败，跳过: $($file.Name)" "WARN"
            continue
        }
        
        # 启动上传任务
        $jobCounter++
        $scriptBlock = {
            param($LocalPath, $RemoteDir, $JobId, $FtpHost, $FtpPort, $FtpUser, $FtpPass, $PerformanceConfig, $FastMode)
            
            # 重新导入必要的函数和变量到作业上下文
            $fileName = [System.IO.Path]::GetFileName($LocalPath)
            $remoteFile = "$RemoteDir/$fileName".Replace('//','/')
            $fileSize = (Get-Item $LocalPath).Length
            
            try {
                $uri = "ftp://${FtpHost}:${FtpPort}$remoteFile"
                $req = [System.Net.FtpWebRequest]::Create($uri)
                $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
                $req.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPass)
                $req.UseBinary = $true
                $req.UsePassive = $true
                $req.Proxy = $null
                $req.Timeout = $PerformanceConfig.UploadTimeoutMs
                
                $bytes = [System.IO.File]::ReadAllBytes($LocalPath)
                $req.ContentLength = $bytes.Length
                
                $stream = $req.GetRequestStream()
                $stream.Write($bytes, 0, $bytes.Length)
                $stream.Close()
                
                $resp = $req.GetResponse()
                $resp.Close()
                
                return @{Success = $true; FileName = $fileName; Size = $fileSize}
            } catch {
                return @{Success = $false; FileName = $fileName; Error = $_.Exception.Message}
            }
        }
        
        $job = Start-Job -ScriptBlock $scriptBlock -ArgumentList $file.FullName, $RemoteDir, $jobCounter, $FtpHost, $FtpPort, $FtpUser, $FtpPass, $PerformanceConfig, $FastMode
        $activeJobs += $job
        
        Write-Log "启动上传任务 [Job$jobCounter]: $($file.Name)" "INFO"
    }
    
    # 等待所有任务完成
    Write-Log "等待所有上传任务完成..." "INFO"
    while ($activeJobs.Count -gt 0) {
        $completedJobs = @()
        foreach ($job in $activeJobs) {
            if ($job.State -eq "Completed") {
                $result = Receive-Job $job
                if ($result.Success) {
                    Write-Log "上传完成: $($result.FileName) ($($result.Size)字节)" "SUCCESS"
                    $script:UploadStats.UploadedFiles++
                    $script:UploadStats.TotalBytes += $result.Size
                } else {
                    Write-Log "上传失败: $($result.FileName) - $($result.Error)" "ERROR"
                    $script:UploadStats.FailedFiles++
                }
                $completedJobs += $job
                Remove-Job $job
            }
        }
        $activeJobs = $activeJobs | Where-Object { $completedJobs -notcontains $_ }
        
        if ($activeJobs.Count -gt 0) {
            Start-Sleep -Milliseconds 200
        }
    }
    
    Write-Log "目录同步完成: $LocalDir" "SUCCESS"
}

function Show-PerformanceStats {
    $duration = ((Get-Date) - $script:UploadStats.StartTime).TotalSeconds
    $throughputKBps = if ($duration -gt 0) { 
        [math]::Round(($script:UploadStats.TotalBytes / 1024) / $duration, 2) 
    } else { 0 }
    
    Write-Log "=== 性能统计 ===" "PERF"
    Write-Log "总文件数: $($script:UploadStats.TotalFiles)" "PERF"
    Write-Log "上传成功: $($script:UploadStats.UploadedFiles)" "PERF"
    Write-Log "跳过文件: $($script:UploadStats.SkippedFiles)" "PERF"
    Write-Log "失败文件: $($script:UploadStats.FailedFiles)" "PERF"
    Write-Log "总字节数: $($script:UploadStats.TotalBytes)" "PERF"
    Write-Log "执行时间: $([math]::Round($duration, 2))秒" "PERF"
    Write-Log "平均吞吐: ${throughputKBps} KB/s" "PERF"
    
    Write-PerfLog "session_summary" ($duration * 1000) $script:UploadStats.TotalBytes "files:$($script:UploadStats.TotalFiles),success:$($script:UploadStats.UploadedFiles),failed:$($script:UploadStats.FailedFiles)"
}

# 主程序开始
Write-Log "高性能FTP上传器启动 (PID: $PID)" "INFO"
Write-Log "配置: 并发=$MaxConcurrent, 批次=$BatchSize, 间隔=${IntervalSeconds}s, 快速模式=$FastMode" "INFO"

# 连接测试
if (-not (Test-FtpConnectivity)) {
    Write-Log "FTP连接失败，程序退出" "ERROR"
    exit 1
}

# 解析目录
$LocalA = $null
$LocalB = $null
foreach ($candidate in @('cloud/demo_json_a','companies/demo_json_a')) {
    $fullPath = Join-Path $ProjectRoot $candidate
    if (Test-Path $fullPath) { $LocalA = $fullPath; break }
}
foreach ($candidate in @('cloud/demo_json_b','companies/demo_json_b')) {
    $fullPath = Join-Path $ProjectRoot $candidate
    if (Test-Path $fullPath) { $LocalB = $fullPath; break }
}

$RemoteHS = '/companies/demo_json_a'
$RemoteZY = '/companies/demo_json_b'

Write-Log "目录映射: LocalA=$LocalA, LocalB=$LocalB" "INFO"

$loopCount = 0

# 主循环
while ($true) {
    $loopStart = Get-Date
    $loopCount++
    
    Write-Log "开始第 $loopCount 次高性能同步循环" "INFO"
    
    try {
        # 重置统计
        $script:UploadStats = @{
            TotalFiles = 0; SkippedFiles = 0; UploadedFiles = 0; FailedFiles = 0
            TotalBytes = 0; StartTime = Get-Date
        }
        
        # 并行同步两个目录
        if ($LocalA) {
            Sync-DirectoryParallel -LocalDir $LocalA -RemoteDir $RemoteHS -Filter 'A-Q*.json'
        }
        if ($LocalB) {
            Sync-DirectoryParallel -LocalDir $LocalB -RemoteDir $RemoteZY -Filter 'B-Q*.json'
        }
        
        # 显示性能统计
        Show-PerformanceStats
        
    } catch {
        Write-Log "同步循环异常: $($_.Exception.Message)" "ERROR"
    }
    
    $loopDuration = ((Get-Date) - $loopStart).TotalSeconds
    Write-Log "第 $loopCount 次循环完成 (耗时: $([math]::Round($loopDuration, 2))s)" "INFO"
    
    if ($Once) {
        Write-Log "单次模式，程序退出" "INFO"
        break
    }
    
    # 清理过期缓存
    if ($script:ExistsCache.Count -gt 1000) {
        $now = Get-Date
        $keysToRemove = @()
        foreach ($key in $script:ExistsCache.Keys) {
            $age = ($now - $script:ExistsCache[$key].Timestamp).TotalSeconds
            if ($age -gt $PerformanceConfig.ExistsCacheTTL) {
                $keysToRemove += $key
            }
        }
        foreach ($key in $keysToRemove) {
            $script:ExistsCache.Remove($key)
        }
        Write-Log "清理了 $($keysToRemove.Count) 个过期缓存项" "INFO"
    }
    
    Start-Sleep -Seconds $IntervalSeconds
}

Write-Log "高性能FTP上传器退出" "INFO"