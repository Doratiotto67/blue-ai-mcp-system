param(
    [Parameter(Mandatory=$true)][string]$Url,
    [switch]$Push
)
$ErrorActionPreference = "Stop"
try {
    $existing = git remote
    if ($existing -match "origin") { git remote remove origin }
    git remote add origin $Url
    Write-Host "Remote 'origin' configured: $Url"
    if ($Push) {
        git push -u origin main
        Write-Host "Pushed branch 'main' to remote"
    }
} catch {
    Write-Host "Failed to configure remote: $($_.Exception.Message)"; exit 1
}