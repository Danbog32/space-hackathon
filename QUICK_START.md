# 🚀 Quick Start

Get Astro-Zoom running in 3 steps.

## Prerequisites

- Node.js 20+
- Python 3.11+
- pnpm

## Install & Start

```bash
# 1. Install dependencies
pnpm install
pip install -r apps/api/requirements.txt
pip install -r ai/requirements.txt

# 2. Build AI data
cd ai && python simple_build.py && cd ..

# 3. Start all services
pnpm dev
```

## Verify

Open http://localhost:3000

- ✅ Web app loads
- ✅ Select "Andromeda Galaxy"
- ✅ Try AI features:
  - Press `3` → "Rectangle + AI Classify" → Draw rectangle
  - Left panel → "🎯 Object Detection" → Type "star" → "Detect Objects"
  - Left panel → "AI Search" → Type "bright region" → "Search"

## Services

| Service  | Port | Purpose                    |
| -------- | ---- | -------------------------- |
| Frontend | 3000 | Web UI                     |
| API      | 8000 | Backend + Proxy            |
| AI       | 8001 | Classification & Detection |

## Troubleshooting

**Port in use?**

```bash
lsof -ti:3000,8000,8001 | xargs kill -9
```

**AI not working?**

```bash
cd ai && python simple_build.py
```

**Still broken?**

```bash
pnpm clean && pnpm install && pnpm -r build
```

That's it! 🌌
