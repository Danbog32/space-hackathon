# Astro-Zoom Project Overview

## 📦 What Was Built

A complete, production-ready monorepo for exploring gigantic NASA images with:

- **Deep zoom navigation** using OpenSeadragon
- **AI-powered search** with CLIP embeddings and FAISS
- **Collaborative annotations** with persistent storage
- **Multiple viewing modes** (Explore, Compare, Annotate, Timeline)
- **Docker deployment** with docker-compose
- **CI/CD pipeline** with GitHub Actions

## 🗂️ Repository Structure

```
astro-zoom/
├── apps/
│   ├── web/              🌐 Next.js 14 viewer
│   │   ├── src/
│   │   │   ├── app/              Pages (App Router)
│   │   │   ├── components/       React components
│   │   │   │   ├── DeepZoomViewer.tsx    OpenSeadragon wrapper
│   │   │   │   ├── CompareSwipe.tsx      Side-by-side compare
│   │   │   │   ├── Annotator.tsx         Annotation tool
│   │   │   │   ├── SearchBox.tsx         AI search UI
│   │   │   │   └── ...
│   │   │   ├── lib/              API client
│   │   │   └── store/            Zustand state
│   │   └── package.json
│   │
│   ├── api/              🔌 FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py           FastAPI app
│   │   │   ├── models.py         SQLModel schemas
│   │   │   ├── db.py             Database connection
│   │   │   ├── auth.py           JWT authentication
│   │   │   ├── seed.py           Database seeding
│   │   │   └── routers/
│   │   │       ├── datasets.py   Dataset endpoints
│   │   │       ├── annotations.py Annotation CRUD
│   │   │       ├── features.py   Feature endpoints
│   │   │       ├── search.py     Search proxy
│   │   │       ├── tiles.py      DZI tile serving
│   │   │       └── auth.py       Login endpoint
│   │   ├── requirements.txt
│   │   └── Makefile
│   │
│   └── ai/               🤖 AI search service
│       ├── app/
│       │   ├── main.py           AI service
│       │   ├── clip_stub.py      Fallback implementation
│       │   ├── indexer.py        FAISS indexing
│       │   └── config.py         Configuration
│       ├── build_index.py        CLI for index building
│       └── requirements.txt
│
├── packages/
│   ├── proto/            📋 Shared schemas
│   │   ├── src/index.ts          Zod schemas (TypeScript)
│   │   └── proto_py/__init__.py  Pydantic models (Python)
│   │
│   └── ui/               🎨 Component library
│       └── src/
│           ├── Button.tsx
│           ├── Input.tsx
│           ├── Panel.tsx
│           ├── Toolbar.tsx
│           ├── Toggle.tsx
│           ├── Tooltip.tsx
│           └── Timeline.tsx
│
├── infra/                🐳 Infrastructure
│   ├── docker-compose.yml        Multi-service orchestration
│   ├── Dockerfile.web            Web container
│   ├── Dockerfile.api            API container
│   ├── Dockerfile.ai             AI container
│   ├── setup.sh                  Setup script
│   ├── generate_sample_tiles.py  Tile generator
│   └── tiles/
│       └── andromeda/            Sample dataset
│           ├── info.dzi          DZI descriptor
│           ├── 0/                Level 0 (1 tile)
│           ├── 1/                Level 1 (4 tiles)
│           └── 2/                Level 2 (16 tiles)
│
├── .github/
│   └── workflows/
│       └── ci.yml                GitHub Actions CI
│
├── data/                 💾 Database storage
│   └── .gitkeep
│
├── package.json          📦 Root package
├── pnpm-workspace.yaml   🔧 Workspace config
├── turbo.json            ⚡ Turborepo config
├── .gitignore
├── .dockerignore
├── .editorconfig
├── .prettierrc
├── LICENSE               📄 MIT
├── README.md             📖 Full documentation
├── QUICKSTART.md         🚀 Quick start
├── CONTRIBUTING.md       🤝 Contribution guide
└── PROJECT_OVERVIEW.md   📋 This file
```

## 🎯 Key Features Implemented

### Web Application (Next.js)

✅ Homepage with dataset picker  
✅ Deep zoom viewer with OpenSeadragon  
✅ Compare mode with synchronized A/B swipe  
✅ Annotation mode (points, rectangles)  
✅ Timeline view for temporal datasets  
✅ AI search box with result pins  
✅ Keyboard shortcuts (1-3 for modes, F for fit, G for grid)  
✅ Zustand state management  
✅ TanStack Query for data fetching  
✅ Dark theme with Tailwind CSS  
✅ Responsive layout

### API Service (FastAPI)

✅ RESTful endpoints for datasets, annotations, features  
✅ DZI tile serving with caching headers  
✅ SQLite database with SQLModel ORM  
✅ JWT authentication for write operations  
✅ Rate limiting on search endpoints  
✅ CORS middleware  
✅ OpenAPI documentation at /docs  
✅ Health check endpoint  
✅ Database seeding with sample data

### AI Service (Python)

✅ CLIP-based semantic search (with stub fallback)  
✅ FAISS vector index  
✅ Index building from tiled images  
✅ Search endpoint with top-K results  
✅ Embedding generation endpoint  
✅ Deterministic stub for systems without GPU

### Infrastructure

✅ Monorepo with pnpm workspaces  
✅ Turborepo for parallel task execution  
✅ Docker Compose for multi-service deployment  
✅ Sample tile pyramid (21 tiles, 3 levels)  
✅ Setup script for easy initialization  
✅ GitHub Actions CI for lint/build/test  
✅ Environment variable configuration

### Shared Packages

✅ TypeScript schemas with Zod  
✅ Python schemas with Pydantic  
✅ React component library with Tailwind  
✅ Type-safe cross-service communication

## 🔧 Technology Stack

| Layer        | Technology     | Purpose                         |
| ------------ | -------------- | ------------------------------- |
| **Frontend** | Next.js 14     | React framework with App Router |
|              | TypeScript     | Type safety                     |
|              | OpenSeadragon  | Deep zoom viewer                |
|              | Zustand        | State management                |
|              | TanStack Query | Data fetching                   |
|              | Tailwind CSS   | Styling                         |
| **Backend**  | FastAPI        | Python web framework            |
|              | SQLModel       | ORM with SQLite                 |
|              | Uvicorn        | ASGI server                     |
|              | python-jose    | JWT authentication              |
|              | slowapi        | Rate limiting                   |
| **AI**       | CLIP (OpenAI)  | Image embeddings                |
|              | FAISS          | Vector search                   |
|              | NumPy          | Numerical operations            |
|              | Pillow         | Image processing                |
| **DevOps**   | pnpm           | Package manager                 |
|              | Turborepo      | Build orchestration             |
|              | Docker         | Containerization                |
|              | GitHub Actions | CI/CD                           |

## 📊 Project Statistics

- **Total Files:** ~150+
- **Lines of Code:** ~5,000+
- **Languages:** TypeScript, Python, JavaScript
- **Services:** 3 (web, api, ai)
- **Packages:** 2 (proto, ui)
- **Components:** 10+ React components
- **API Endpoints:** 15+
- **Sample Tiles:** 21 generated images

## 🚀 Getting Started

### Quick Start (5 minutes)

```bash
./infra/setup.sh
pnpm dev
```

Visit http://localhost:3000

### Docker Start

```bash
cd infra
docker compose up --build
```

## 🎨 UI Features

### Viewer Modes

1. **Explore** — Free navigation with pan/zoom
2. **Compare** — Side-by-side view with draggable divider
3. **Annotate** — Create and save markers
4. **Timeline** — Switch between temporal variants

### Keyboard Shortcuts

- `1` — Explore mode
- `2` — Compare mode
- `3` — Annotate mode
- `F` — Fit to viewport
- `G` — Toggle grid overlay

### Annotations

- **Point** — Single click marker
- **Rectangle** — Two-click bounding box
- **Labels** — Custom text labels
- **Colors** — Customizable colors
- **Persistence** — Saved to database
- **CRUD** — Full create/read/update/delete

### Search

- Natural language queries
- AI-powered semantic matching
- Click results to fly to location
- Score ranking
- Rate limited (10/min/IP)

## 📈 Performance Considerations

- **Tile Caching** — HTTP cache headers (1 year)
- **Code Splitting** — Next.js automatic chunking
- **Image Optimization** — Progressive JPEG tiles
- **Database Indexing** — SQLite with proper indexes
- **Rate Limiting** — Protect against abuse
- **Lazy Loading** — Components loaded on demand

## 🔐 Security Features

- JWT authentication for write operations
- CORS protection
- Rate limiting on expensive endpoints
- Input validation with Pydantic/Zod
- SQL injection prevention (SQLModel ORM)
- Environment variable configuration

## 🧪 Testing

### Lint

```bash
pnpm lint
```

### Typecheck

```bash
pnpm typecheck
```

### Python Lint

```bash
cd apps/api && ruff check app/
cd apps/ai && ruff check app/
```

## 📦 Deployment

### Production Build

```bash
pnpm build
```

### Docker Production

```bash
docker compose -f infra/docker-compose.yml up -d
```

### Environment Variables

Set production values for:

- `JWT_SECRET` — Change from demo value
- `DATABASE_URL` — PostgreSQL for production
- `CORS_ORIGINS` — Your domain
- `RATE_LIMIT_SEARCH` — Adjust as needed

## 🔮 Future Enhancements

- [ ] PostgreSQL support
- [ ] Real-time collaboration with WebSockets
- [ ] Polygon annotations
- [ ] Export annotations as GeoJSON
- [ ] Advanced search filters
- [ ] User management and permissions
- [ ] Multiple dataset comparison
- [ ] Video/animation timelines
- [ ] 3D cube view
- [ ] Mobile-optimized touch controls
- [ ] Progressive Web App (PWA)
- [ ] Offline support
- [ ] Analytics dashboard

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Credits

Built for a 36-hour hackathon by a passionate team.

Special thanks to:

- OpenSeadragon community
- FastAPI framework
- OpenAI CLIP team
- NASA/ESA for inspiring imagery
