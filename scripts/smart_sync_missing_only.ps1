# Smart Sync - Only upload JSON files that are missing from server
# Intelligent sync that ONLY uploads files missing on server, never duplicates

param(
    [string]$FtpHost = 'scan.example.com',
    [int]$FtpPort = 21,
    [string]$Username = 'your_ftp_username', 
    [string]$Password = '[REDACTED-FTP-PASSWORD]',
    [int]$ScanIntervalSeconds = 8
)

$ErrorActionPreference = 'Continue'

# Get project root and setup paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$hsDir = Join-Path $ProjectRoot "cloud\demo_json_a"
$zyDir = Join-Path $ProjectRoot "cloud\demo_json_b"
$logDir = Join-Path $ProjectRoot "auto_sync\logs"
$logFile = Join-Path $logDir "smart_sync.log"

# Create necessary directories
New-Item -ItemType Directory -Force -Path $hsDir, $zyDir, $logDir | Out-Null

function Write-SmartLog($msg, $level = "INFO") {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fff')
    $logEntry = "$ts [$level] SMART_SYNC: $msg"
    $logEntry | Out-File -FilePath $logFile -Encoding UTF8 -Append
    
    $color = switch($level) {
        "ERROR" { "Red" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "SKIP" { "Cyan" }
        default { "White" }
    }
    Write-Host $logEntry -ForegroundColor $color
}

function Test-FileExistsOnServer([string]$fileName, [string]$remoteDir) {
    $remoteUrl = "ftp://$FtpHost`:$FtpPort$remoteDir/$fileName"
    
    try {
        $checkReq = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $checkReq.Method = [System.Net.WebRequestMethods+Ftp]::GetFileSize
        $checkReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $checkReq.UsePassive = $true
        $checkReq.Timeout = 8000
        $checkResp = $checkReq.GetResponse()
        $remoteSize = $checkResp.ContentLength
        $checkResp.Close()
        
        return @{ Exists = $true; Size = $remoteSize }
    } catch {
        return @{ Exists = $false; Size = 0 }
    }
}

function Upload-OnlyIfMissing([string]$localPath, [string]$remoteDir) {
    $fileName = [System.IO.Path]::GetFileName($localPath)
    
    # Check if local file exists and is stable
    if (-not (Test-Path $localPath)) {
        Write-SmartLog "Local file not found: $localPath" "WARNING"
        return $false
    }
    
    # Wait for file stability
    $size1 = (Get-Item $localPath).Length
    Start-Sleep -Milliseconds 200
    $size2 = (Get-Item $localPath).Length
    if ($size1 -ne $size2) {
        Write-SmartLog "File still writing, waiting: $fileName" "WARNING"
        Start-Sleep -Milliseconds 500
        return $false
    }
    
    # Check if file exists on server
    $serverCheck = Test-FileExistsOnServer -fileName $fileName -remoteDir $remoteDir
    
    if ($serverCheck.Exists) {
        $localSize = (Get-Item $localPath).Length
        if ($serverCheck.Size -eq $localSize) {
            Write-SmartLog "SKIP - File already exists on server: $fileName (Local:$localSize bytes, Server:$($serverCheck.Size) bytes)" "SKIP"
            return $true  # File exists and sizes match, skip upload
        } else {
            Write-SmartLog "Size mismatch, re-uploading: $fileName (Local:$localSize, Server:$($serverCheck.Size))" "WARNING"
        }
    } else {
        Write-SmartLog "File MISSING on server, uploading: $fileName" "INFO"
    }
    
    # Execute upload only if needed
    try {
        $remoteUrl = "ftp://$FtpHost`:$FtpPort$remoteDir/$fileName"
        $uploadReq = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $uploadReq.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $uploadReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $uploadReq.UsePassive = $true
        $uploadReq.UseBinary = $true
        $uploadReq.Timeout = 30000
        $uploadReq.Proxy = $null
        
        $fileContent = [System.IO.File]::ReadAllBytes($localPath)
        $uploadReq.ContentLength = $fileContent.Length
        
        $requestStream = $uploadReq.GetRequestStream()
        $requestStream.Write($fileContent, 0, $fileContent.Length)
        $requestStream.Close()
        
        $response = $uploadReq.GetResponse()
        $response.Close()
        
        Write-SmartLog "UPLOAD SUCCESS: $fileName (Size: $($fileContent.Length) bytes)" "SUCCESS"
        return $true
        
    } catch {
        Write-SmartLog "UPLOAD FAILED: $fileName | Error: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Scan-ForMissingFiles([string]$localDir, [string]$remoteDir, [string]$prefix) {
    if (-not (Test-Path $localDir)) {
        Write-SmartLog "Local directory not found: $localDir" "WARNING"
        return @{ Total = 0; Missing = 0; Uploaded = 0; Skipped = 0 }
    }
    
    $allFiles = Get-ChildItem -Path $localDir -Filter "*.json" | Sort-Object Name
    $totalFiles = $allFiles.Count
    $missingCount = 0
    $uploadedCount = 0
    $skippedCount = 0
    
    Write-SmartLog "Scanning $prefix directory: $localDir (Total: $totalFiles files)"
    
    foreach ($file in $allFiles) {
        $serverCheck = Test-FileExistsOnServer -fileName $file.Name -remoteDir $remoteDir
        
        if (-not $serverCheck.Exists) {
            $missingCount++
            Write-SmartLog "MISSING on server: $($file.Name)" "WARNING"
            
            $success = Upload-OnlyIfMissing -localPath $file.FullName -remoteDir $remoteDir
            if ($success) {
                $uploadedCount++
            }
        } else {
            $localSize = $file.Length
            if ($serverCheck.Size -eq $localSize) {
                $skippedCount++
                Write-SmartLog "EXISTS and complete: $($file.Name)" "SKIP"
            } else {
                $missingCount++
                Write-SmartLog "Size mismatch: $($file.Name) (Local:$localSize, Server:$($serverCheck.Size))" "WARNING"
                
                $success = Upload-OnlyIfMissing -localPath $file.FullName -remoteDir $remoteDir
                if ($success) {
                    $uploadedCount++
                }
            }
        }
        
        Start-Sleep -Milliseconds 100
    }
    
    return @{
        Total = $totalFiles
        Missing = $missingCount
        Uploaded = $uploadedCount
        Skipped = $skippedCount
    }
}

# Main program
Write-SmartLog "=== Smart Sync Started - Only uploads files MISSING from server ===" "SUCCESS"
Write-SmartLog "FTP Server: $FtpHost`:$FtpPort"
Write-SmartLog "Local HS Dir: $hsDir"
Write-SmartLog "Local ZY Dir: $zyDir"
Write-SmartLog "Scan Interval: ${ScanIntervalSeconds}s"

# Execute initial full scan for missing files
Write-SmartLog "Starting initial scan for missing files..." "INFO"

$hsResult = Scan-ForMissingFiles -localDir $hsDir -remoteDir "/companies/demo_json_a" -prefix "HS"
$zyResult = Scan-ForMissingFiles -localDir $zyDir -remoteDir "/companies/demo_json_b" -prefix "ZY"

Write-SmartLog "HS Results: Total=$($hsResult.Total), Missing=$($hsResult.Missing), Uploaded=$($hsResult.Uploaded), Skipped=$($hsResult.Skipped)" "SUCCESS"
Write-SmartLog "ZY Results: Total=$($zyResult.Total), Missing=$($zyResult.Missing), Uploaded=$($zyResult.Uploaded), Skipped=$($zyResult.Skipped)" "SUCCESS"

# Start continuous monitoring for new files only
Write-SmartLog "Starting continuous monitoring for NEW files only..." "INFO"
$lastScanTime = Get-Date

while ($true) {
    Start-Sleep -Seconds $ScanIntervalSeconds
    
    $currentTime = Get-Date
    
    # Only check newly created or modified files
    $newFiles = @()
    
    # Check HS directory for new files
    if (Test-Path $hsDir) {
        $hsNewFiles = Get-ChildItem -Path $hsDir -Filter "*.json" | Where-Object { $_.LastWriteTime -gt $lastScanTime }
        foreach ($file in $hsNewFiles) {
            $newFiles += @{ Path = $file.FullName; RemoteDir = "/companies/demo_json_a"; Name = $file.Name }
        }
    }
    
    # Check ZY directory for new files
    if (Test-Path $zyDir) {
        $zyNewFiles = Get-ChildItem -Path $zyDir -Filter "*.json" | Where-Object { $_.LastWriteTime -gt $lastScanTime }
        foreach ($file in $zyNewFiles) {
            $newFiles += @{ Path = $file.FullName; RemoteDir = "/companies/demo_json_b"; Name = $file.Name }
        }
    }
    
    # Process new files (only upload if missing from server)
    if ($newFiles.Count -gt 0) {
        Write-SmartLog "Found $($newFiles.Count) new files, checking if missing on server..."
        
        foreach ($fileInfo in $newFiles) {
            $serverCheck = Test-FileExistsOnServer -fileName $fileInfo.Name -remoteDir $fileInfo.RemoteDir
            
            if (-not $serverCheck.Exists) {
                Write-SmartLog "New file MISSING on server, uploading: $($fileInfo.Name)" "INFO"
                Upload-OnlyIfMissing -localPath $fileInfo.Path -remoteDir $fileInfo.RemoteDir
            } else {
                $localSize = (Get-Item $fileInfo.Path).Length
                if ($serverCheck.Size -eq $localSize) {
                    Write-SmartLog "New file already EXISTS on server, skipping: $($fileInfo.Name)" "SKIP"
                } else {
                    Write-SmartLog "New file size mismatch, re-uploading: $($fileInfo.Name)" "WARNING"
                    Upload-OnlyIfMissing -localPath $fileInfo.Path -remoteDir $fileInfo.RemoteDir
                }
            }
        }
    }
    
    $lastScanTime = $currentTime
    
    # Heartbeat every 5 minutes
    if ($currentTime.Second -eq 0 -and $currentTime.Minute % 5 -eq 0) {
        Write-SmartLog "Monitoring heartbeat - Smart sync active (only missing files)" "INFO"
    }
}