@echo off
echo ========================================
echo 立即同步所有JSON文件
echo ========================================
cd /d "C:\Projects\Demo"

echo 正在上传所有demo_json_a文件...
for %%f in (cloud\demo_json_a\*.json) do (
    echo 上传: %%~nxf
    powershell -Command "$w=New-Object System.Net.WebClient;$w.Credentials=New-Object System.Net.NetworkCredential('your_ftp_username','[REDACTED-FTP-PASSWORD]');try{$w.UploadFile('ftp://192.0.2.100/companies/demo_json_a/%%~nxf','%%f');Write-Host 'OK'}catch{Write-Host 'FAIL'};$w.Dispose()" 2>nul
)

echo.
echo 正在上传所有demo_json_b文件...
for %%f in (cloud\demo_json_b\*.json) do (
    echo 上传: %%~nxf
    powershell -Command "$w=New-Object System.Net.WebClient;$w.Credentials=New-Object System.Net.NetworkCredential('your_ftp_username','[REDACTED-FTP-PASSWORD]');try{$w.UploadFile('ftp://192.0.2.100/companies/demo_json_b/%%~nxf','%%f');Write-Host 'OK'}catch{Write-Host 'FAIL'};$w.Dispose()" 2>nul
)

echo.
echo 同步完成！按任意键退出...
pause >nul