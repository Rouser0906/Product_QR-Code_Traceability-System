Write-Host "Testing single file upload..."

$FtpServer = "10.0.0.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"
$LocalFile = "C:\Projects\Demo\cloud\demo_json_a\A-DEMO-000009374.json"
$RemoteFile = "ftp://10.0.0.100/companies/demo_json_a/A-DEMO-000009374.json"

try {
    Write-Host "Local file: $LocalFile"
    Write-Host "Remote URL: $RemoteFile"
    
    if (Test-Path $LocalFile) {
        Write-Host "Local file exists, starting upload..."
        
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
        $webclient.UploadFile($RemoteFile, $LocalFile)
        $webclient.Dispose()
        
        Write-Host "Upload successful!" -ForegroundColor Green
    } else {
        Write-Host "Local file does not exist!" -ForegroundColor Red
    }
} catch {
    Write-Host "Upload failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Test completed."