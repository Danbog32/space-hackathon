"""Main FastAPI application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import CORS_ORIGINS
from app.db import create_db_and_tables
from app.routers import (
    datasets,
    features,
    annotations,
    search,
    tiles,
    overlays,
    auth as auth_router,
    uploads,
    classify,
    detect
)

from app.seed import seed_database

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    create_db_and_tables()
    seed_database()
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title="Astro-Zoom API",
    description="Backend API for deep zoom image viewing with AI search",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
app.include_router(features.router, prefix="/features", tags=["features"])
app.include_router(annotations.router, prefix="/annotations", tags=["annotations"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(classify.router, prefix="/classify", tags=["classify"])
app.include_router(detect.router, prefix="/detect", tags=["detect"])
app.include_router(tiles.router, prefix="/tiles", tags=["tiles"])
app.include_router(overlays.router, prefix="/overlays", tags=["overlays"])
app.include_router(uploads.router, prefix="/uploads", tags=["uploads"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from datetime import datetime

    return {"status": "ok", "version": "0.1.0", "timestamp": datetime.now().isoformat()}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Astro-Zoom API",
        "docs": "/docs",
        "health": "/health",
    }

