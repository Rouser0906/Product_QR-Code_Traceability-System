@echo off
echo Testing file upload to server...
cd /d "C:\Projects\Demo"

powershell -Command "try { $webclient = New-Object System.Net.WebClient; $webclient.Credentials = New-Object System.Net.NetworkCredential('your_ftp_username', '[REDACTED-FTP-PASSWORD]'); $webclient.UploadFile('ftp://10.0.0.100/companies/demo_json_a/HS-DEMO-000009374.json', 'cloud\demo_json_a\HS-DEMO-000009374.json'); $webclient.Dispose(); Write-Host 'Upload successful: HS-DEMO-000009374.json' -ForegroundColor Green } catch { Write-Host 'Upload failed:' $_.Exception.Message -ForegroundColor Red }"

echo.
echo Test completed. Press any key to exit...
pause >nul