param(
  [string]$AwsProfile = "case-inteligente",
  [string]$InstanceId = "i-073dedc10a4f94d94"
)

$ErrorActionPreference = "Stop"
$pluginCandidates = @(
  (Join-Path $env:LOCALAPPDATA "case-session-manager-plugin\package\bin"),
  (Join-Path $env:ProgramFiles "Amazon\SessionManagerPlugin\bin")
)
$pluginBin = $pluginCandidates | Where-Object { Test-Path (Join-Path $_ "session-manager-plugin.exe") } | Select-Object -First 1
$awsBin = Join-Path $env:LOCALAPPDATA "Programs\Amazon\AWSCLIV2"
$key = Join-Path $env:LOCALAPPDATA "case-ia-tunnel\id_ed25519"
if ($pluginBin) { $env:PATH = "$pluginBin;$env:PATH" }
if (Test-Path (Join-Path $awsBin "aws.exe")) { $env:PATH = "$awsBin;$env:PATH" }

if (-not (Test-Path $key)) { throw "Falta la clave SSH del tunel: $key" }
if (-not (Get-Command aws.exe -ErrorAction SilentlyContinue)) { throw "Falta AWS CLI v2" }
if (-not (Get-Command session-manager-plugin.exe -ErrorAction SilentlyContinue)) {
  throw "Falta el plugin de AWS Session Manager. Instalalo desde AWS y vuelve a abrir PowerShell."
}
& aws.exe sts get-caller-identity --profile $AwsProfile --region us-east-1 --query Account --output text | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Inicia sesion con: aws login --profile $AwsProfile --region us-east-1" }

if (-not (docker info --format '{{.ServerVersion}}' 2>$null)) {
  Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 2
    if (docker info --format '{{.ServerVersion}}' 2>$null) { break }
  }
}
if (-not (docker info --format '{{.ServerVersion}}' 2>$null)) { throw "Docker no inicio" }
if (-not (docker container inspect case-ollama-local --format '{{.Id}}' 2>$null)) {
  throw "Falta el contenedor case-ollama-local. Crealo y descarga qwen2.5-coder:1.5b antes de iniciar el tunel."
}
docker start case-ollama-local | Out-Null

$proxy = "ProxyCommand=aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters portNumber=%p --profile $AwsProfile --region us-east-1"
while ($true) {
  & ssh.exe -o $proxy -o ExitOnForwardFailure=yes -o BatchMode=yes `
    -o ConnectTimeout=30 -o StrictHostKeyChecking=accept-new -i $key `
    -N -R "0.0.0.0:11435:127.0.0.1:11434" "case-ia-tunnel@$InstanceId"
  Write-Warning "El tunel de IA local se desconecto. Reintentando en 15 segundos."
  Start-Sleep -Seconds 15
}
