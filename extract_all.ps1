# CeresPINN - Extraccion de datos completa (LIVE / network)
#
# Descarga CHIRPS + NASA NEX-GDDP + USDA NASS en modo real (no dry-run).
# Los archivos se escriben en backend/data/raw/ (git-ignored).
#
# Requisitos:
#   1) (NASS) Obtener una API key gratuita: https://quickstats.nass.usda.gov/api
#   2) Crear backend/data/.env a partir del .env.example y pegar la key.
#   3) Tener el venv activado o usar .venv\Scripts\python.exe (default).
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File extract_all.ps1
#   powershell -ExecutionPolicy Bypass -File extract_all.ps1   (acepta NASS key argument)

param(
    [string]$NassKey = "",
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$envFile = Join-Path $root "backend\data\.env"
$python = if ($Python) { $Python } else { Join-Path $root ".venv\Scripts\python.exe" }

# --- Cargar .env manual (sin dependencias) ---
function Load-EnvFile([string]$path) {
    if (-not (Test-Path $path)) { return $false }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line -split "=", 2
            $key = $parts[0].Trim()
            $val = $parts[1].Trim().Trim('"').Trim("'")
            Set-Item -Path "Env:$key" -Value $val
        }
    }
    return $true
}

$loaded = Load-EnvFile $envFile

# --- Resolver la NASS key: parametro > .env > variable de entorno ---
if ($NassKey) { $env:NASS_API_KEY = $NassKey }
if (-not $env:NASS_API_KEY) {
    Write-Host ""
    Write-Host "ERROR: Falta NASS_API_KEY." -ForegroundColor Red
    Write-Host "  - Registrate gratis en: https://quickstats.nass.usda.gov/api"
    Write-Host "  - Luego:  Copy-Item backend/data/.env.example backend/data/.env   y pega tu key."
    Write-Host "  - O pasa la key como argumento:  .\extract_all.ps1 -NassKey TU-KEY"
    exit 1
}

Write-Host ""
Write-Host "CeresPINN - Extraccion LIVE de datos" -ForegroundColor Cyan
Write-Host ("  Python        : " + $python)
Write-Host ("  NASS_API_KEY  : " + $env:NASS_API_KEY.Substring(0,6) + "... (cargada)")
Write-Host ("  data dir      : " + (Join-Path $root "backend\data\raw"))
Write-Host ("  dry-run OFF   : si, descarga real")
Write-Host ""

# --- Forzar modo LIVE (nunca dry-run) ---
$env:CERESPINN_DRY_RUN = "0"
$env:CERESPINN_DATA_DIR = Join-Path $root "backend\data"

# --- Ejecutar cada pipeline en LIVE ---
$pipelines = @("all")
foreach ($p in $pipelines) {
    Write-Host ">>> lanzando: python -m backend.data.extractors $p" -ForegroundColor Yellow
    & $python -m backend.data.extractors $p
    if ($LASTEXITCODE -ne 0) {
        Write-Host ("Pipeline '" + $p + "' termino con error (exit " + $LASTEXITCODE + ").") -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Listo. Revisa los archivos en backend/data/raw/ y los manifests." -ForegroundColor Green