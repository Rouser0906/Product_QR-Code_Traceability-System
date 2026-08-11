# ??????
$ProjectRoot = "C:\Projects\Demo"
Set-Location $ProjectRoot

# ??????
$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*windows_ftp_json_uploader*" }
if ($procs.Count -eq 0) {
    try {
        [Console]::Beep(1000, 500)
        Write-EventLog -LogName Application -Source "Application" -EventId 1001 -EntryType Warning -Message "AutoSync Alert: ???????? $(Get-Date)"
    } catch {}
}

# ???????
$logFile = "auto_sync\logs\ftp_uploader.log"
if (Test-Path $logFile) {
    $lastWrite = (Get-Item $logFile).LastWriteTime
    $age = ((Get-Date) - $lastWrite).TotalMinutes
    if ($age -gt 20) {
        try {
            [Console]::Beep(800, 300)
            Write-EventLog -LogName Application -Source "Application" -EventId 1002 -EntryType Warning -Message "AutoSync Alert: ???? $([math]::Round($age, 1)) ????? $(Get-Date)"
        } catch {}
    }
}

# ??????
try {
    $drive = Get-PSDrive -Name "D"
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeSpaceGB -lt 2) {
        [Console]::Beep(1200, 800)
        Write-EventLog -LogName Application -Source "Application" -EventId 1003 -EntryType Error -Message "AutoSync Alert: ?????? ${freeSpaceGB}GB $(Get-Date)"
    }
} catch {}
