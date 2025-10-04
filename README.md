# 🌌 Astro-Zoom

**Deep zoom viewer for gigantic NASA images with AI-powered search and collaborative annotations.**

Built for a 36-hour hackathon, Astro-Zoom lets you explore massive astronomical images with smooth deep-zoom navigation powered by OpenSeadragon, find interesting features using CLIP-based semantic search, and annotate regions collaboratively.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Node](https://img.shields.io/badge/node-20+-green.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

## ✨ Features

- **🔍 Deep Zoom Navigation** — Explore gigapixel images with smooth pan/zoom using OpenSeadragon
- **🤖 AI Search** — Find features with natural language queries powered by CLIP embeddings
- **✏️ Annotations** — Create points, rectangles, and polygons with labels
- **⚖️ Compare Mode** — Side-by-side view with synchronized zoom/pan
- **⏱️ Timeline** — View temporal changes in image datasets
- **🎨 Modern UI** — Dark theme, responsive design, keyboard shortcuts
- **🚀 Production Ready** — Docker, rate limiting, authentication, CI/CD

## 🏗️ Architecture

```
astro-zoom/
├── apps/
│   ├── web/          Next.js 14 + OpenSeadragon viewer
│   ├── api/          FastAPI backend with SQLite
│   └── ai/           CLIP + FAISS semantic search
├── packages/
│   ├── proto/        Shared TypeScript/Python schemas
│   └── ui/           React component library
├── infra/
│   ├── docker-compose.yml
│   ├── tiles/        Sample DZI tile pyramids
│   └── Dockerfile.*
└── .github/workflows/ CI/CD pipelines
```

### Tech Stack

**Frontend**

- Next.js 14 (App Router), TypeScript
- OpenSeadragon (deep zoom)
- Zustand (state), TanStack Query (data fetching)
- Tailwind CSS

**Backend**

- FastAPI, Uvicorn, SQLModel (SQLite)
- JWT authentication, rate limiting
- DZI tile serving

**AI**

- CLIP (OpenAI ViT-B/32) or stub fallback
- FAISS (CPU) vector search
- Numpy, Pillow

**DevOps**

- Monorepo: pnpm workspaces + Turborepo
- Docker Compose
- GitHub Actions CI

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+ ([download](https://nodejs.org/))
- **pnpm** 8+ (installed automatically if missing)
- **Python** 3.11+ ([download](https://www.python.org/downloads/))
- **Docker** (optional, for containerized setup)

### Option 1: Native Development (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd astro-zoom

# Run setup script (installs deps, generates tiles)
chmod +x infra/setup.sh
./infra/setup.sh

# Start all services
pnpm dev
```

**Services will be available at:**

- 🌐 Web: http://localhost:3000
- 🔌 API: http://localhost:8000 (docs at /docs)
- 🤖 AI: http://localhost:8001

> **⚠️ Troubleshooting:** If you see "Failed to fetch datasets" error, the API server may not be running. See [START_SERVICES.md](START_SERVICES.md) for help.

### Option 2: Docker Compose

```bash
# Generate sample tiles first
python3 infra/generate_sample_tiles.py

# Start all services
cd infra
docker compose up --build
```

Wait ~30s for services to start, then visit http://localhost:3000.

## 📖 Usage

### Using Real NASA Data

The project includes mock sample tiles by default. To use the **real 209MB NASA Andromeda image**:

```bash
# Install tiling dependencies
pip install -r infra/requirements_tiling.txt

# Process the real image (takes 10-30 minutes)
python infra/process_real_image.py
```

This downloads the actual NASA Hubble Andromeda mosaic (42208x9870 pixels) and generates an optimized tile pyramid. See `infra/TILE_GENERATION.md` for details.

### Exploring Datasets

1. Visit http://localhost:3000
2. Click on "Andromeda Galaxy (Sample)" or "Andromeda Galaxy (NASA Hubble 2025)"
3. Use mouse to pan/zoom, or:
   - **Scroll** to zoom
   - **Drag** to pan
   - **F** key to fit image
   - **G** key to toggle grid

### Keyboard Shortcuts

- **1** — Explore mode
- **2** — Compare mode (side-by-side)
- **3** — Annotate mode
- **F** — Fit to viewport
- **G** — Toggle grid overlay

### Creating Annotations

1. Switch to **Annotate mode** (press `3` or click toolbar)
2. Choose annotation type: Point or Rectangle
3. Click on the image:
   - **Point**: Single click
   - **Rectangle**: Click start, then click end
4. Annotations save automatically and persist on refresh

### AI Search

1. Open the **Search Box** (left sidebar)
2. Enter a natural language query, e.g.:
   - "bright star cluster"
   - "spiral arm structure"
   - "dark dust lane"
3. Click results to fly to matching regions

> **Note:** Search uses stub embeddings by default. For real AI search, install `open-clip-torch` and `torch` in `apps/ai`.

## 🔧 Development

### Project Structure

```
apps/web/
├── src/
│   ├── app/              Next.js App Router pages
│   ├── components/       React components
│   │   ├── DeepZoomViewer.tsx
│   │   ├── CompareSwipe.tsx
│   │   ├── Annotator.tsx
│   │   └── ...
│   ├── lib/              API client
│   └── store/            Zustand stores

apps/api/
├── app/
│   ├── main.py           FastAPI app
│   ├── models.py         SQLModel database models
│   ├── routers/          API endpoints
│   │   ├── datasets.py
│   │   ├── annotations.py
│   │   ├── search.py
│   │   └── tiles.py
│   └── seed.py           Database seeding

apps/ai/
├── app/
│   ├── main.py           AI service
│   ├── clip_stub.py      Fallback implementation
│   └── indexer.py        FAISS indexing
```

### Running Individual Services

**Web (Next.js)**

```bash
cd apps/web
pnpm dev
```

**API (FastAPI)**

```bash
cd apps/api
make dev
# or: uvicorn app.main:app --reload --port 8000
```

**AI (Python)**

```bash
cd apps/ai
make dev
# or: uvicorn app.main:app --reload --port 8001
```

### Building for Production

```bash
# Build all packages
pnpm build

# Run production web server
cd apps/web
pnpm build
pnpm start

# Run production API/AI (use gunicorn or similar)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🧪 Testing

```bash
# Lint all code
pnpm lint

# Typecheck TypeScript
pnpm typecheck

# Python linting
cd apps/api
ruff check app/

# Run tests (if implemented)
pnpm test
```

## 📊 Adding Your Own Datasets

### 1. Create DZI Tiles

Use [Vips](https://www.libvips.org/) or [OpenSlide](https://openslide.org/) to generate DZI pyramids:

```bash
# With ImageMagick + vips
vips dzsave your_image.tif tiles/my-dataset

# This creates:
# tiles/my-dataset/info.dzi
# tiles/my-dataset/0/0_0.jpg
# tiles/my-dataset/1/*.jpg
# ... etc
```

### 2. Register Dataset

Add to `apps/api/app/seed.py`:

```python
dataset = Dataset(
    id="my-dataset",
    name="My Amazing Dataset",
    description="High-resolution image of...",
    tile_type="dzi",
    tile_url="/tiles/my-dataset",
    levels=json.dumps([0, 1, 2, 3, 4]),
    pixel_size=json.dumps([16384, 16384]),
)
session.add(dataset)
```

### 3. Build Search Index

```bash
cd apps/ai
python build_index.py my-dataset
```

## 🔐 Authentication

Demo credentials (for annotation writes):

- **Username:** `editor`
- **Password:** `demo123`

Login at `/auth/login` or via API:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"editor","password":"demo123"}'
```

Use the returned JWT token in `Authorization: Bearer <token>` header.

## 🐳 Docker

### Build Images

```bash
cd infra
docker compose build
```

### View Logs

```bash
docker compose logs -f web
docker compose logs -f api
docker compose logs -f ai
```

### Reset Volumes

```bash
docker compose down -v
docker compose up --build
```

## 🚦 API Documentation

FastAPI automatically generates OpenAPI docs:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

**Datasets**

- `GET /datasets` — List all datasets
- `GET /datasets/{id}` — Get dataset details

**Annotations**

- `GET /annotations?datasetId=X` — List annotations
- `POST /annotations` — Create annotation
- `PUT /annotations/{id}` — Update annotation
- `DELETE /annotations/{id}` — Delete annotation

**Search**

- `GET /search?q=crater&datasetId=X` — AI semantic search

**Tiles**

- `GET /tiles/{dataset}/info.dzi` — DZI descriptor
- `GET /tiles/{dataset}/{level}/{col}_{row}.jpg` — Tile image

## 🤝 Contributing

This is a hackathon project, but contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -am 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenSeadragon** — Incredible deep zoom library
- **OpenAI CLIP** — Semantic image search
- **NASA/ESA** — Inspiring imagery
- **FastAPI** — Modern Python web framework
- **Next.js** — React framework

## 🐛 Troubleshooting

### Port already in use

```bash
# Find and kill process using port 3000
lsof -ti:3000 | xargs kill -9

# Or use different ports
PORT=3001 pnpm dev
```

### Database locked

```bash
# Remove SQLite lock
rm data/astro.db-shm data/astro.db-wal
```

### CORS errors

Make sure `NEXT_PUBLIC_API_URL` matches your API URL:

```bash
# .env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Tiles not loading

Check that tiles exist:

```bash
ls -la infra/tiles/andromeda/
python3 infra/generate_sample_tiles.py
```

### AI search returns empty

The stub implementation generates random results. For real search:

```bash
cd apps/ai
pip install open-clip-torch torch
python build_index.py andromeda
```

## 📧 Contact

Built for a 36-hour hackathon by your team name here.

---

**Happy exploring! 🌌✨**
