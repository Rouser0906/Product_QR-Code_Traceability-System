# 自动同步服务 - 监控JSON文件变化并立即上传到服务器
# 这个脚本会持续运行，监控文件变化并自动上传

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop
)

# 服务器配置
$FtpServer = "10.0.0.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"

# 本地路径配置
$LocalBasePath = "C:\Projects\Demo\cloud"
$LogPath = "C:\Projects\Demo\scripts\auto_sync\logs"

# 确保日志目录存在
if (!(Test-Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force | Out-Null
}

$LogFile = Join-Path $LogPath "auto_sync_$(Get-Date -Format 'yyyyMMdd').log"

function Write-SyncLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry -Encoding UTF8
}

function Upload-JsonFile {
    param(
        [string]$LocalFile,
        [string]$RemoteDir
    )
    
    $fileName = Split-Path $LocalFile -Leaf
    $remoteUrl = "ftp://$FtpServer$RemoteDir/$fileName"
    
    try {
        Write-SyncLog "开始上传: $fileName"
        
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
        $webclient.UploadFile($remoteUrl, $LocalFile)
        $webclient.Dispose()
        
        Write-SyncLog "上传成功: $fileName" "SUCCESS"
        return $true
    }
    catch {
        Write-SyncLog "上传失败: $fileName - $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Start-FileWatcher {
    Write-SyncLog "启动文件监控服务..."
    
    # 监控demo_json_a目录
    $aWatcher = New-Object System.IO.FileSystemWatcher
    $aWatcher.Path = Join-Path $LocalBasePath "demo_json_a"
    $aWatcher.Filter = "*.json"
    $aWatcher.NotifyFilter = [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::LastWrite
    $aWatcher.EnableRaisingEvents = $true
    
    # 监控demo_json_b目录
    $zyWatcher = New-Object System.IO.FileSystemWatcher
    $zyWatcher.Path = Join-Path $LocalBasePath "demo_json_b"
    $zyWatcher.Filter = "*.json"
    $zyWatcher.NotifyFilter = [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::LastWrite
    $zyWatcher.EnableRaisingEvents = $true
    
    # 文件变化处理函数
    $aAction = {
        $path = $Event.SourceEventArgs.FullPath
        $name = $Event.SourceEventArgs.Name
        $changeType = $Event.SourceEventArgs.ChangeType
        
        if ($changeType -eq "Created" -or $changeType -eq "Changed") {
            Start-Sleep -Seconds 2  # 等待文件写入完成
            
            if (Test-Path $path) {
                Write-SyncLog "检测到demo_json_a文件变化: $name ($changeType)"
                Upload-JsonFile -LocalFile $path -RemoteDir "/companies/demo_json_a"
            }
        }
    }
    
    $zyAction = {
        $path = $Event.SourceEventArgs.FullPath
        $name = $Event.SourceEventArgs.Name
        $changeType = $Event.SourceEventArgs.ChangeType
        
        if ($changeType -eq "Created" -or $changeType -eq "Changed") {
            Start-Sleep -Seconds 2  # 等待文件写入完成
            
            if (Test-Path $path) {
                Write-SyncLog "检测到demo_json_b文件变化: $name ($changeType)"
                Upload-JsonFile -LocalFile $path -RemoteDir "/companies/demo_json_b"
            }
        }
    }
    
    # 注册事件处理器
    Register-ObjectEvent -InputObject $aWatcher -EventName "Created" -Action $aAction
    Register-ObjectEvent -InputObject $aWatcher -EventName "Changed" -Action $aAction
    Register-ObjectEvent -InputObject $zyWatcher -EventName "Created" -Action $zyAction
    Register-ObjectEvent -InputObject $zyWatcher -EventName "Changed" -Action $zyAction
    
    Write-SyncLog "文件监控服务已启动"
    Write-SyncLog "监控目录: $(Join-Path $LocalBasePath 'demo_json_a')"
    Write-SyncLog "监控目录: $(Join-Path $LocalBasePath 'demo_json_b')"
    Write-SyncLog "按Ctrl+C停止服务"
    
    try {
        # 首次启动时同步所有现有文件
        Write-SyncLog "执行初始同步..."
        Sync-AllFiles
        
        # 持续监控
        while ($true) {
            Start-Sleep -Seconds 5
            # 每5分钟记录一次心跳
            if ((Get-Date).Minute % 5 -eq 0 -and (Get-Date).Second -lt 5) {
                Write-SyncLog "服务运行中..." "HEARTBEAT"
            }
        }
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        Write-SyncLog "服务被用户停止"
    }
    finally {
        $aWatcher.Dispose()
        $zyWatcher.Dispose()
        Write-SyncLog "文件监控服务已停止"
    }
}

function Sync-AllFiles {
    Write-SyncLog "开始同步所有现有文件..."
    
    # 同步demo_json_a文件
    $aDir = Join-Path $LocalBasePath "demo_json_a"
    if (Test-Path $aDir) {
        $aFiles = Get-ChildItem -Path $aDir -Filter "*.json" -File
        Write-SyncLog "找到 $($aFiles.Count) 个demo_json_a文件"
        foreach ($file in $aFiles) {
            Upload-JsonFile -LocalFile $file.FullName -RemoteDir "/companies/demo_json_a"
            Start-Sleep -Milliseconds 200
        }
    }
    
    # 同步demo_json_b文件
    $zyDir = Join-Path $LocalBasePath "demo_json_b"
    if (Test-Path $zyDir) {
        $zyFiles = Get-ChildItem -Path $zyDir -Filter "*.json" -File
        Write-SyncLog "找到 $($zyFiles.Count) 个demo_json_b文件"
        foreach ($file in $zyFiles) {
            Upload-JsonFile -LocalFile $file.FullName -RemoteDir "/companies/demo_json_b"
            Start-Sleep -Milliseconds 200
        }
    }
    
    Write-SyncLog "初始同步完成"
}

# 主执行逻辑
if ($Install) {
    Write-SyncLog "安装自动同步服务..."
    # 这里可以添加Windows服务安装逻辑
    Write-SyncLog "请手动运行 Start-FileWatcher 来启动服务"
}
elseif ($Uninstall) {
    Write-SyncLog "卸载自动同步服务..."
    # 这里可以添加Windows服务卸载逻辑
}
elseif ($Start) {
    Start-FileWatcher
}
elseif ($Stop) {
    Write-SyncLog "停止自动同步服务..."
    # 发送停止信号
}
else {
    # 默认启动监控服务
    Start-FileWatcher
}