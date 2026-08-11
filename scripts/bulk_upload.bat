@echo off
echo ========================================
echo Bulk Upload JSON Files to Server
echo ========================================
cd /d "C:\Projects\Demo"

echo Uploading demo_json_a files...
for %%f in (cloud\demo_json_a\*.json) do (
    echo Uploading %%~nxf...
    powershell -Command "$webclient = New-Object System.Net.WebClient; $webclient.Credentials = New-Object System.Net.NetworkCredential('your_ftp_username', '[REDACTED-FTP-PASSWORD]'); try { $webclient.UploadFile('ftp://10.0.0.100/companies/demo_json_a/%%~nxf', '%%f'); Write-Host 'OK: %%~nxf' } catch { Write-Host 'FAIL: %%~nxf' }; $webclient.Dispose()"
)

echo.
echo Uploading demo_json_b files...
for %%f in (cloud\demo_json_b\*.json) do (
    echo Uploading %%~nxf...
    powershell -Command "$webclient = New-Object System.Net.WebClient; $webclient.Credentials = New-Object System.Net.NetworkCredential('your_ftp_username', '[REDACTED-FTP-PASSWORD]'); try { $webclient.UploadFile('ftp://10.0.0.100/companies/demo_json_b/%%~nxf', '%%f'); Write-Host 'OK: %%~nxf' } catch { Write-Host 'FAIL: %%~nxf' }; $webclient.Dispose()"
)

echo.
echo Upload completed! Press any key to exit...
pause >nul