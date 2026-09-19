param(
  [Parameter(Mandatory = $true)][string]$AwsAccountId,
  [Parameter(Mandatory = $true)][string]$Region,
  [Parameter(Mandatory = $true)][string]$BackendRepository,
  [Parameter(Mandatory = $true)][string]$FrontendRepository,
  [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

aws ecr get-login-password --region $Region |
  docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$Region.amazonaws.com"

docker build -f backend/Dockerfile -t "$BackendRepository`:$Tag" .

Push-Location "$PSScriptRoot\..\frontend"
try {
  npm ci --no-audit --no-fund
  npm run build
}
finally {
  Pop-Location
}

docker build -f frontend/Dockerfile.runtime -t "$FrontendRepository`:$Tag" .

docker push "$BackendRepository`:$Tag"
docker push "$FrontendRepository`:$Tag"

Write-Output "Images pushed: $BackendRepository`:$Tag, $FrontendRepository`:$Tag"
