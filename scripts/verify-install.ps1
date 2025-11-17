$services = @(
    "http://localhost:9080",
    "http://localhost:9081",
    "http://localhost:9082",
    "http://localhost:9083",
    "http://localhost:9084",
    "http://localhost:9086"
)
$results = @()
foreach ($s in $services) {
    $ok = $false
    try { $r = Invoke-WebRequest -Uri ($s + "/health") -UseBasicParsing -TimeoutSec 5; if ($r.StatusCode -eq 200) { $ok = $true } } catch {}
    $results += [PSCustomObject]@{ service = $s; healthy = $ok }
}
$smokeOk = $false
try { $qr = Invoke-WebRequest -Uri "http://localhost:9080/mcp/tools/quick_code?description=hello&language=python&style=minimal&stub=1" -UseBasicParsing -TimeoutSec 5; if ($qr.StatusCode -eq 200) { $smokeOk = $true } } catch {}
$report = [PSCustomObject]@{ health = $results; smoke = $smokeOk }
if (-not (Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
$report | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 "logs/test-runner-report.json"
$allHealthy = -not ($results | Where-Object { -not $_.healthy })
if ($allHealthy -and $smokeOk) { Write-Host "Instalação OK" } else { Write-Host "Falhas detectadas"; exit 1 }