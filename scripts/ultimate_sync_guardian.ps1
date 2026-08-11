# 终极同步守护程序 - 确保JSON文件100%自动同步
# 多重保障：文件监控 + 定时扫描 + 重试机制 + 日志记录

param(
    [string]$FtpHost = 'scan.example.com',
    [int]$FtpPort = 21,
    [string]$Username = 'your_ftp_username',
    [string]$Password = '[REDACTED-FTP-PASSWORD]',
    [string]$LocalHS = 'C:\Projects\Demo\cloud\demo_json_a',
    [string]$LocalZY = 'C:\Projects\Demo\cloud\demo_json_b',
    [string]$RemoteHS = '/companies/demo_json_a',
    [string]$RemoteZY = '/companies/demo_json_b'
)

$ErrorActionPreference = 'Continue'

# 全局变量
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $ProjectRoot 'auto_sync\logs'
$LogFile = Join-Path $LogDir 'ultimate_sync.log'
$StatusFile = Join-Path $LogDir 'sync_status.json'
$PendingQueue = @{}
$UploadedFiles = @{}

# 确保日志目录存在
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-ULog($level, $message) {
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $logEntry = "[$timestamp] [$level] $message"
    Write-Host $logEntry -ForegroundColor $(if($level -eq 'ERROR'){'Red'} elseif($level -eq 'WARN'){'Yellow'} elseif($level -eq 'SUCCESS'){'Green'} else{'White'})
    $logEntry | Out-File -FilePath $LogFile -Encoding UTF8 -Append
}

function Test-FtpConnection {
    try {
        $testReq = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost`:$FtpPort/")
        $testReq.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $testReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $testReq.UsePassive = $true
        $testReq.Timeout = 10000
        $response = $testReq.GetResponse()
        $response.Close()
        Write-ULog "SUCCESS" "FTP连接测试成功"
        return $true
    } catch {
        Write-ULog "ERROR" "FTP连接失败: $($_.Exception.Message)"
        return $false
    }
}

function Get-RemoteFileHash($remotePath) {
    try {
        $req = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost`:$FtpPort$remotePath")
        $req.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
        $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $req.UsePassive = $true
        $req.Timeout = 5000
        $response = $req.GetResponse()
        $size = $response.ContentLength
        $response.Close()
        return $size
    } catch {
        return $null
    }
}

function Upload-JsonFileWithRetry($localPath, $maxRetries = 3) {
    if (-not (Test-Path $localPath)) {
        Write-ULog "WARN" "本地文件不存在: $localPath"
        return $false
    }

    # 等待文件稳定
    Start-Sleep -Milliseconds 500
    $localSize1 = (Get-Item $localPath).Length
    Start-Sleep -Milliseconds 300
    $localSize2 = (Get-Item $localPath).Length
    if ($localSize1 -ne $localSize2) {
        Write-ULog "INFO" "文件正在写入，等待稳定: $localPath"
        Start-Sleep -Seconds 2
    }

    $fileName = [System.IO.Path]::GetFileName($localPath)
    $parentDir = [System.IO.Path]::GetDirectoryName($localPath)
    
    # 判断目标目录
    $isHS = $parentDir -match '\\demo_json_a$'
    $isZY = $parentDir -match '\\demo_json_b$'
    
    if (-not ($isHS -or $isZY)) {
        Write-ULog "WARN" "文件不在监控目录中: $localPath"
        return $false
    }

    $remoteDir = if ($isHS) { $RemoteHS } else { $RemoteZY }
    $remotePath = "$remoteDir/$fileName"
    $remoteUrl = "ftp://$FtpHost`:$FtpPort$remotePath"

    # 检查远程文件
    $remoteSize = Get-RemoteFileHash $remotePath
    $localSize = (Get-Item $localPath).Length
    
    if ($remoteSize -eq $localSize) {
        Write-ULog "INFO" "文件已存在且大小相同，跳过: $fileName"
        $UploadedFiles[$localPath] = Get-Date
        return $true
    }

    # 执行上传，带重试机制
    for ($attempt = 1; $attempt -le $maxRetries; $attempt++) {
        try {
            Write-ULog "INFO" "开始上传 (尝试 $attempt/$maxRetries): $fileName -> $remotePath"
            
            $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
            $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
            $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
            $req.UsePassive = $true
            $req.UseBinary = $true
            $req.Timeout = 30000
            $req.Proxy = $null
            
            $fileBytes = [System.IO.File]::ReadAllBytes($localPath)
            $req.ContentLength = $fileBytes.Length
            
            $requestStream = $req.GetRequestStream()
            $requestStream.Write($fileBytes, 0, $fileBytes.Length)
            $requestStream.Close()
            
            $response = $req.GetResponse()
            $response.Close()
            
            # 验证上传
            Start-Sleep -Milliseconds 500
            $uploadedSize = Get-RemoteFileHash $remotePath
            if ($uploadedSize -eq $localSize) {
                Write-ULog "SUCCESS" "上传成功并验证: $fileName ($localSize 字节)"
                $UploadedFiles[$localPath] = Get-Date
                return $true
            } else {
                throw "上传后大小不匹配: 本地=$localSize, 远程=$uploadedSize"
            }
            
        } catch {
            Write-ULog "ERROR" "上传失败 (尝试 $attempt/$maxRetries): $fileName - $($_.Exception.Message)"
            if ($attempt -lt $maxRetries) {
                $delay = $attempt * 2
                Write-ULog "INFO" "等待 $delay 秒后重试..."
                Start-Sleep -Seconds $delay
            }
        }
    }
    
    Write-ULog "ERROR" "上传最终失败: $fileName (已重试 $maxRetries 次)"
    return $false
}

function Scan-AndUploadPending {
    Write-ULog "INFO" "开始扫描待上传文件..."
    
    $directories = @(
        @{Path=$LocalHS; Type="HS"},
        @{Path=$LocalZY; Type="ZY"}
    )
    
    $uploadCount = 0
    foreach ($dir in $directories) {
        if (Test-Path $dir.Path) {
            $jsonFiles = Get-ChildItem -Path $dir.Path -Filter "*.json" -File
            foreach ($file in $jsonFiles) {
                $fullPath = $file.FullName
                
                # 检查是否已上传且未修改
                if ($UploadedFiles.ContainsKey($fullPath)) {
                    $lastModified = $file.LastWriteTime
                    $lastUploaded = $UploadedFiles[$fullPath]
                    if ($lastModified -le $lastUploaded) {
                        continue # 跳过已上传且未修改的文件
                    }
                }
                
                Write-ULog "INFO" "发现待上传文件: $($file.Name)"
                if (Upload-JsonFileWithRetry $fullPath) {
                    $uploadCount++
                }
            }
        } else {
            Write-ULog "WARN" "监控目录不存在: $($dir.Path)"
        }
    }
    
    if ($uploadCount -gt 0) {
        Write-ULog "SUCCESS" "本轮扫描完成，上传了 $uploadCount 个文件"
    }
}

function Start-FileWatcher($path, $type) {
    try {
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Force -Path $path | Out-Null
            Write-ULog "INFO" "创建监控目录: $path"
        }
        
        $watcher = New-Object System.IO.FileSystemWatcher
        $watcher.Path = $path
        $watcher.Filter = "*.json"
        $watcher.IncludeSubdirectories = $false
        $watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::CreationTime
        $watcher.EnableRaisingEvents = $true
        
        $action = {
            param($source, $eventArgs)
            $filePath = $eventArgs.FullPath
            $fileName = [System.IO.Path]::GetFileName($filePath)
            
            # 防抖处理
            if ($PendingQueue.ContainsKey($filePath)) {
                $lastEvent = $PendingQueue[$filePath]
                if (((Get-Date) - $lastEvent).TotalSeconds -lt 2) {
                    return
                }
            }
            $PendingQueue[$filePath] = Get-Date
            
            Write-ULog "DETECTED" "检测到文件变化: $fileName"
            
            # 直接调用上传函数，不使用Job避免作用域问题
            Start-Sleep -Seconds 1
            Write-ULog "INFO" "开始处理文件: $fileName"
            Upload-JsonFileWithRetry $filePath
        }
        
        Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action
        Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $action
        
        Write-ULog "SUCCESS" "启动文件监控: $path ($type)"
        return $watcher
        
    } catch {
        Write-ULog "ERROR" "启动文件监控失败: $path - $($_.Exception.Message)"
        return $null
    }
}

function Save-SyncStatus {
    $status = @{
        LastRun = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
        UploadedFiles = $UploadedFiles
        TotalUploaded = $UploadedFiles.Count
    }
    $status | ConvertTo-Json -Depth 3 | Out-File -FilePath $StatusFile -Encoding UTF8
}

function Load-SyncStatus {
    if (Test-Path $StatusFile) {
        try {
            $status = Get-Content $StatusFile -Raw | ConvertFrom-Json
            if ($status.UploadedFiles) {
                foreach ($file in $status.UploadedFiles.PSObject.Properties) {
                    $UploadedFiles[$file.Name] = [DateTime]$file.Value
                }
            }
            Write-ULog "INFO" "加载同步状态: 已上传 $($UploadedFiles.Count) 个文件"
        } catch {
            Write-ULog "WARN" "加载同步状态失败: $($_.Exception.Message)"
        }
    }
}

# 主程序开始
Write-ULog "INFO" "======== 终极同步守护程序启动 ========"
Write-ULog "INFO" "监控目录: $LocalHS"
Write-ULog "INFO" "监控目录: $LocalZY"
Write-ULog "INFO" "FTP服务器: $FtpHost`:$FtpPort"

# 加载历史状态
Load-SyncStatus

# 测试FTP连接
if (-not (Test-FtpConnection)) {
    Write-ULog "ERROR" "FTP连接失败，程序将继续运行但上传可能失败"
}

# 启动文件监控
$hsWatcher = Start-FileWatcher $LocalHS "HS"
$zyWatcher = Start-FileWatcher $LocalZY "ZY"

# 初始扫描
Scan-AndUploadPending

Write-ULog "INFO" "进入监控循环..."

# 主循环
$scanCounter = 0
try {
    while ($true) {
        Start-Sleep -Seconds 10
        
        # 处理队列中的文件
        $toProcess = @()
        foreach ($file in $PendingQueue.Keys) {
            $eventTime = $PendingQueue[$file]
            if (((Get-Date) - $eventTime).TotalSeconds -gt 2) {
                $toProcess += $file
            }
        }
        
        foreach ($file in $toProcess) {
            $PendingQueue.Remove($file)
            if (Test-Path $file) {
                Upload-JsonFileWithRetry $file
            }
        }
        
        # 定期全量扫描（每5分钟）
        $scanCounter++
        if ($scanCounter -ge 30) { # 30 * 10秒 = 5分钟
            $scanCounter = 0
            Scan-AndUploadPending
            Save-SyncStatus
        }
        
        # 定期测试FTP连接（每分钟）
        if (($scanCounter % 6) -eq 0) {
            Test-FtpConnection | Out-Null
        }
    }
} finally {
    # 清理资源
    if ($hsWatcher) { $hsWatcher.Dispose() }
    if ($zyWatcher) { $zyWatcher.Dispose() }
    Save-SyncStatus
    Write-ULog "INFO" "程序结束，已保存同步状态"
}