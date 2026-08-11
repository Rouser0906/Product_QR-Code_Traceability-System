@echo off
REM 删除超过3年的 JSON 文件，记录日志
setlocal EnableExtensions

set "LOGDIR=C:\inetpub\qr-system\companies\_logs"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

REM 使用 PowerShell 执行删除逻辑
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop';" ^
 "$Paths=@('C:\inetpub\qr-system\companies\demo_json_a','C:\inetpub\qr-system\companies\demo_json_b');" ^
 "$threshold=(Get-Date).AddYears(-3);" ^
 "$logDir='%LOGDIR%'; if(-not (Test-Path $logDir)){New-Item -ItemType Directory -Path $logDir|Out-Null};" ^
 "$logFile=Join-Path $logDir ('cleanup_'+(Get-Date -Format 'yyyyMMdd')+'.log');" ^
 "('['+(Get-Date -Format u)+'] Cleanup start. Threshold: '+$threshold) | Out-File -Append -FilePath $logFile -Encoding utf8;" ^
 "foreach($p in $Paths){ if(Test-Path $p){ Get-ChildItem -Path $p -File -Filter '*.json' -Recurse | Where-Object {$_.LastWriteTime -lt $threshold} | ForEach-Object { try { Remove-Item -LiteralPath $_.FullName -Force; ('['+(Get-Date -Format u)+'] Deleted: '+$_.FullName) | Out-File -Append -FilePath $logFile -Encoding utf8 } catch { ('['+(Get-Date -Format u)+'] Failed: '+$_.FullName+' - '+$_.Exception.Message) | Out-File -Append -FilePath $logFile -Encoding utf8 } } } };" ^
 "('['+(Get-Date -Format u)+'] Cleanup completed.') | Out-File -Append -FilePath $logFile -Encoding utf8"

endlocal
