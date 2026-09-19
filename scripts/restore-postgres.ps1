param(
  [Parameter(Mandatory = $true)][string]$DatabaseUrl,
  [Parameter(Mandatory = $true)][string]$BackupPath
)

$ErrorActionPreference = "Stop"
pg_restore --clean --if-exists --dbname=$DatabaseUrl $BackupPath
Write-Output "Backup restored from $BackupPath"
