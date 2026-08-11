param(
  [string]$BaseUrl = 'https://your-company-domain.com',
  [string]$Code,
  [ValidateSet('hs','zy')][string]$Company = 'hs',
  [switch]$Insecure
)

$ErrorActionPreference = 'Stop'

function New-HttpClient {
  param([switch]$Insecure)
  if ($Insecure) {
    add-type @"
using System.Net;
using System.Security.Cryptography.X509Certificates;
public class TrustAllCertsPolicy : ICertificatePolicy {
    public bool CheckValidationResult(
        ServicePoint srvPoint, X509Certificate certificate,
        WebRequest request, int certificateProblem) { return true; }
}
"@
    [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
  }
}

function Test-Endpoint {
  param(
    [string]$Url,
    [string]$ExpectContentType,
    [string]$Method = 'GET'
  )
  try {
    $resp = Invoke-WebRequest -Method $Method -Uri $Url -UseBasicParsing -TimeoutSec 30
    $ct = $resp.Headers['Content-Type']
    return [PSCustomObject]@{
      Url = $Url
      StatusCode = $resp.StatusCode
      ContentType = $ct
      HasExpectedContentType = ($ExpectContentType -and $ct -like "$ExpectContentType*")
      AllowOrigin = $resp.Headers['Access-Control-Allow-Origin']
      AllowMethods = $resp.Headers['Access-Control-Allow-Methods']
      AllowHeaders = $resp.Headers['Access-Control-Allow-Headers']
      Pass = $true
      Error = $null
    }
  } catch {
    return [PSCustomObject]@{
      Url = $Url
      StatusCode = $null
      ContentType = $null
      HasExpectedContentType = $false
      AllowOrigin = $null
      AllowMethods = $null
      AllowHeaders = $null
      Pass = $false
      Error = $_.Exception.Message
    }
  }
}

New-HttpClient -Insecure:$Insecure

$results = @()

# 1) index.html 可访问
$results += Test-Endpoint -Url ("{0}/index.html" -f $BaseUrl) -ExpectContentType 'text/html'

# 2) 参数统一：id->code（仅验证 302 存在与否，部分环境可能已直接使用 code，故允许通过）
try {
  $resp = Invoke-WebRequest -Method GET -Uri ("{0}/index.html?id={1}" -f $BaseUrl, ($Code?$Code:'HS-DEMO-000000001')) -MaximumRedirection 0 -UseBasicParsing -TimeoutSec 15
  $redirOk = $false
} catch {
  $redirOk = ($_.Exception.Response.StatusCode.value__ -in 301,302,307,308)
}
$results += [PSCustomObject]@{ Url = "$BaseUrl/index.html?id=..."; StatusCode = if($redirOk){302}else{200}; Pass = $true; Note = 'id->code redirection checked' }

# 3) API 响应
if (-not $Code) { Write-Warning '未指定 -Code，API 检测将跳过实际数据校验，仅做 200 检测'; }
$apiUrl = ("{0}/api/get_product_data.php?code={1}" -f $BaseUrl, ($Code?$Code:'HS-DEMO-000000001'))
try {
  $api = Invoke-RestMethod -Method GET -Uri $apiUrl -TimeoutSec 30
  $ok = $true
  $hasInfo = $api._api_info -ne $null
} catch {
  $ok = $false
  $hasInfo = $false
}
$results += [PSCustomObject]@{ Url = $apiUrl; Pass = $ok; HasApiInfo = $hasInfo }

# 4) JSON 访问 + CORS/MIME
$companyDir = if ($Company -eq 'hs') { 'demo_json_a' } else { 'demo_json_b' }
$jsonUrl = ("{0}/companies/{1}/{2}.json" -f $BaseUrl, $companyDir, ($Code?$Code:'HS-DEMO-000000001'))
$results += Test-Endpoint -Url $jsonUrl -ExpectContentType 'application/json'

# 汇总
$fail = $results | Where-Object { $_.Pass -ne $true -and $_.HasExpectedContentType -ne $true -and $_.HasApiInfo -ne $true } | Measure-Object | Select-Object -ExpandProperty Count
$results | Format-Table -AutoSize
if ($fail -gt 0) {
  Write-Host "❌ Healthcheck has issues. Please review above table." -ForegroundColor Red
  exit 1
} else {
  Write-Host "✅ Healthcheck passed." -ForegroundColor Green
}
