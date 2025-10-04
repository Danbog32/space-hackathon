# Starting Astro-Zoom Services

## Quick Start

The easiest way to start all services:

```bash
pnpm dev
```

This starts:

- **Web app** (Next.js) on http://localhost:3000
- **API server** (FastAPI) on http://localhost:8000
- **AI service** (CLIP search) on http://localhost:8001

## Manual Start (Individual Services)

If you need to start services individually:

### 1. API Server (Required)

```bash
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Web App (Required)

```bash
cd apps/web
pnpm dev
```

### 3. AI Service (Optional - for search)

```bash
cd apps/ai
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Verification

Check that services are running:

```bash
# API Health Check
curl http://localhost:8000/health

# Datasets Endpoint
curl http://localhost:8000/datasets

# Web App
open http://localhost:3000
```

## Common Issues

### "Failed to fetch datasets"

**Problem:** API server is not running  
**Solution:** Start the API server (see above)

```bash
cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Port Already in Use

**Problem:** Port 8000 or 3000 is already in use  
**Solution:** Kill the existing process

```bash
# Find process on port 8000
lsof -ti:8000 | xargs kill -9

# Find process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database Not Found

**Problem:** `astro.db` doesn't exist  
**Solution:** The database is created automatically on first startup

If you need to reset it:

```bash
rm data/astro.db
# Restart API server - it will recreate and seed
```

### Real Tiles Not Showing

**Problem:** Still seeing 1024x1024 mock tiles  
**Solution:** Generate real tiles

```bash
pip install -r infra/requirements_tiling.txt
python infra/process_real_image.py
```

## Service Dependencies

- **Web app** → Requires API server
- **API server** → Standalone (creates DB on startup)
- **AI service** → Optional (search uses stub if not running)

## Development Workflow

### Normal Development

```bash
# Terminal 1: Start all services
pnpm dev

# Edit code - services auto-reload
```

### API Development Only

```bash
# Terminal 1: API server
cd apps/api
uvicorn app.main:app --reload --port 8000

# Terminal 2: Test endpoints
curl http://localhost:8000/docs  # OpenAPI docs
```

### Frontend Development Only

```bash
# Terminal 1: Make sure API is running
cd apps/api && uvicorn app.main:app --reload --port 8000

# Terminal 2: Web app
cd apps/web
pnpm dev
```

## Production

For production deployment:

```bash
cd infra
docker compose up --build -d
```

Services will be available at:

- Web: http://localhost:3000
- API: http://localhost:8000 (+ /docs)
- AI: http://localhost:8001

## Logs

### View API Logs

If running with `pnpm dev`, logs appear in terminal.

For Docker:

```bash
docker compose logs -f api
```

### View Web Logs

```bash
# Check terminal where pnpm dev is running
# Or for Docker:
docker compose logs -f web
```

## Status Check

Quick status check of all services:

```bash
# API
curl -s http://localhost:8000/health | jq

# Web (returns HTML)
curl -s http://localhost:3000 | grep "Astro-Zoom"

# AI (if running)
curl -s http://localhost:8001/health | jq
```

## Current Status

✅ **API Server:** Running on port 8000  
✅ **Database:** Seeded with NASA Andromeda dataset (42208x9870)  
✅ **Tiles:** Available at /tiles/andromeda  
✅ **Web App:** Should now load datasets successfully

## Next Steps

1. Refresh your browser at http://localhost:3000
2. You should now see "Andromeda Galaxy (NASA Hubble 2025)"
3. Click to open the viewer
4. Zoom in to see the incredible detail!

## Troubleshooting Commands

```bash
# Check what's running
ps aux | grep -E "(uvicorn|next)" | grep -v grep

# Check ports
lsof -i :8000  # API
lsof -i :3000  # Web

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/datasets
curl http://localhost:8000/tiles/andromeda/info.dzi

# Check database
ls -lh data/astro.db

# Check tiles
ls -R infra/tiles/andromeda/ | head -20
```
