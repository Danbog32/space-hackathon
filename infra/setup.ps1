Param()

Write-Host "🌌 Astro-Zoom Setup Script (Windows)" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Ensure we run from repo root
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$SCRIPT_DIR\.." | Out-Null

# Check dependencies
function Assert-Command($cmd, $help) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Error "❌ $cmd not found. $help"
    exit 1
  }
}

Assert-Command node "Please install Node.js 20+"
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
  Write-Host "pnpm not found. Installing..."
  npm install -g pnpm@8.15.0
}
Assert-Command python "Please install Python 3.11+ and ensure 'python' is on PATH"

Write-Host "✓ All required tools found"

# Install Node deps
Write-Host "Installing Node.js dependencies..."
pnpm install
Write-Host "✓ Node.js dependencies installed"

# Install Python deps
Write-Host "Installing Python dependencies..."
Push-Location apps/api
python -m pip install -r requirements.txt
Pop-Location

Push-Location apps/ai
python -m pip install -r requirements.txt
Pop-Location

python -m pip install -r infra/requirements_tiling.txt
Write-Host "✓ Python dependencies installed"

# Ensure datasets
Write-Host "Ensuring default datasets (Andromeda & Earth)..."
python infra/ensure_datasets.py
Write-Host "✓ Datasets ready"

# Build packages
Write-Host "Building shared packages..."
pnpm -r build --filter=@astro-zoom/proto --filter=@astro-zoom/ui
Write-Host "✓ Packages built"

# Create .env if missing
if (-not (Test-Path .env)) {
  @"
NODE_ENV=development
API_URL=http://localhost:8000
AI_URL=http://localhost:8001
NEXT_PUBLIC_API_URL=http://localhost:8000
TILE_BASE=file://infra/tiles
JWT_SECRET=devsecret_change_in_production_please
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600
DATABASE_URL=sqlite:///data/astro.db
RATE_LIMIT_SEARCH=10/minute
"@ | Set-Content .env -Encoding UTF8
  Write-Host "✓ .env file created"
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start development:"
Write-Host "  pnpm dev"
