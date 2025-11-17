$ErrorActionPreference = "Stop"
& $PSScriptRoot\setup-env.ps1
try { docker --version | Out-Null } catch { Write-Host "Docker não instalado"; exit 1 }
try { docker-compose --version | Out-Null } catch { Write-Host "Docker Compose não instalado"; exit 1 }
docker-compose build
docker-compose up -d
Write-Host "Sistema iniciado"