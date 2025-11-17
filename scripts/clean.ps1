$ErrorActionPreference = "Stop"
docker-compose down
Write-Host "Serviços parados"
try { docker system prune -f | Out-Null } catch {}
try { docker volume prune -f | Out-Null } catch {}
Write-Host "Limpeza concluída"