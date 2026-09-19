param(
  [string]$BackendUrl = "http://127.0.0.1:8000",
  [string]$FrontendUrl = "http://127.0.0.1:5173"
)

$ErrorActionPreference = "Stop"

$health = Invoke-RestMethod "$BackendUrl/health"
if ($health.status -ne "ok") {
  throw "Backend health failed"
}

$openapi = Invoke-RestMethod "$BackendUrl/openapi.json"
$requiredPaths = @(
  "/api/v1/auth/login",
  "/api/v1/projects",
  "/api/v1/uml/diagrams",
  "/api/v1/generation/spring-boot",
  "/api/v1/generation/flutter",
  "/api/v1/ai/profile"
)

$paths = $openapi.paths.PSObject.Properties.Name
foreach ($path in $requiredPaths) {
  if ($paths -notcontains $path) {
    throw "Missing OpenAPI path $path"
  }
}

$frontend = Invoke-WebRequest -UseBasicParsing $FrontendUrl
if ($frontend.StatusCode -ne 200) {
  throw "Frontend smoke test failed"
}

Write-Output "Smoke test passed"
