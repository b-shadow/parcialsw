param(
  [Parameter(Mandatory = $true)][string]$InstanceId,
  [Parameter(Mandatory = $true)][string]$Region,
  [Parameter(Mandatory = $true)][string]$BackendImage
)

$ErrorActionPreference = "Stop"

$registry = $BackendImage.Split("/")[0]
$commands = @(
  "aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $registry",
  "docker pull $BackendImage",
  "docker rm -f case-inteligente-backend || true",
  "docker run -d --name case-inteligente-backend --restart unless-stopped --env-file /opt/case-inteligente/backend.env -p 8000:8000 -v case_generated_artifacts:/storage/generated $BackendImage",
  "docker ps --filter name=case-inteligente-backend"
)
$parameters = @{ commands = $commands } | ConvertTo-Json -Compress

$command = aws ssm send-command `
  --region $Region `
  --instance-ids $InstanceId `
  --document-name "AWS-RunShellScript" `
  --comment "Refresh CASE Inteligente backend container" `
  --parameters $parameters `
  --query "Command.CommandId" `
  --output text

Write-Output "SSM command sent: $command"
Write-Output "Check result with:"
Write-Output "aws ssm list-command-invocations --region $Region --command-id $command --details"
