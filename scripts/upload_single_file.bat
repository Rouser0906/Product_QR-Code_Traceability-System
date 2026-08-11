@echo off
echo 正在上传 HS-DEMO-000009379.json...
cd /d "C:\Projects\Demo"

powershell -Command "$webclient = New-Object System.Net.WebClient; $webclient.Credentials = New-Object System.Net.NetworkCredential('your_ftp_username', '[REDACTED-FTP-PASSWORD]'); try { $webclient.UploadFile('ftp://10.0.0.100/companies/demo_json_a/HS-DEMO-000009379.json', 'cloud\demo_json_a\HS-DEMO-000009379.json'); Write-Host 'SUCCESS: HS-DEMO-000009379.json uploaded!' -ForegroundColor Green } catch { Write-Host 'FAILED: ' $_.Exception.Message -ForegroundColor Red } finally { $webclient.Dispose() }"

echo.
pause