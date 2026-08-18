# 自动同步JSON文件到服务器的PowerShell脚本

param(
    [string]$Mode = "once"
)

# 服务器配置
$FtpServer = "192.0.2.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"

# 本地路径配置
$LocalBasePath = "C:\Projects\Demo\cloud"
$LogPath = "C:\Projects\Demo\scripts\auto_sync\logs"

# 确保日志目录存在
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

$LogFile = Join-Path $LogPath "sync_$(Get-Date -Format 'yyyyMMdd').log"

# 写日志函数
function Write-SyncLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

# 上传文件函数
function Upload-FileToFtp {
    param(
        [string]$LocalFile,
        [string]$RemoteFile
    )
    
    try {
        $ftpUri = "ftp://$FtpServer$RemoteFile"
        Write-SyncLog "上传文件: $LocalFile -> $ftpUri"
        
        # 使用WebClient上传文件
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
        $webclient.UploadFile($ftpUri, $LocalFile)
        $webclient.Dispose()
        
        Write-SyncLog "文件上传成功: $(Split-Path $LocalFile -Leaf)"
        return $true
    }
    catch {
        Write-SyncLog "文件上传失败: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# 同步目录函数
function Sync-JsonDirectory {
    param(
        [string]$LocalDir,
        [string]$RemoteDir
    )
    
    if (!(Test-Path $LocalDir)) {
        Write-SyncLog "本地目录不存在: $LocalDir" "WARNING"
        return
    }
    
    $jsonFiles = Get-ChildItem -Path $LocalDir -Filter "*.json" -File
    Write-SyncLog "在 $LocalDir 中找到 $($jsonFiles.Count) 个JSON文件"
    
    foreach ($file in $jsonFiles) {
        $remoteFile = "$RemoteDir/$($file.Name)"
        Upload-FileToFtp -LocalFile $file.FullName -RemoteFile $remoteFile
        Start-Sleep -Milliseconds 100  # 避免过快的请求
    }
}

# 主执行逻辑
Write-SyncLog "自动同步脚本启动，模式: $Mode"

try {
    # 同步demo_json_a目录
    $aLocalDir = Join-Path $LocalBasePath "demo_json_a"
    $aRemoteDir = "/companies/demo_json_a"
    Write-SyncLog "开始同步demo_json_a目录"
    Sync-JsonDirectory -LocalDir $aLocalDir -RemoteDir $aRemoteDir
    
    # 同步demo_json_b目录
    $zyLocalDir = Join-Path $LocalBasePath "demo_json_b"
    $zyRemoteDir = "/companies/demo_json_b"
    Write-SyncLog "开始同步demo_json_b目录"
    Sync-JsonDirectory -LocalDir $zyLocalDir -RemoteDir $zyRemoteDir
    
    Write-SyncLog "同步完成"
}
catch {
    Write-SyncLog "同步过程中发生错误: $($_.Exception.Message)" "ERROR"
}

# 如果是监控模式
if ($Mode -eq "watch") {
    Write-SyncLog "启动监控模式"
    
    $watcher1 = New-Object System.IO.FileSystemWatcher
    $watcher1.Path = Join-Path $LocalBasePath "demo_json_a"
    $watcher1.Filter = "*.json"
    $watcher1.EnableRaisingEvents = $true
    
    $watcher2 = New-Object System.IO.FileSystemWatcher
    $watcher2.Path = Join-Path $LocalBasePath "demo_json_b"
    $watcher2.Filter = "*.json"
    $watcher2.EnableRaisingEvents = $true
    
    $action = {
        $path = $Event.SourceEventArgs.FullPath
        $name = $Event.SourceEventArgs.Name
        $changeType = $Event.SourceEventArgs.ChangeType
        
        if ($changeType -eq "Created" -or $changeType -eq "Changed") {
            Start-Sleep -Seconds 1  # 等待文件写入完成
            
            if ($path.Contains("demo_json_a")) {
                $remoteFile = "/companies/demo_json_a/$name"
            } else {
                $remoteFile = "/companies/demo_json_b/$name"
            }
            
            Write-SyncLog "检测到文件变化: $name ($changeType)"
            Upload-FileToFtp -LocalFile $path -RemoteFile $remoteFile
        }
    }
    
    Register-ObjectEvent -InputObject $watcher1 -EventName "Created" -Action $action
    Register-ObjectEvent -InputObject $watcher1 -EventName "Changed" -Action $action
    Register-ObjectEvent -InputObject $watcher2 -EventName "Created" -Action $action
    Register-ObjectEvent -InputObject $watcher2 -EventName "Changed" -Action $action
    
    Write-SyncLog "文件监控已启动，按Ctrl+C退出"
    
    try {
        while ($true) {
            Start-Sleep -Seconds 1
        }
    }
    finally {
        $watcher1.Dispose()
        $watcher2.Dispose()
        Write-SyncLog "监控模式已停止"
    }
}