# 🚀 Deployment Guide

## Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ & pnpm
- Python 3.11+
- Git

### One-Command Setup

**Windows (PowerShell):**
```powershell
.\start.ps1
```

**Linux/Mac/WSL:**
```bash
chmod +x *.sh
./start.sh
```

**Using Makefile:**
```bash
make dev
```

### Access Points
- 🌐 **Web**: http://localhost:3000
- 🔌 **API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🤖 **AI Service**: http://localhost:8001

---

## Development Setup (Without Docker)

### 1. Install Dependencies

```bash
# Node.js packages
pnpm install

# Python packages (API)
cd apps/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Python packages (AI)
cd ../ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy example environment file
cp .env.example .env

# Or for development
cp .env.development .env

# Edit .env with your settings
nano .env
```

### 3. Prepare Data

```bash
# Create database
mkdir -p data

# Generate sample tiles
python infra/generate_sample_tiles.py

# Seed database (run API once to create schema)
cd apps/api
python -m app.seed
```

### 4. Start Services Individually

**Terminal 1 - Web:**
```bash
cd apps/web
pnpm dev
```

**Terminal 2 - API:**
```bash
cd apps/api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 - AI:**
```bash
cd apps/ai
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

## Docker Deployment

### Development

```bash
# Start all services
docker-compose -f infra/docker-compose.yml up --build

# Run in background
docker-compose -f infra/docker-compose.yml up -d

# View logs
docker-compose -f infra/docker-compose.yml logs -f

# Stop services
docker-compose -f infra/docker-compose.yml down
```

### Production (Docker Compose)

1. **Update Environment:**
```bash
cp .env.example .env.production
# Edit .env.production with production values
```

2. **Build Images:**
```bash
docker-compose -f infra/docker-compose.yml build
```

3. **Start Services:**
```bash
docker-compose -f infra/docker-compose.yml --env-file .env.production up -d
```

4. **Verify Health:**
```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

---

## Cloud Deployment

### Option 1: Vercel (Frontend) + Render (Backend)

#### Frontend (Vercel)
1. **Connect Repository:**
   - Go to vercel.com
   - Import GitHub repository
   - Root: `apps/web`

2. **Configure:**
   ```
   Framework: Next.js
   Build Command: pnpm build
   Output Directory: .next
   Install Command: pnpm install
   ```

3. **Environment Variables:**
   ```
   NEXT_PUBLIC_API_URL=https://your-api.render.com
   ```

4. **Deploy:**
   - Auto-deploys on push to main

#### Backend (Render)
1. **Create Web Service:**
   - Docker service
   - Dockerfile: `infra/Dockerfile.api`

2. **Environment Variables:**
   ```
   DATABASE_URL=postgresql://...
   JWT_SECRET=<strong-random-secret>
   CORS_ORIGINS=https://your-app.vercel.app
   AI_URL=https://your-ai-service.render.com
   ```

3. **Create AI Service:**
   - Docker service
   - Dockerfile: `infra/Dockerfile.ai`

4. **Add Database:**
   - PostgreSQL instance
   - Copy connection string to API env vars

### Option 2: Fly.io (All Services)

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy API
cd apps/api
fly launch --dockerfile ../../infra/Dockerfile.api
fly secrets set JWT_SECRET=<secret>
fly secrets set CORS_ORIGINS=https://your-domain.com

# Deploy AI
cd apps/ai
fly launch --dockerfile ../../infra/Dockerfile.ai

# Deploy Web
cd apps/web
fly launch --dockerfile ../../infra/Dockerfile.web
fly secrets set NEXT_PUBLIC_API_URL=https://api.fly.dev
```

### Option 3: AWS (ECS + RDS + S3)

**Architecture:**
```
[ CloudFront ] → [ ALB ] → [ ECS Tasks ]
                              ↓
                          [ RDS (Postgres) ]
                              ↓
                          [ S3 (Tiles) ]
```

**Steps:**
1. Create RDS PostgreSQL instance
2. Create S3 bucket for tiles
3. Build & push Docker images to ECR
4. Create ECS cluster & services
5. Configure ALB with health checks
6. Set up CloudFront for CDN
7. Configure Route53 for DNS

See: `docs/AWS_DEPLOYMENT.md` (TODO)

### Option 4: DigitalOcean App Platform

1. **Connect Repository**
2. **Configure Components:**
   - Web: Docker, port 3000
   - API: Docker, port 8000
   - AI: Docker, port 8001
   - DB: Managed PostgreSQL

3. **Set Environment Variables**
4. **Deploy**

---

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `postgresql://user:pass@host:5432/db` |
| `JWT_SECRET` | JWT signing secret | `your-secret-key-min-32-chars` |
| `CORS_ORIGINS` | Allowed origins (comma-separated) | `https://app.com,https://api.com` |
| `AI_URL` | AI service URL | `http://ai:8001` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_EXPIRATION` | Token lifetime (seconds) | `3600` |
| `RATE_LIMIT_SEARCH` | Search rate limit | `10/minute` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `TILE_BASE` | Tile storage location | `/app/infra/tiles` |

### Security Variables

```bash
# Generate strong JWT secret
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Setup

### SQLite (Development)
```bash
# Automatic - created on first run
# Location: ./data/astro.db
```

### PostgreSQL (Production)

```bash
# Create database
createdb astro_viewer

# Set connection string
export DATABASE_URL="postgresql://user:password@localhost:5432/astro_viewer"

# Run migrations (future)
# alembic upgrade head
```

**Connection String Format:**
```
postgresql://[user]:[password]@[host]:[port]/[database]
```

---

## Tile Storage

### Local Storage (Development)
```bash
# Tiles stored in: ./infra/tiles/
# Structure: tiles/{dataset}/{level}/{col}_{row}.jpg
```

### S3 (Production)

1. **Create S3 Bucket:**
```bash
aws s3 mb s3://nasa-viewer-tiles
```

2. **Upload Tiles:**
```bash
aws s3 sync ./infra/tiles/ s3://nasa-viewer-tiles/tiles/
```

3. **Configure:**
```bash
export TILE_BASE="s3://nasa-viewer-tiles/tiles"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

4. **Set Bucket Policy** (public read):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::nasa-viewer-tiles/*"
  }]
}
```

---

## Health Checks

### Endpoints
```bash
# API health
curl http://localhost:8000/health
# Response: {"status": "ok", "version": "0.1.0", "timestamp": "..."}

# AI health
curl http://localhost:8001/health
# Response: {"status": "ok", "version": "0.1.0", "timestamp": "..."}

# Web (Next.js)
curl http://localhost:3000
# Response: HTML page
```

### Automated
```bash
# Run health check script
./healthcheck.sh  # Linux/Mac
.\healthcheck.ps1 # Windows

# Or using Make
make health
```

---

## Monitoring & Logging

### View Logs

**Docker:**
```bash
# All services
docker-compose -f infra/docker-compose.yml logs -f

# Specific service
docker-compose -f infra/docker-compose.yml logs -f api

# Last 100 lines
docker-compose -f infra/docker-compose.yml logs --tail=100
```

**Local:**
```bash
# Audit logs
tail -f logs/audit.log

# With formatting
tail -f logs/audit.log | jq

# View recent audit events
make audit
```

### Log Locations
- **API Logs**: `/app/logs/api.log`
- **Audit Logs**: `/app/logs/audit.log`
- **Docker Logs**: `docker logs <container-id>`

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :3000  # Linux/Mac
netstat -ano | findstr :3000  # Windows

# Kill process
kill -9 <PID>  # Linux/Mac
Stop-Process -Id <PID> -Force  # Windows PowerShell
```

### Services Won't Start

1. **Check prerequisites:**
```bash
node --version  # Should be 18+
python --version  # Should be 3.11+
docker --version
```

2. **Check logs:**
```bash
make logs
```

3. **Clean restart:**
```bash
make clean
make build
make dev
```

### Database Issues

**Locked database:**
```bash
rm data/astro.db-shm data/astro.db-wal
```

**Reset database:**
```bash
rm data/astro.db
# Restart API to recreate
```

### Docker Issues

**Clean everything:**
```bash
docker-compose -f infra/docker-compose.yml down -v
docker system prune -a
```

**Rebuild from scratch:**
```bash
make clean
make build
make dev
```

---

## Performance Tuning

### Frontend
- Enable Next.js image optimization
- Use `next/dynamic` for code splitting
- Implement service worker for tile caching

### Backend
- Enable response caching for static endpoints
- Use connection pooling for database
- Implement Redis for session storage

### AI Service
- Precompute FAISS indices
- Use GPU for CLIP if available
- Implement result caching

---

## Security Checklist

Before deploying to production:

- [ ] Change `JWT_SECRET` to strong random value
- [ ] Use HTTPS/TLS (Let's Encrypt)
- [ ] Update `CORS_ORIGINS` to production domains
- [ ] Set `DEBUG=false`
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Set up monitoring/alerting
- [ ] Review rate limits
- [ ] Enable audit log rotation
- [ ] Scan Docker images for vulnerabilities
- [ ] Set up WAF (if using cloud)
- [ ] Configure CDN for tiles
- [ ] Enable DDoS protection

---

## Backup & Recovery

### Database Backup
```bash
# SQLite
cp data/astro.db data/astro.db.backup

# PostgreSQL
pg_dump astro_viewer > backup.sql
```

### Restore
```bash
# SQLite
cp data/astro.db.backup data/astro.db

# PostgreSQL
psql astro_viewer < backup.sql
```

---

## CI/CD (Optional)

### GitHub Actions

`.github/workflows/deploy.yml`:
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker images
        run: |
          docker build -t api -f infra/Dockerfile.api .
          docker push api
      - name: Deploy to Render
        run: |
          # Trigger Render deployment
```

---

## Support

**Issues:** Create GitHub issue  
**Documentation:** See `README.md`, `SECURITY.md`  
**Team:** @Illia (DevOps/Security), @Edward (API), @Bohdan (Frontend)

---

**Last Updated:** 2025-10-04  
**Version:** 0.1.0

