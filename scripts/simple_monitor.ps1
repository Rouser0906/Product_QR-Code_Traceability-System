# 简单的JSON文件监控和自动上传服务

Write-Host "启动JSON文件自动同步监控服务..." -ForegroundColor Green
Write-Host "监控目录: C:\Projects\Demo\cloud\demo_json_a" -ForegroundColor Yellow
Write-Host "监控目录: C:\Projects\Demo\cloud\demo_json_b" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green

# 服务器配置
$FtpServer = "192.0.2.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"

# 上传文件函数
function Upload-JsonFile {
    param([string]$FilePath, [string]$RemoteDir)
    
    $fileName = Split-Path $FilePath -Leaf
    $remoteUrl = "ftp://$FtpServer$RemoteDir/$fileName"
    
    try {
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
        $webclient.UploadFile($remoteUrl, $FilePath)
        $webclient.Dispose()
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 上传成功: $fileName" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 上传失败: $fileName - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# 先同步所有现有文件
Write-Host "正在同步所有现有文件..." -ForegroundColor Cyan

# 同步demo_json_a文件
$aDir = "C:\Projects\Demo\cloud\demo_json_a"
if (Test-Path $aDir) {
    $aFiles = Get-ChildItem -Path $aDir -Filter "*.json" -File
    Write-Host "找到 $($aFiles.Count) 个demo_json_a文件" -ForegroundColor Cyan
    foreach ($file in $aFiles) {
        Upload-JsonFile -FilePath $file.FullName -RemoteDir "/companies/demo_json_a"
        Start-Sleep -Milliseconds 100
    }
}

# 同步demo_json_b文件
$zyDir = "C:\Projects\Demo\cloud\demo_json_b"
if (Test-Path $zyDir) {
    $zyFiles = Get-ChildItem -Path $zyDir -Filter "*.json" -File
    Write-Host "找到 $($zyFiles.Count) 个demo_json_b文件" -ForegroundColor Cyan
    foreach ($file in $zyFiles) {
        Upload-JsonFile -FilePath $file.FullName -RemoteDir "/companies/demo_json_b"
        Start-Sleep -Milliseconds 100
    }
}

Write-Host "初始同步完成，开始实时监控..." -ForegroundColor Green

# 创建文件监控器
$aWatcher = New-Object System.IO.FileSystemWatcher
$aWatcher.Path = $aDir
$aWatcher.Filter = "*.json"
$aWatcher.NotifyFilter = [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::LastWrite
$aWatcher.EnableRaisingEvents = $true

$zyWatcher = New-Object System.IO.FileSystemWatcher
$zyWatcher.Path = $zyDir
$zyWatcher.Filter = "*.json"
$zyWatcher.NotifyFilter = [System.IO.NotifyFilters]::CreationTime -bor [System.IO.NotifyFilters]::LastWrite
$zyWatcher.EnableRaisingEvents = $true

# demo_json_a文件变化处理
$aAction = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    
    if ($changeType -eq "Created" -or $changeType -eq "Changed") {
        Start-Sleep -Seconds 2  # 等待文件写入完成
        if (Test-Path $path) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 检测到demo_json_a文件: $name ($changeType)" -ForegroundColor Yellow
            Upload-JsonFile -FilePath $path -RemoteDir "/companies/demo_json_a"
        }
    }
}

# demo_json_b文件变化处理
$zyAction = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    
    if ($changeType -eq "Created" -or $changeType -eq "Changed") {
        Start-Sleep -Seconds 2  # 等待文件写入完成
        if (Test-Path $path) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 检测到demo_json_b文件: $name ($changeType)" -ForegroundColor Yellow
            Upload-JsonFile -FilePath $path -RemoteDir "/companies/demo_json_b"
        }
    }
}

# 注册事件
Register-ObjectEvent -InputObject $aWatcher -EventName "Created" -Action $aAction
Register-ObjectEvent -InputObject $aWatcher -EventName "Changed" -Action $aAction
Register-ObjectEvent -InputObject $zyWatcher -EventName "Created" -Action $zyAction
Register-ObjectEvent -InputObject $zyWatcher -EventName "Changed" -Action $zyAction

Write-Host "监控服务已启动！等待文件变化..." -ForegroundColor Green

try {
    while ($true) {
        Start-Sleep -Seconds 10
        # 每10分钟显示一次心跳
        if ((Get-Date).Minute % 10 -eq 0 -and (Get-Date).Second -lt 10) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] 监控服务运行中..." -ForegroundColor Blue
        }
    }
}
finally {
    $aWatcher.Dispose()
    $zyWatcher.Dispose()
    Write-Host "监控服务已停止" -ForegroundColor Red
}