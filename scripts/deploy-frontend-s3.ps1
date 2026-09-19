param(
  [Parameter(Mandatory = $true)][string]$Bucket,
  [Parameter(Mandatory = $true)][string]$CloudFrontDistributionId,
  [string]$ApiBaseUrl,
  [string]$WsBaseUrl
)

$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
  if ($ApiBaseUrl) {
    $env:VITE_API_BASE_URL = $ApiBaseUrl
  }
  if ($WsBaseUrl) {
    $env:VITE_WS_BASE_URL = $WsBaseUrl
  }
  npm ci
  npm run build
  aws s3 sync .\dist "s3://$Bucket" --delete
  aws cloudfront create-invalidation --distribution-id $CloudFrontDistributionId --paths "/*"
  Write-Output "Frontend deployed to s3://$Bucket"
}
finally {
  Pop-Location
}
