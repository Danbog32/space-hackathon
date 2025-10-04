"""AI service configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
ROOT_DIR = BASE_DIR.parent.parent
TILES_DIR = ROOT_DIR / "infra" / "tiles"
INDEX_DIR = BASE_DIR / "indices"

# Ensure directories exist
INDEX_DIR.mkdir(exist_ok=True)

# CLIP model configuration
CLIP_MODEL = os.getenv("CLIP_MODEL", "ViT-B-32")
CLIP_PRETRAINED = os.getenv("CLIP_PRETRAINED", "openai")

# Index configuration
DEFAULT_PATCH_SIZE = int(os.getenv("DEFAULT_PATCH_SIZE", "256"))
DEFAULT_STRIDE = int(os.getenv("DEFAULT_STRIDE", "128"))

# Check if CLIP is available
try:
    import open_clip
    import torch

    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    print("Warning: CLIP not available, using stub implementation")

