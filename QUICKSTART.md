# 🚀 Quick Start Guide

Get Astro-Zoom running in under 5 minutes!

## Prerequisites Check

```bash
node --version  # Should be 20+
python3 --version  # Should be 3.11+
```

## Installation

```bash
# 1. Install dependencies
pnpm install

# 2. Install Python packages
pip install -r apps/api/requirements.txt
pip install -r apps/ai/requirements.txt

# 3. Generate sample tiles (already done if you ran setup.sh)
python3 infra/generate_sample_tiles.py

# 4. Build shared packages
pnpm -r build --filter=@astro-zoom/proto --filter=@astro-zoom/ui
```

## Start Development

```bash
# Start all services
pnpm dev
```

This runs:

- Web app on http://localhost:3000
- API on http://localhost:8000
- AI service on http://localhost:8001

## Verify It Works

1. Open http://localhost:3000
2. Click on "Andromeda Galaxy (Sample)"
3. You should see a deep-zoom star field!
4. Try:
   - Press `3` to enter Annotate mode
   - Click to create a point
   - Click twice to create a rectangle
   - Refresh page - annotation persists!

## Quick Test

```bash
# Test API
curl http://localhost:8000/health

# Test AI
curl http://localhost:8001/health

# Test datasets
curl http://localhost:8000/datasets

# Test search
curl "http://localhost:8000/search?q=star&datasetId=andromeda"
```

## Docker Alternative

```bash
cd infra
docker compose up --build
```

Wait ~30 seconds, then visit http://localhost:3000

## Troubleshooting

**Ports in use?**

```bash
# Kill processes on ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
```

**Module not found?**

```bash
# Rebuild packages
pnpm clean
pnpm install
pnpm -r build
```

**Tiles not loading?**

```bash
# Regenerate tiles
python3 infra/generate_sample_tiles.py
```

## Next Steps

- Read [README.md](README.md) for full documentation
- Explore the code in `apps/web/src/components/`
- Add your own datasets (see README)
- Deploy to production

Happy hacking! 🌌
