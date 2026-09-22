param(
  [Parameter(Mandatory = $true)][string]$AwsAccountId,
  [Parameter(Mandatory = $true)][string]$Region,
  [Parameter(Mandatory = $true)][string]$BackendRepository,
  [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

aws ecr get-login-password --region $Region |
  docker login --username AWS --password-stdin "$AwsAccountId.dkr.ecr.$Region.amazonaws.com"

docker build -f backend/Dockerfile -t "$BackendRepository`:$Tag" .
docker push "$BackendRepository`:$Tag"

Write-Output "Backend image pushed for EC2: $BackendRepository`:$Tag"
Write-Output "Deploy frontend with scripts/deploy-frontend-s3.ps1 after Terraform creates S3 and CloudFront."
