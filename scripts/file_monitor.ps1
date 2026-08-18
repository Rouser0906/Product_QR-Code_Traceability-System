# JSON File Auto-Sync Monitor Service

Write-Host "Starting JSON file auto-sync monitor service..." -ForegroundColor Green
Write-Host "Monitoring: C:\Projects\Demo\cloud\demo_json_a" -ForegroundColor Yellow
Write-Host "Monitoring: C:\Projects\Demo\cloud\demo_json_b" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop service" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green

# Server configuration
$FtpServer = "192.0.2.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"

# Upload function
function Upload-JsonFile {
    param([string]$FilePath, [string]$RemoteDir)
    
    $fileName = Split-Path $FilePath -Leaf
    $remoteUrl = "ftp://$FtpServer$RemoteDir/$fileName"
    
    try {
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
        $webclient.UploadFile($remoteUrl, $FilePath)
        $webclient.Dispose()
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] SUCCESS: $fileName" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] FAILED: $fileName - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Sync all existing files first
Write-Host "Syncing all existing files..." -ForegroundColor Cyan

# Sync demo_json_a files
$aDir = "C:\Projects\Demo\cloud\demo_json_a"
if (Test-Path $aDir) {
    $aFiles = Get-ChildItem -Path $aDir -Filter "*.json" -File
    Write-Host "Found $($aFiles.Count) demo_json_a files" -ForegroundColor Cyan
    foreach ($file in $aFiles) {
        Upload-JsonFile -FilePath $file.FullName -RemoteDir "/companies/demo_json_a"
        Start-Sleep -Milliseconds 100
    }
}

# Sync demo_json_b files
$zyDir = "C:\Projects\Demo\cloud\demo_json_b"
if (Test-Path $zyDir) {
    $zyFiles = Get-ChildItem -Path $zyDir -Filter "*.json" -File
    Write-Host "Found $($zyFiles.Count) demo_json_b files" -ForegroundColor Cyan
    foreach ($file in $zyFiles) {
        Upload-JsonFile -FilePath $file.FullName -RemoteDir "/companies/demo_json_b"
        Start-Sleep -Milliseconds 100
    }
}

Write-Host "Initial sync completed, starting real-time monitoring..." -ForegroundColor Green

# Create file watchers
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

# Event handlers
$aAction = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    
    if ($changeType -eq "Created" -or $changeType -eq "Changed") {
        Start-Sleep -Seconds 2
        if (Test-Path $path) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Detected demo_json_a file: $name ($changeType)" -ForegroundColor Yellow
            Upload-JsonFile -FilePath $path -RemoteDir "/companies/demo_json_a"
        }
    }
}

$zyAction = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    
    if ($changeType -eq "Created" -or $changeType -eq "Changed") {
        Start-Sleep -Seconds 2
        if (Test-Path $path) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Detected demo_json_b file: $name ($changeType)" -ForegroundColor Yellow
            Upload-JsonFile -FilePath $path -RemoteDir "/companies/demo_json_b"
        }
    }
}

# Register events
Register-ObjectEvent -InputObject $aWatcher -EventName "Created" -Action $aAction
Register-ObjectEvent -InputObject $aWatcher -EventName "Changed" -Action $aAction
Register-ObjectEvent -InputObject $zyWatcher -EventName "Created" -Action $zyAction
Register-ObjectEvent -InputObject $zyWatcher -EventName "Changed" -Action $zyAction

Write-Host "Monitor service started! Waiting for file changes..." -ForegroundColor Green

try {
    while ($true) {
        Start-Sleep -Seconds 10
        if ((Get-Date).Minute % 10 -eq 0 -and (Get-Date).Second -lt 10) {
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Monitor service running..." -ForegroundColor Blue
        }
    }
}
finally {
    $aWatcher.Dispose()
    $zyWatcher.Dispose()
    Write-Host "Monitor service stopped" -ForegroundColor Red
}