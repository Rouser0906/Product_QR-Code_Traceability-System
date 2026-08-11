# Reliable JSON File Monitor - Simplified Version

# Configuration
$LocalA = 'C:\Projects\Demo\cloud\demo_json_a'
$LocalB = 'C:\Projects\Demo\cloud\demo_json_b'
$FtpHost = 'scan.example.com'
$FtpPort = 21
$Username = 'your_ftp_username'
$Password = '[REDACTED-FTP-PASSWORD]'
$RemoteHS = '/companies/demo_json_a'
$RemoteZY = '/companies/demo_json_b'

# Ensure log directory exists
$LogDir = 'auto_sync\logs'
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}
$LogFile = Join-Path $LogDir 'json_monitor.log'

function Write-Log($message) {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logEntry = "[$timestamp] $message"
    Write-Host $logEntry -ForegroundColor Green
    $logEntry | Out-File -FilePath $LogFile -Encoding UTF8 -Append
}

function Upload-JsonFile($localPath, $remoteDir) {
    try {
        $fileName = Split-Path $localPath -Leaf
        $remoteUrl = "ftp://${FtpHost}:${FtpPort}${remoteDir}/${fileName}"
        
        Write-Log "Uploading: $fileName"
        
        $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $req.UsePassive = $true
        $req.UseBinary = $true
        $req.Timeout = 30000
        
        $fileContent = [System.IO.File]::ReadAllBytes($localPath)
        $req.ContentLength = $fileContent.Length
        
        $stream = $req.GetRequestStream()
        $stream.Write($fileContent, 0, $fileContent.Length)
        $stream.Close()
        
        $response = $req.GetResponse()
        $response.Close()
        
        Write-Log "SUCCESS: $fileName uploaded"
        return $true
    } catch {
        Write-Log "ERROR: Failed to upload $fileName - $($_.Exception.Message)"
        return $false
    }
}

function Get-LastProcessedFiles {
    $statusFile = Join-Path $LogDir 'last_processed.txt'
    if (Test-Path $statusFile) {
        return Get-Content $statusFile
    }
    return @()
}

function Save-ProcessedFile($fileName) {
    $statusFile = Join-Path $LogDir 'last_processed.txt'
    $fileName | Out-File -FilePath $statusFile -Encoding UTF8 -Append
}

function Monitor-NewFiles {
    Write-Log "=== JSON Monitor Started ==="
    Write-Log "Monitoring: $LocalA"
    Write-Log "Monitoring: $LocalB"
    
    $lastProcessed = Get-LastProcessedFiles
    $processedThisSession = @()
    
    while ($true) {
        try {
            # Check A directory
            if (Test-Path $LocalA) {
                $aFiles = Get-ChildItem -Path $LocalA -Filter "*.json" -File
                foreach ($file in $aFiles) {
                    if ($file.Name -notin $lastProcessed -and $file.Name -notin $processedThisSession) {
                        # Wait a moment to ensure file is fully written
                        Start-Sleep -Seconds 2
                        
                        if (Upload-JsonFile $file.FullName $RemoteHS) {
                            Save-ProcessedFile $file.Name
                            $processedThisSession += $file.Name
                        }
                    }
                }
            }
            
            # Check B directory
            if (Test-Path $LocalB) {
                $zyFiles = Get-ChildItem -Path $LocalB -Filter "*.json" -File
                foreach ($file in $zyFiles) {
                    if ($file.Name -notin $lastProcessed -and $file.Name -notin $processedThisSession) {
                        # Wait a moment to ensure file is fully written
                        Start-Sleep -Seconds 2
                        
                        if (Upload-JsonFile $file.FullName $RemoteZY) {
                            Save-ProcessedFile $file.Name
                            $processedThisSession += $file.Name
                        }
                    }
                }
            }
            
            # Wait before next check
            Start-Sleep -Seconds 10
            
        } catch {
            Write-Log "ERROR in monitoring loop: $($_.Exception.Message)"
            Start-Sleep -Seconds 30
        }
    }
}

# Start monitoring
Monitor-NewFiles