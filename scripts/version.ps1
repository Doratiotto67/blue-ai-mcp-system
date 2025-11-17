param(
    [ValidateSet("major","minor","patch")]
    [string]$Bump = "patch"
)
$path = "VERSION"
if (-not (Test-Path $path)) { "0.1.0" | Set-Content -Encoding UTF8 $path }
$ver = (Get-Content $path -Raw).Trim()
$parts = $ver.Split('.')
$maj = [int]$parts[0]; $min = [int]$parts[1]; $pat = [int]$parts[2]
switch ($Bump) { "major" { $maj++; $min=0; $pat=0 } "minor" { $min++; $pat=0 } default { $pat++ } }
$new = "$maj.$min.$pat"
$new | Set-Content -Encoding UTF8 $path
if (Test-Path ".git") { git tag -a ("v" + $new) -m ("Release v" + $new) | Out-Null }
Write-Host "Versão atualizada para $new"