# Fixed JSON File Monitor - Clean Version

# Configuration
$LocalHS = 'C:\Projects\Demo\cloud\demo_json_a'
$LocalZY = 'C:\Projects\Demo\cloud\demo_json_b'
$FtpHost = 'scan.example.com'
$FtpPort = 21
$Username = 'your_ftp_username'
$Password = '[REDACTED-FTP-PASSWORD]'
$RemoteHS = '/companies/demo_json_a'
$RemoteZY = '/companies/demo_json_b'

function Upload-JsonFile($localFile, $remoteDir) {
    try {
        $fileName = Split-Path $localFile -Leaf
        $remoteUrl = "ftp://${FtpHost}:${FtpPort}${remoteDir}/${fileName}"
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Uploading: $fileName" -ForegroundColor Yellow
        
        $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
        $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $req.UsePassive = $true
        $req.UseBinary = $true
        $req.Timeout = 30000
        
        $fileContent = [System.IO.File]::ReadAllBytes($localFile)
        $req.ContentLength = $fileContent.Length
        
        $stream = $req.GetRequestStream()
        $stream.Write($fileContent, 0, $fileContent.Length)
        $stream.Close()
        
        $response = $req.GetResponse()
        $response.Close()
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] SUCCESS: $fileName uploaded" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ERROR: $fileName - $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Track processed files
$processedFiles = @{}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] JSON Monitor Started" -ForegroundColor Green
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Monitoring HS: $LocalHS" -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Monitoring ZY: $LocalZY" -ForegroundColor Cyan
Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Get existing files to avoid re-uploading
if (Test-Path $LocalHS) {
    Get-ChildItem -Path $LocalHS -Filter "*.json" -File | ForEach-Object {
        $processedFiles[$_.FullName] = $_.LastWriteTime
    }
}
if (Test-Path $LocalZY) {
    Get-ChildItem -Path $LocalZY -Filter "*.json" -File | ForEach-Object {
        $processedFiles[$_.FullName] = $_.LastWriteTime
    }
}

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Monitoring started..." -ForegroundColor Green

# Main monitoring loop
while ($true) {
    try {
        $foundNewFile = $false
        
        # Check HS directory
        if (Test-Path $LocalHS) {
            $hsFiles = Get-ChildItem -Path $LocalHS -Filter "*.json" -File
            foreach ($file in $hsFiles) {
                if (-not $processedFiles.ContainsKey($file.FullName) -or $processedFiles[$file.FullName] -lt $file.LastWriteTime) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] New HS file: $($file.Name)" -ForegroundColor Yellow
                    
                    Start-Sleep -Seconds 2
                    
                    if (Upload-JsonFile $file.FullName $RemoteHS) {
                        $processedFiles[$file.FullName] = $file.LastWriteTime
                        $foundNewFile = $true
                    }
                }
            }
        }
        
        # Check ZY directory
        if (Test-Path $LocalZY) {
            $zyFiles = Get-ChildItem -Path $LocalZY -Filter "*.json" -File
            foreach ($file in $zyFiles) {
                if (-not $processedFiles.ContainsKey($file.FullName) -or $processedFiles[$file.FullName] -lt $file.LastWriteTime) {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] New ZY file: $($file.Name)" -ForegroundColor Yellow
                    
                    Start-Sleep -Seconds 2
                    
                    if (Upload-JsonFile $file.FullName $RemoteZY) {
                        $processedFiles[$file.FullName] = $file.LastWriteTime
                        $foundNewFile = $true
                    }
                }
            }
        }
        
        if (-not $foundNewFile) {
            if ((Get-Date).Second -eq 0) {
                Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Monitoring... (processed $($processedFiles.Count) files)" -ForegroundColor DarkGray
            }
        }
        
        Start-Sleep -Seconds 5
        
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Monitor error: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 10
    }
}