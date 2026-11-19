param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$pythonExecutable = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw 'Create .venv and install requirements.txt first. See README.md.'
}
if (-not (Test-Path -LiteralPath 'frontend/dist/index.html')) {
    throw 'Build the frontend first: cd frontend; npm ci; npm run build.'
}

& $pythonExecutable -m uvicorn backend.main:app --host 127.0.0.1 --port $Port --workers 1
