# Working File Watcher - Simple and Reliable JSON Auto Upload

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

function Write-Log($message) {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logMessage = "[$timestamp] $message"
    Write-Host $logMessage -ForegroundColor Green
    
    # Also write to log file
    $logPath = "auto_sync\logs\file_watcher.log"
    if (!(Test-Path (Split-Path $logPath))) {
        New-Item -ItemType Directory -Force -Path (Split-Path $logPath) | Out-Null
    }
    $logMessage | Out-File -FilePath $logPath -Encoding UTF8 -Append
}

function Upload-File($localFile, $remoteDir) {
    try {
        $fileName = [System.IO.Path]::GetFileName($localFile)
        $remoteUrl = "ftp://$FtpHost`:$FtpPort$remoteDir/$fileName"
        
        Write-Log "Uploading: $fileName"
        
        $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $req.UsePassive = $true
        $req.UseBinary = $true
        $req.Timeout = 30000
        
        $fileBytes = [System.IO.File]::ReadAllBytes($localFile)
        $req.ContentLength = $fileBytes.Length
        
        $requestStream = $req.GetRequestStream()
        $requestStream.Write($fileBytes, 0, $fileBytes.Length)
        $requestStream.Close()
        
        $response = $req.GetResponse()
        $response.Close()
        
        Write-Log "SUCCESS: $fileName uploaded successfully"
        return $true
    } catch {
        Write-Log "ERROR uploading $fileName`: $($_.Exception.Message)"
        return $false
    }
}

function Start-Monitoring {
    Write-Log "=== JSON File Watcher Started ==="
    Write-Log "Monitoring HS: $LocalHS"
    Write-Log "Monitoring ZY: $LocalZY"
    Write-Log "Target Server: $FtpHost"
    
    # Ensure directories exist
    if (!(Test-Path $LocalHS)) { New-Item -ItemType Directory -Force -Path $LocalHS }
    if (!(Test-Path $LocalZY)) { New-Item -ItemType Directory -Force -Path $LocalZY }
    
    # Create file watchers
    $hsWatcher = New-Object System.IO.FileSystemWatcher
    $hsWatcher.Path = $LocalHS
    $hsWatcher.Filter = "*.json"
    $hsWatcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite
    $hsWatcher.EnableRaisingEvents = $true
    
    $zyWatcher = New-Object System.IO.FileSystemWatcher
    $zyWatcher.Path = $LocalZY
    $zyWatcher.Filter = "*.json"
    $zyWatcher.NotifyFilter = [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::LastWrite
    $zyWatcher.EnableRaisingEvents = $true
    
    # Event handlers
    $hsAction = {
        param($source, $e)
        Start-Sleep -Seconds 1  # Wait for file to be fully written
        Write-Log "HS file detected: $($e.Name)"
        Upload-File $e.FullPath $using:RemoteHS
    }
    
    $zyAction = {
        param($source, $e)
        Start-Sleep -Seconds 1  # Wait for file to be fully written
        Write-Log "ZY file detected: $($e.Name)"
        Upload-File $e.FullPath $using:RemoteZY
    }
    
    # Register events
    Register-ObjectEvent -InputObject $hsWatcher -EventName Created -Action $hsAction
    Register-ObjectEvent -InputObject $hsWatcher -EventName Changed -Action $hsAction
    Register-ObjectEvent -InputObject $zyWatcher -EventName Created -Action $zyAction
    Register-ObjectEvent -InputObject $zyWatcher -EventName Changed -Action $zyAction
    
    Write-Log "File watchers activated. Monitoring for new JSON files..."
    Write-Log "Press Ctrl+C to stop monitoring"
    
    # Keep script running and periodically sync any missed files
    $syncCounter = 0
    try {
        while ($true) {
            Start-Sleep -Seconds 30
            
            # Every 5 minutes, do a full sync check
            $syncCounter++
            if ($syncCounter -ge 10) {  # 10 * 30 seconds = 5 minutes
                Write-Log "Performing periodic sync check..."
                
                # Quick sync of any new files
                $hsFiles = Get-ChildItem -Path $LocalHS -Filter "*.json" -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }
                $zyFiles = Get-ChildItem -Path $LocalZY -Filter "*.json" -File | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }
                
                foreach ($file in $hsFiles) {
                    Write-Log "Periodic sync: $($file.Name)"
                    Upload-File $file.FullName $RemoteHS
                    Start-Sleep -Milliseconds 200
                }
                
                foreach ($file in $zyFiles) {
                    Write-Log "Periodic sync: $($file.Name)"
                    Upload-File $file.FullName $RemoteZY
                    Start-Sleep -Milliseconds 200
                }
                
                $syncCounter = 0
            }
        }
    } finally {
        # Cleanup
        $hsWatcher.Dispose()
        $zyWatcher.Dispose()
        Write-Log "File watchers stopped"
    }
}

# Start monitoring
Start-Monitoring