"""Application configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent.parent
DATA_DIR = ROOT_DIR / "data"
TILES_DIR = ROOT_DIR / "infra" / "tiles"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/astro.db")

# Services
API_URL = os.getenv("API_URL", "http://localhost:8000")
AI_URL = os.getenv("AI_URL", "http://localhost:8001")

# Auth
JWT_SECRET = os.getenv("JWT_SECRET", "devsecret_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Rate limiting
RATE_LIMIT_SEARCH = os.getenv("RATE_LIMIT_SEARCH", "10/minute")

# Tile serving
TILE_BASE = os.getenv("TILE_BASE", str(TILES_DIR))
if TILE_BASE.startswith("file://"):
    TILE_BASE = TILE_BASE[7:]

