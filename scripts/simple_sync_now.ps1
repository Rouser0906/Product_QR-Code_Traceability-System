# Simple JSON File Sync - Immediate Upload Solution

param(
    [string]$TargetFile = "",
    [string]$FtpHost = 'scan.example.com',
    [int]$FtpPort = 21,
    [string]$Username = 'your_ftp_username',
    [string]$Password = '[REDACTED-FTP-PASSWORD]',
    [string]$LocalA = 'C:\Projects\Demo\cloud\demo_json_a',
    [string]$LocalB = 'C:\Projects\Demo\cloud\demo_json_b',
    [string]$RemoteHS = '/companies/demo_json_a',
    [string]$RemoteZY = '/companies/demo_json_b'
)

function Write-Log($message) {
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "[$timestamp] $message" -ForegroundColor Green
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
        Write-Host "ERROR uploading $fileName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Sync-AllFiles {
    Write-Log "Starting immediate sync of all JSON files..."
    
    $totalUploaded = 0
    
    # Sync A files
    if (Test-Path $LocalA) {
        $aFiles = Get-ChildItem -Path $LocalA -Filter "*.json" -File
        Write-Log "Found $($aFiles.Count) A files"
        
        foreach ($file in $aFiles) {
            if (Upload-File $file.FullName $RemoteHS) {
                $totalUploaded++
            }
            Start-Sleep -Milliseconds 200  # Brief pause between uploads
        }
    }
    
    # Sync B files
    if (Test-Path $LocalB) {
        $zyFiles = Get-ChildItem -Path $LocalB -Filter "*.json" -File
        Write-Log "Found $($zyFiles.Count) B files"
        
        foreach ($file in $zyFiles) {
            if (Upload-File $file.FullName $RemoteZY) {
                $totalUploaded++
            }
            Start-Sleep -Milliseconds 200  # Brief pause between uploads
        }
    }
    
    Write-Log "Sync completed! Uploaded $totalUploaded files"
}

function Upload-SpecificFile($fileName) {
    Write-Log "Looking for specific file: $fileName"
    
    # Check A directory
    $aPath = Join-Path $LocalA $fileName
    if (Test-Path $aPath) {
        Write-Log "Found in A directory: $aPath"
        Upload-File $aPath $RemoteHS
        return
    }
    
    # Check B directory
    $zyPath = Join-Path $LocalB $fileName
    if (Test-Path $zyPath) {
        Write-Log "Found in B directory: $zyPath"
        Upload-File $zyPath $RemoteZY
        return
    }
    
    Write-Host "File not found: $fileName" -ForegroundColor Yellow
}

# Main execution
Write-Log "=== Simple JSON Sync Tool ==="
Write-Log "FTP Server: $FtpHost"
Write-Log "A Directory: $LocalA"
Write-Log "B Directory: $LocalB"

# Handle target file parameter
if ($TargetFile -and $TargetFile -like "*.json") {
    Write-Log "Target file specified: $TargetFile"
    Upload-SpecificFile $TargetFile
} else {
    Write-Log "No specific target file, syncing all files..."
    Sync-AllFiles
}

Write-Log "=== Sync Complete ==="