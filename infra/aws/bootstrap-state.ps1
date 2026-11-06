param(
  [Parameter(Mandatory = $true)][string]$Bucket,
  [Parameter(Mandatory = $true)][string]$Region
)

$ErrorActionPreference = 'Stop'

aws s3api head-bucket --bucket $Bucket 2>$null
if ($LASTEXITCODE -ne 0) {
  if ($Region -eq 'us-east-1') {
    aws s3api create-bucket --bucket $Bucket --region $Region | Out-Null
  } else {
    aws s3api create-bucket --bucket $Bucket --region $Region --create-bucket-configuration "LocationConstraint=$Region" | Out-Null
  }
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el bucket de estado' }
}

$block = @{ BlockPublicAcls = $true; IgnorePublicAcls = $true; BlockPublicPolicy = $true; RestrictPublicBuckets = $true } | ConvertTo-Json -Compress
aws s3api put-public-access-block --bucket $Bucket --public-access-block-configuration $block | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No se pudo bloquear el acceso publico' }
aws s3api put-bucket-versioning --bucket $Bucket --versioning-configuration 'Status=Enabled' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No se pudo activar el versionado' }
$encryption = @{ Rules = @(@{ ApplyServerSideEncryptionByDefault = @{ SSEAlgorithm = 'AES256' } }) } | ConvertTo-Json -Compress -Depth 5
aws s3api put-bucket-encryption --bucket $Bucket --server-side-encryption-configuration $encryption | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'No se pudo activar el cifrado' }

Write-Output "Bucket de estado preparado: $Bucket ($Region). Configure terraform init con -backend-config=bucket=$Bucket -backend-config=key=case-inteligente/staging/terraform.tfstate -backend-config=region=$Region"
