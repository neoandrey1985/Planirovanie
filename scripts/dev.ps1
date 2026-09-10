# Планирование спринтов — helper для Windows. Пример: ./scripts/dev.ps1 up
param([string]$cmd = "up")

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

switch ($cmd) {
    "up"    { docker compose up --build }
    "up-d"  { docker compose up -d --build }
    "down"  { docker compose down }
    "clean" { docker compose down -v }
    "logs"  { docker compose logs -f }
    "ps"    { docker compose ps }
    "build" { docker compose build }
    "test"  {
        Push-Location backend-java; mvn -B -ntp test; $j = $LASTEXITCODE; Pop-Location
        python analytics-python/tests/test_compute.py; $p = $LASTEXITCODE
        if ($j -ne 0 -or $p -ne 0) { exit 1 }
    }
    "seed"  { python scripts/gen_initsql.py }
    default { Write-Host "Usage: ./scripts/dev.ps1 [up|up-d|down|clean|logs|ps|build|test|seed]" }
}
