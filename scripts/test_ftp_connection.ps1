# Test FTP Connection Details

$FtpHost = 'scan.example.com'
$FtpPort = 21
$Username = 'your_ftp_username'
$Password = '[REDACTED-FTP-PASSWORD]'

Write-Host "=== FTP Connection Diagnostic ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Basic FTP Connection
Write-Host "1. Testing basic FTP connection..." -ForegroundColor Yellow
try {
    $testReq = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost`:$FtpPort/")
    $testReq.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
    $testReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
    $testReq.UsePassive = $true
    $testReq.Timeout = 10000
    
    $response = $testReq.GetResponse()
    $stream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $listing = $reader.ReadToEnd()
    $reader.Close()
    $response.Close()
    
    Write-Host "✓ FTP connection successful!" -ForegroundColor Green
    Write-Host "Directory listing:" -ForegroundColor Gray
    $listing -split "`n" | ForEach-Object { 
        if ($_.Trim()) { Write-Host "  $_" -ForegroundColor DarkGray }
    }
} catch {
    Write-Host "✗ FTP connection failed: $($_.Exception.Message)" -ForegroundColor Red
    
    # Try with different settings
    Write-Host ""
    Write-Host "2. Trying alternative FTP settings..." -ForegroundColor Yellow
    
    try {
        $testReq2 = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost`:$FtpPort/")
        $testReq2.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $testReq2.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $testReq2.UsePassive = $false  # Try active mode
        $testReq2.Timeout = 15000
        
        $response2 = $testReq2.GetResponse()
        $response2.Close()
        
        Write-Host "✓ FTP connection successful with active mode!" -ForegroundColor Green
    } catch {
        Write-Host "✗ Active mode also failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 2: Check specific directories
Write-Host ""
Write-Host "3. Testing access to target directories..." -ForegroundColor Yellow

$testDirs = @('/companies', '/companies/demo_json_a', '/companies/demo_json_b')

foreach ($dir in $testDirs) {
    try {
        $testReq = [System.Net.FtpWebRequest]::Create("ftp://$FtpHost`:$FtpPort$dir")
        $testReq.Method = [System.Net.WebRequestMethods+Ftp]::ListDirectory
        $testReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $testReq.UsePassive = $true
        $testReq.Timeout = 10000
        
        $response = $testReq.GetResponse()
        $response.Close()
        
        Write-Host "✓ Directory accessible: $dir" -ForegroundColor Green
    } catch {
        Write-Host "✗ Directory not accessible: $dir - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 3: Try uploading a small test file
Write-Host ""
Write-Host "4. Testing file upload..." -ForegroundColor Yellow

try {
    $testContent = "Test file created at $(Get-Date)"
    $testFileName = "test_upload_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    $remoteUrl = "ftp://$FtpHost`:$FtpPort/companies/demo_json_a/$testFileName"
    
    $req = [System.Net.FtpWebRequest]::Create($remoteUrl)
    $req.Method = [System.Net.WebRequestMethods+Ftp]::UploadFile
    $req.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
    $req.UsePassive = $true
    $req.UseBinary = $false  # Text mode for test
    
    $contentBytes = [System.Text.Encoding]::UTF8.GetBytes($testContent)
    $req.ContentLength = $contentBytes.Length
    
    $requestStream = $req.GetRequestStream()
    $requestStream.Write($contentBytes, 0, $contentBytes.Length)
    $requestStream.Close()
    
    $response = $req.GetResponse()
    $response.Close()
    
    Write-Host "✓ Test file upload successful: $testFileName" -ForegroundColor Green
    
    # Try to delete the test file
    try {
        $delReq = [System.Net.FtpWebRequest]::Create($remoteUrl)
        $delReq.Method = [System.Net.WebRequestMethods+Ftp]::DeleteFile
        $delReq.Credentials = New-Object System.Net.NetworkCredential($Username, $Password)
        $delReq.UsePassive = $true
        
        $delResponse = $delReq.GetResponse()
        $delResponse.Close()
        
        Write-Host "✓ Test file deleted successfully" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not delete test file (but upload worked)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "✗ File upload failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Diagnostic Complete ===" -ForegroundColor Cyan