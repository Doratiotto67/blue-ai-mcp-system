$envFileExists = Test-Path .env
if (-not $envFileExists) { Copy-Item .env.example .env }
$envContent = Get-Content .env -Raw
$ok = $true
if ($envContent -notmatch "OPENROUTER_API_KEY\s*=\s*\S+") { Write-Host "OPENROUTER_API_KEY ausente ou vazio"; $ok = $false }
if ($envContent -notmatch "LOG_LEVEL\s*=\s*\S+") { Write-Host "LOG_LEVEL ausente ou vazio"; $ok = $false }
if ($ok) { Write-Host "Ambiente configurado" } else { exit 1 }