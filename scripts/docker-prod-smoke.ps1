param(
  [string]$EnvFile = ".env.production.example"
)

$ErrorActionPreference = "Stop"

Push-Location "$PSScriptRoot\..\frontend"
try {
  npm ci --no-audit --no-fund
  npm run build
}
finally {
  Pop-Location
}

docker compose --env-file $EnvFile -f docker-compose.prod.yml build
docker compose --env-file $EnvFile -f docker-compose.prod.yml up -d postgres backend frontend
Start-Sleep -Seconds 12
.\scripts\smoke-test.ps1 -BackendUrl "http://127.0.0.1:8000" -FrontendUrl "http://127.0.0.1:8080"
