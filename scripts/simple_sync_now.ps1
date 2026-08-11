# Simple JSON File Sync - Immediate Upload Solution

param(
    [string]$TargetFile = "",
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
    
    # Sync HS files
    if (Test-Path $LocalHS) {
        $hsFiles = Get-ChildItem -Path $LocalHS -Filter "*.json" -File
        Write-Log "Found $($hsFiles.Count) HS files"
        
        foreach ($file in $hsFiles) {
            if (Upload-File $file.FullName $RemoteHS) {
                $totalUploaded++
            }
            Start-Sleep -Milliseconds 200  # Brief pause between uploads
        }
    }
    
    # Sync ZY files
    if (Test-Path $LocalZY) {
        $zyFiles = Get-ChildItem -Path $LocalZY -Filter "*.json" -File
        Write-Log "Found $($zyFiles.Count) ZY files"
        
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
    
    # Check HS directory
    $hsPath = Join-Path $LocalHS $fileName
    if (Test-Path $hsPath) {
        Write-Log "Found in HS directory: $hsPath"
        Upload-File $hsPath $RemoteHS
        return
    }
    
    # Check ZY directory
    $zyPath = Join-Path $LocalZY $fileName
    if (Test-Path $zyPath) {
        Write-Log "Found in ZY directory: $zyPath"
        Upload-File $zyPath $RemoteZY
        return
    }
    
    Write-Host "File not found: $fileName" -ForegroundColor Yellow
}

# Main execution
Write-Log "=== Simple JSON Sync Tool ==="
Write-Log "FTP Server: $FtpHost"
Write-Log "HS Directory: $LocalHS"
Write-Log "ZY Directory: $LocalZY"

# Handle target file parameter
if ($TargetFile -and $TargetFile -like "*.json") {
    Write-Log "Target file specified: $TargetFile"
    Upload-SpecificFile $TargetFile
} else {
    Write-Log "No specific target file, syncing all files..."
    Sync-AllFiles
}

Write-Log "=== Sync Complete ==="