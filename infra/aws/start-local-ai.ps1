param(
  [string]$AwsProfile = "case-inteligente",
  [string]$InstanceId = "i-073dedc10a4f94d94"
)

$ErrorActionPreference = "Stop"
$pluginBin = Join-Path $env:LOCALAPPDATA "case-session-manager-plugin\package\bin"
$awsBin = Join-Path $env:LOCALAPPDATA "Programs\Amazon\AWSCLIV2"
$key = Join-Path $env:LOCALAPPDATA "case-ia-tunnel\id_ed25519"
$env:PATH = "$pluginBin;$awsBin;$env:PATH"

if (-not (Test-Path $key)) { throw "Falta la clave SSH del tunel: $key" }
if (-not (Test-Path (Join-Path $pluginBin "session-manager-plugin.exe"))) {
  throw "Falta el plugin de AWS Session Manager"
}

if (-not (docker info --format '{{.ServerVersion}}' 2>$null)) {
  Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Seconds 2
    if (docker info --format '{{.ServerVersion}}' 2>$null) { break }
  }
}
if (-not (docker info --format '{{.ServerVersion}}' 2>$null)) { throw "Docker no inicio" }
docker start case-ollama-local | Out-Null

$proxy = "ProxyCommand=aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters portNumber=%p --profile $AwsProfile --region us-east-1"
while ($true) {
  & ssh.exe -o $proxy -o ExitOnForwardFailure=yes -o BatchMode=yes `
    -o ConnectTimeout=30 -o StrictHostKeyChecking=accept-new -i $key `
    -N -R "0.0.0.0:11435:127.0.0.1:11434" "case-ia-tunnel@$InstanceId"
  Write-Warning "El tunel de IA local se desconecto. Reintentando en 15 segundos."
  Start-Sleep -Seconds 15
}
