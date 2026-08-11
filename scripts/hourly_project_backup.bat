@echo off
REM 每小时项目备份（压缩为 zip）。可直接运行，或由计划任务调用。
setlocal EnableExtensions EnableDelayedExpansion

REM 推导默认路径：项目根=脚本所在目录的上级
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\") do set "PROJECT_ROOT=%%~fI"
set "BACKUP_DIR=%PROJECT_ROOT%backups"

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM 使用 PowerShell 执行备份（排除无关目录与文件）
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ErrorActionPreference='Stop';" ^
 "$ProjectRoot='%PROJECT_ROOT%'; $BackupDir='%BACKUP_DIR%';" ^
 "$ts=Get-Date -Format 'yyyyMMdd_HHmmss'; $zip=Join-Path $BackupDir ('project_backup_'+$ts+'.zip');" ^
 "$exDirs=@('.git','.venv','scripts\\venv','node_modules','logs','cache','backups','tmp_dev_trash_*');" ^
 "$exFiles=@('*.db-wal','*.db-shm','*.tmp','*.bak');" ^
 "$tmp=Join-Path $env:TEMP ('tmp_dev_backup_'+$ts); if(Test-Path $tmp){Remove-Item -Recurse -Force $tmp}; New-Item -ItemType Directory -Path $tmp|Out-Null;" ^
 "Get-ChildItem -Path $ProjectRoot -Recurse -Force | ForEach-Object { $rel=$_.FullName.Substring($ProjectRoot.Length).TrimStart('\\','/'); foreach($d in $exDirs){ if($rel -like "$d*" -or $rel -like "*\$d*" -or $rel -eq $d){ return } }; foreach($f in $exFiles){ if($_.Name -like $f){ return } }; if($_.PSIsContainer){ $o=Join-Path $tmp $rel; if(-not (Test-Path $o)){New-Item -ItemType Directory -Path $o|Out-Null} } else { $o=Join-Path $tmp $rel; $od=Split-Path $o; if(-not (Test-Path $od)){New-Item -ItemType Directory -Path $od|Out-Null}; Copy-Item -LiteralPath $_.FullName -Destination $o -Force } }" ^
 "if(Test-Path $zip){ Remove-Item -Force $zip }; Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zip -Force; Remove-Item -Recurse -Force $tmp;" ^
 "Write-Output ('[OK] Backup created: '+$zip)"

endlocal
