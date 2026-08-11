#!/usr/bin/env powershell
# 增强版FTP上传器 - 更稳定、更智能的文件同步
param(
    [string]$ConfigFile = "auto_sync/enhanced_config.json",
    [switch]$Once = $false,
    [switch]$Debug = $false,
    [switch]$SafeMode = $false
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

# 加载配置
function Load-Config($configPath) {
    try {
        $fullPath = Join-Path $ProjectRoot $configPath
        if (-not (Test-Path $fullPath)) {
            throw "配置文件不存在: $fullPath"
        }
        return Get-Content $fullPath -Raw | ConvertFrom-Json
    } catch {
        Write-Error "加载配置失败: $($_.Exception.Message)"
        exit 1
    }
}

$config = Load-Config $ConfigFile

# 设置日志
$logDir = Join-Path $ProjectRoot 'auto_sync\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'enhanced_uploader.log'
$errorLogFile = Join-Path $logDir 'upload_errors.log'
$successLogFile = Join-Path $logDir 'upload_success.log'

function Write-Log($msg, $level = "INFO") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $logMsg = "$ts [$level] PID:$PID $msg"
    
    # 写入主日志
    $logMsg | Out-File -FilePath $logFile -Encoding utf8 -Append
    
    # 根据级别写入专门日志
    if ($level -eq "ERROR") {
        $logMsg | Out-File -FilePath $errorLogFile -Encoding utf8 -Append
    } elseif ($level -eq "SUCCESS") {
        $logMsg | Out-File -FilePath $successLogFile -Encoding utf8 -Append
    }
    
    # 调试模式下输出到控制台
    if ($Debug) {
        $color = switch($level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "SUCCESS" { "Green" }
            default { "White" }
        }
        Write-Host $logMsg -ForegroundColor $color
    }
}

function Test-FtpConnection($ftpConfig) {
    try {
        $uri = "ftp://$($ftpConfig.host):$($ftpConfig.port)"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $req.Credentials = New-Object System.Net.NetworkCredential($ftpConfig.username, $ftpConfig.password)
        $req.Timeout = $ftpConfig.connection_timeout_ms
        $req.UsePassive = $ftpConfig.use_passive
        $req.Proxy = $null
        
        $resp = $req.GetResponse()
        $resp.Close()
        Write-Log "FTP连接测试成功" "SUCCESS"
        return $true
    } catch {
        Write-Log "FTP连接测试失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-RemoteFileExists($remotePath, $ftpConfig) {
    try {
        $uri = "ftp://$($ftpConfig.host):$($ftpConfig.port)$remotePath"
        $req = [System.Net.FtpWebRequest]::Create($uri)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
        $req.Credentials = New-Object System.Net.NetworkCredential($ftpConfig.username, $ftpConfig.password)
        $req.Timeout = 5000  # 短超时用于存在性检查
        $req.UsePassive = $ftpConfig.use_passive
        $req.Proxy = $null
        
        $resp = $req.GetResponse()
        $size = $resp.ContentLength
        $resp.Close()
        return @{exists = $true; size = $size}
    } catch {
        return @{exists = $false; size = 0}
    }
}

function Ensure-RemoteDirectory($remoteDir, $ftpConfig) {
    try {
        # 分解路径并逐级创建
        $pathParts = $remoteDir.Trim('/').Split('/')
        $currentPath = ""
        
        foreach ($part in $pathParts) {
            if ($part) {
                $currentPath += "/$part"
                try {
                    $uri = "ftp://$($ftpConfig.host):$($ftpConfig.port)$currentPath"
                    $req = [System.Net.FtpWebRequest]::Create($uri)
                    $req.Method = [System.Net.WebRequestMethods+Ftp]::MakeDirectory
                    $req.Credentials = New-Object System.Net.NetworkCredential($ftpConfig.username, $ftpConfig.password)
                    $req.UsePassive = $ftpConfig.use_passive
                    $req.Proxy = $null
                    
                    $resp = $req.GetResponse()
                    $resp.Close()
                    Write-Log "创建远程目录: $currentPath" "INFO"
                } catch {
                    # 目录可能已存在，忽略错误
                }
            }
        }
        return $true
    } catch {
        Write-Log "确保远程目录失败 $remoteDir : $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-FileStability($filePath, $checkDurationMs = 300) {
    try {
        $initialSize = (Get-Item $filePath).Length
        Start-Sleep -Milliseconds $checkDurationMs
        $finalSize = (Get-Item $filePath).Length
        return $initialSize -eq $finalSize
    } catch {
        return $false
    }
}

function Invoke-FileUpload($localPath, $remoteDir, $ftpConfig, $syncConfig) {
    $fileName = [System.IO.Path]::GetFileName($localPath)
    $remoteFile = "$remoteDir/$fileName".Replace('//','/')
    
    try {
        # 检查文件稳定性
        if (-not (Test-FileStability $localPath $syncConfig.file_stability_check_ms)) {
            Write-Log "文件不稳定，跳过: $fileName" "WARN"
            return $false
        }
        
        # 检查文件大小限制
        $fileSize = (Get-Item $localPath).Length
        $maxSizeMB = $config.file_filters.max_file_size_mb
        if ($fileSize -gt ($maxSizeMB * 1MB)) {
            Write-Log "文件过大，跳过: $fileName (${fileSize}字节 > ${maxSizeMB}MB)" "WARN"
            return $false
        }
        
        if ($fileSize -lt $config.file_filters.min_file_size_bytes) {
            Write-Log "文件过小，跳过: $fileName (${fileSize}字节)" "WARN"
            return $false
        }
        
        # 检查远程文件是否存在
        if (-not $syncConfig.overwrite_existing) {
            $remoteCheck = Test-RemoteFileExists $remoteFile $ftpConfig
            if ($remoteCheck.exists) {
                if ($remoteCheck.size -eq $fileSize) {
                    Write-Log "文件已存在且大小相同，跳过: $remoteFile" "INFO"
                    return $true
                } else {
                    Write-Log "文件已存在但大小不同 (远程:$($remoteCheck.size) vs 本地:$fileSize): $remoteFile" "WARN"
                }
            }
        }
        
        # 确保远程目录存在
        if (-not (Ensure-RemoteDirectory $remoteDir $ftpConfig)) {
            Write-Log "无法创建远程目录: $remoteDir" "ERROR"
            return $false
        }
        
        # 执行上传（带重试机制）
        $attempt = 0
        $delay = [double]$syncConfig.retry_delay_ms
        $maxRetries = $syncConfig.retry_attempts
        
        while ($attempt -lt $maxRetries) {
            try {
                $uri = "ftp://$($ftpConfig.host):$($ftpConfig.port)$remoteFile"
                $req = [System.Net.FtpWebRequest]::Create($uri)
                $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
                $req.Credentials = New-Object System.Net.NetworkCredential($ftpConfig.username, $ftpConfig.password)
                $req.UseBinary = $true
                $req.UsePassive = $ftpConfig.use_passive
                $req.Timeout = $ftpConfig.upload_timeout_ms
                $req.Proxy = $null
                
                $bytes = [System.IO.File]::ReadAllBytes($localPath)
                $req.ContentLength = $bytes.Length
                
                $uploadStart = Get-Date
                $stream = $req.GetRequestStream()
                $stream.Write($bytes, 0, $bytes.Length)
                $stream.Close()
                
                $resp = $req.GetResponse()
                $resp.Close()
                
                $uploadTime = ((Get-Date) - $uploadStart).TotalMilliseconds
                $speedKBps = [math]::Round(($bytes.Length / 1024) / ($uploadTime / 1000), 2)
                
                Write-Log "上传成功: $localPath -> $remoteFile (${fileSize}字节, ${uploadTime}ms, ${speedKBps}KB/s)" "SUCCESS"
                
                # 可选：上传后删除本地文件
                if ($syncConfig.delete_after_upload) {
                    try {
                        Remove-Item $localPath -Force
                        Write-Log "已删除本地文件: $localPath" "INFO"
                    } catch {
                        Write-Log "删除本地文件失败: $localPath - $($_.Exception.Message)" "WARN"
                    }
                }
                
                return $true
                
            } catch {
                $attempt++
                $errorMsg = $_.Exception.Message
                Write-Log "上传重试 [$attempt/$maxRetries]: $fileName - $errorMsg" "WARN"
                
                if ($attempt -ge $maxRetries) {
                    Write-Log "上传最终失败: $localPath -> $remoteDir - $errorMsg" "ERROR"
                    return $false
                }
                
                # 指数退避延迟
                Start-Sleep -Milliseconds ([int][Math]::Min($delay, 30000))
                $delay *= $syncConfig.retry_backoff_multiplier
            }
        }
        return $false
    } catch {
        Write-Log "上传过程异常: $localPath - $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Sync-TaskDirectory($task, $ftpConfig, $syncConfig) {
    Write-Log "开始同步任务: $($task.task_id)"
    
    if (-not $task.enabled) {
        Write-Log "任务已禁用: $($task.task_id)" "INFO"
        return
    }
    
    $uploadCount = 0
    $skipCount = 0
    $errorCount = 0
    
    # 查找有效的本地目录
    $localDir = $null
    foreach ($candidate in $task.local_directories) {
        $fullPath = Join-Path $ProjectRoot $candidate
        if (Test-Path $fullPath) {
            $localDir = $fullPath
            break
        }
    }
    
    if (-not $localDir) {
        Write-Log "任务 $($task.task_id) 没有找到有效的本地目录: $($task.local_directories -join ', ')" "ERROR"
        return
    }
    
    Write-Log "使用本地目录: $localDir"
    
    # 获取匹配的文件并按修改时间排序
    try {
        $files = Get-ChildItem -Path $localDir -Filter $task.file_pattern -File | 
                  Sort-Object LastWriteTime -Descending |
                  Select-Object -First $task.max_files_per_batch
        
        Write-Log "发现 $($files.Count) 个匹配文件 (模式: $($task.file_pattern))"
        
        foreach ($file in $files) {
            try {
                # 检查文件年龄
                $fileAge = ((Get-Date) - $file.LastWriteTime).TotalDays
                if ($fileAge -gt $config.file_filters.max_file_age_days) {
                    Write-Log "文件过旧，跳过: $($file.Name) (${fileAge}天)" "INFO"
                    $skipCount++
                    continue
                }
                
                $success = Invoke-FileUpload $file.FullName $task.remote_directory $ftpConfig $syncConfig
                
                if ($success) {
                    $uploadCount++
                } else {
                    $errorCount++
                }
                
                # 安全模式下限制上传速度
                if ($SafeMode -and $uploadCount -gt 0 -and ($uploadCount % 5) -eq 0) {
                    Write-Log "安全模式：暂停2秒" "INFO"
                    Start-Sleep -Seconds 2
                }
                
            } catch {
                $errorCount++
                Write-Log "处理文件异常: $($file.FullName) - $($_.Exception.Message)" "ERROR"
            }
        }
        
        Write-Log "任务 $($task.task_id) 完成: 上传 $uploadCount, 跳过 $skipCount, 错误 $errorCount"
        
    } catch {
        Write-Log "扫描目录失败: $localDir - $($_.Exception.Message)" "ERROR"
    }
}

# 主程序开始
Write-Log "增强版FTP上传器启动 (PID: $PID)" "INFO"
Write-Log "配置文件: $ConfigFile, 单次模式: $Once, 调试模式: $Debug, 安全模式: $SafeMode"

# 测试FTP连接
if (-not (Test-FtpConnection $config.ftp_connection)) {
    if (-not $SafeMode) {
        Write-Log "FTP连接失败，退出程序" "ERROR"
        exit 1
    } else {
        Write-Log "FTP连接失败，但继续运行（安全模式）" "WARN"
    }
}

$loopCount = 0
$lastConnectivityCheck = Get-Date

# 主循环
while ($true) {
    $loopStart = Get-Date
    $loopCount++
    
    Write-Log "开始第 $loopCount 次同步循环"
    
    try {
        # 定期检查FTP连接
        if (((Get-Date) - $lastConnectivityCheck).TotalSeconds -gt $config.ftp_connection.connection_test_interval_seconds) {
            Test-FtpConnection $config.ftp_connection | Out-Null
            $lastConnectivityCheck = Get-Date
        }
        
        # 执行所有启用的同步任务
        foreach ($task in $config.sync_tasks) {
            if ($task.enabled) {
                Sync-TaskDirectory $task $config.ftp_connection $config.sync_settings
            }
        }
        
    } catch {
        Write-Log "同步循环异常: $($_.Exception.Message)" "ERROR"
    }
    
    $loopDuration = ((Get-Date) - $loopStart).TotalMilliseconds
    Write-Log "第 $loopCount 次循环完成 (耗时: ${loopDuration}ms)"
    
    if ($Once) {
        Write-Log "单次模式，退出程序" "INFO"
        break
    }
    
    Start-Sleep -Seconds $config.sync_settings.scan_interval_seconds
}

Write-Log "增强版FTP上传器退出" "INFO"