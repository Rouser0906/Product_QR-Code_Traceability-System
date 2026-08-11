# 修复版自动同步程序 - 监控cloud目录并自动上传到FTP
# 解决空白窗口问题，确保JSON文件自动同步功能

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
$LogFile = Join-Path $LogDir 'fixed_sync.log'
$PendingFiles = @{}

# 确保日志目录存在
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

function Write-SyncLog($level, $message) {
    $timestamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $logEntry = "[$timestamp] [$level] $message"
    Write-Host $logEntry -ForegroundColor $(
        switch($level) {
            'ERROR' { 'Red' }
            'WARN' { 'Yellow' }
            'SUCCESS' { 'Green' }
            'UPLOAD' { 'Cyan' }
            default { 'White' }
        }
    )
    Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
}

function Test-FtpConnection {
    try {
        $uri = "ftp://$FtpHost`:$FtpPort/"
        $request = [System.Net.FtpWebRequest]::Create($uri)
        $request.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $request.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $request.UsePassive = $true
        $request.Timeout = 10000
        
        $response = $request.GetResponse()
        $response.Close()
        
        Write-SyncLog "SUCCESS" "FTP连接测试成功"
        return $true
    } catch {
        Write-SyncLog "ERROR" "FTP连接失败: $($_.Exception.Message)"
        return $false
    }
}

function Upload-JsonFile($localFilePath) {
    if (-not (Test-Path $localFilePath)) {
        Write-SyncLog "WARN" "本地文件不存在: $localFilePath"
        return $false
    }

    $fileName = [System.IO.Path]::GetFileName($localFilePath)
    $parentDir = [System.IO.Path]::GetDirectoryName($localFilePath)
    
    # 判断目标目录
    $isHS = $parentDir -like "*\demo_json_a"
    $isZY = $parentDir -like "*\demo_json_b"
    
    if (-not ($isHS -or $isZY)) {
        Write-SyncLog "WARN" "文件不在监控目录中: $localFilePath"
        return $false
    }

    $remoteDir = if ($isHS) { $RemoteHS } else { $RemoteZY }
    $remotePath = "$remoteDir/$fileName"
    $remoteUrl = "ftp://$FtpHost`:$FtpPort$remotePath"

    # 执行上传，最多重试3次
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Write-SyncLog "UPLOAD" "开始上传 (尝试 $attempt/3): $fileName -> $remotePath"
            
            # 等待文件稳定
            Start-Sleep -Milliseconds 500
            
            $request = [System.Net.FtpWebRequest]::Create($remoteUrl)
            $request.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
            $request.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
            $request.UsePassive = $true
            $request.UseBinary = $true
            $request.Timeout = 30000
            
            $fileBytes = [System.IO.File]::ReadAllBytes($localFilePath)
            $request.ContentLength = $fileBytes.Length
            
            $requestStream = $request.GetRequestStream()
            $requestStream.Write($fileBytes, 0, $fileBytes.Length)
            $requestStream.Close()
            
            $response = $request.GetResponse()
            $response.Close()
            
            Write-SyncLog "SUCCESS" "上传成功: $fileName ($($fileBytes.Length) 字节)"
            return $true
            
        } catch {
            Write-SyncLog "ERROR" "上传失败 (尝试 $attempt/3): $fileName - $($_.Exception.Message)"
            if ($attempt -lt 3) {
                Start-Sleep -Seconds ($attempt * 2)
            }
        }
    }
    
    Write-SyncLog "ERROR" "上传最终失败: $fileName (已重试3次)"
    return $false
}

function Start-DirectoryMonitor($path, $type) {
    try {
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Force -Path $path | Out-Null
            Write-SyncLog "INFO" "创建监控目录: $path"
        }
        
        $watcher = New-Object System.IO.FileSystemWatcher
        $watcher.Path = $path
        $watcher.Filter = "*.json"
        $watcher.IncludeSubdirectories = $false
        $watcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite
        $watcher.EnableRaisingEvents = $true
        
        $action = {
            param($source, $eventArgs)
            $filePath = $eventArgs.FullPath
            $fileName = [System.IO.Path]::GetFileName($filePath)
            
            Write-SyncLog "DETECTED" "检测到文件变化: $fileName"
            
            # 延迟处理避免文件锁定
            Start-Sleep -Seconds 2
            
            if (Test-Path $filePath) {
                Upload-JsonFile $filePath
            }
        }
        
        Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action
        Register-ObjectEvent -InputObject $watcher -EventName Changed -Action $action
        
        Write-SyncLog "SUCCESS" "启动文件监控: $path ($type)"
        return $watcher
        
    } catch {
        Write-SyncLog "ERROR" "启动文件监控失败: $path - $($_.Exception.Message)"
        return $null
    }
}

function Scan-ExistingFiles {
    Write-SyncLog "INFO" "扫描现有文件..."
    
    $directories = @(
        @{Path=$LocalHS; Type="HS"},
        @{Path=$LocalZY; Type="ZY"}
    )
    
    $uploadCount = 0
    foreach ($dir in $directories) {
        if (Test-Path $dir.Path) {
            $jsonFiles = Get-ChildItem -Path $dir.Path -Filter "*.json" -File
            foreach ($file in $jsonFiles) {
                Write-SyncLog "INFO" "发现文件: $($file.Name)"
                if (Upload-JsonFile $file.FullName) {
                    $uploadCount++
                }
            }
        } else {
            Write-SyncLog "WARN" "监控目录不存在: $($dir.Path)"
        }
    }
    
    Write-SyncLog "SUCCESS" "初始扫描完成，处理了 $uploadCount 个文件"
}

# 主程序开始
Write-SyncLog "INFO" "======== 修复版自动同步程序启动 ========"
Write-SyncLog "INFO" "监控目录: $LocalHS"
Write-SyncLog "INFO" "监控目录: $LocalZY"
Write-SyncLog "INFO" "FTP服务器: $FtpHost`:$FtpPort"

# 测试FTP连接
if (-not (Test-FtpConnection)) {
    Write-SyncLog "ERROR" "FTP连接失败，程序将继续运行但上传可能失败"
}

# 启动文件监控
$hsWatcher = Start-DirectoryMonitor $LocalHS "HS"
$zyWatcher = Start-DirectoryMonitor $LocalZY "ZY"

# 初始扫描现有文件
Scan-ExistingFiles

Write-SyncLog "INFO" "进入监控循环..."

# 主循环
try {
    while ($true) {
        Start-Sleep -Seconds 30
        
        # 定期测试FTP连接
        if (-not (Test-FtpConnection)) {
            Write-SyncLog "WARN" "FTP连接中断，等待恢复..."
        }
    }
} catch {
    Write-SyncLog "ERROR" "程序异常: $($_.Exception.Message)"
} finally {
    # 清理资源
    if ($hsWatcher) { 
        $hsWatcher.EnableRaisingEvents = $false
        $hsWatcher.Dispose() 
    }
    if ($zyWatcher) { 
        $zyWatcher.EnableRaisingEvents = $false
        $zyWatcher.Dispose() 
    }
    Write-SyncLog "INFO" "程序结束，已清理资源"
}