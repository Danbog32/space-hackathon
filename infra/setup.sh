#!/bin/bash
# Setup script for Astro-Zoom development environment

set -e

echo "🌌 Astro-Zoom Setup Script"
echo "=========================="
echo ""

# Check for required tools
echo "Checking dependencies..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 20+"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "❌ pnpm not found. Installing..."
    npm install -g pnpm@8.15.0
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

echo "✓ All required tools found"
echo ""

# Install Node dependencies
echo "Installing Node.js dependencies..."
pnpm install
echo "✓ Node.js dependencies installed"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."

cd apps/api
pip install -r requirements.txt
cd ../..

cd apps/ai
pip install -r requirements.txt
cd ../..

echo "✓ Python dependencies installed"
echo ""

# Generate sample tiles
echo "Generating sample tile data..."
python3 infra/generate_sample_tiles.py
echo "✓ Sample tiles generated"
echo ""

# Build packages
echo "Building shared packages..."
pnpm -r build --filter=@astro-zoom/proto --filter=@astro-zoom/ui
echo "✓ Packages built"
echo ""

# Copy .env.example if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cat > .env << 'EOF'
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
EOF
    echo "✓ .env file created"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start development:"
echo "  pnpm dev          - Run all services with Turborepo"
echo "  docker compose up - Run with Docker (in infra/ directory)"
echo ""
echo "Services will be available at:"
echo "  Web:  http://localhost:3000"
echo "  API:  http://localhost:8000"
echo "  AI:   http://localhost:8001"
echo ""

