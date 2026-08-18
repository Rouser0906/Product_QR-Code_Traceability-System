Write-Host "Testing upload of A-DEMO-000009379.json..." -ForegroundColor Yellow

$FtpServer = "192.0.2.100"
$FtpUser = "your_ftp_username"
$FtpPassword = "[REDACTED-FTP-PASSWORD]"
$LocalFile = "C:\Projects\Demo\cloud\demo_json_a\A-DEMO-000009379.json"
$RemoteUrl = "ftp://192.0.2.100/companies/demo_json_a/A-DEMO-000009379.json"

try {
    if (Test-Path $LocalFile) {
        Write-Host "Local file exists: $LocalFile" -ForegroundColor Green
        
        $webclient = New-Object System.Net.WebClient
        $webclient.Credentials = New-Object System.Net.NetworkCredential($FtpUser, $FtpPassword)
        $webclient.UploadFile($RemoteUrl, $LocalFile)
        $webclient.Dispose()
        
        Write-Host "SUCCESS: A-DEMO-000009379.json uploaded successfully!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Local file does not exist: $LocalFile" -ForegroundColor Red
    }
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "Test completed." -ForegroundColor Yellow