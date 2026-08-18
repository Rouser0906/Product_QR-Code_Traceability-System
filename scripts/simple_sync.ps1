# Simple JSON file sync script

# Server configuration
$FtpServer = "192.0.2.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"

# Local path configuration
$LocalBasePath = "C:\Projects\Demo\cloud"

Write-Host "Starting JSON file sync to server..."

# Check demo_json_a directory
$aLocalDir = Join-Path $LocalBasePath "demo_json_a"
if (Test-Path $aLocalDir) {
    $aFiles = Get-ChildItem -Path $aLocalDir -Filter "*.json" -File
    Write-Host "Found $($aFiles.Count) demo_json_a files"
    
    foreach ($file in $aFiles) {
        try {
            $ftpUri = "ftp://$FtpServer/companies/demo_json_a/$($file.Name)"
            Write-Host "Uploading: $($file.Name)"
            
            $webclient = New-Object System.Net.WebClient
            $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
            $webclient.UploadFile($ftpUri, $file.FullName)
            $webclient.Dispose()
            
            Write-Host "Successfully uploaded: $($file.Name)" -ForegroundColor Green
        }
        catch {
            Write-Host "Upload failed: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
        }
        Start-Sleep -Milliseconds 200
    }
} else {
    Write-Host "demo_json_a directory does not exist: $aLocalDir" -ForegroundColor Yellow
}

# Check demo_json_b directory
$zyLocalDir = Join-Path $LocalBasePath "demo_json_b"
if (Test-Path $zyLocalDir) {
    $zyFiles = Get-ChildItem -Path $zyLocalDir -Filter "*.json" -File
    Write-Host "Found $($zyFiles.Count) demo_json_b files"
    
    foreach ($file in $zyFiles) {
        try {
            $ftpUri = "ftp://$FtpServer/companies/demo_json_b/$($file.Name)"
            Write-Host "Uploading: $($file.Name)"
            
            $webclient = New-Object System.Net.WebClient
            $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
            $webclient.UploadFile($ftpUri, $file.FullName)
            $webclient.Dispose()
            
            Write-Host "Successfully uploaded: $($file.Name)" -ForegroundColor Green
        }
        catch {
            Write-Host "Upload failed: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
        }
        Start-Sleep -Milliseconds 200
    }
} else {
    Write-Host "demo_json_b directory does not exist: $zyLocalDir" -ForegroundColor Yellow
}

Write-Host "Sync completed!"