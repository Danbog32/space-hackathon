#!/usr/bin/env python3
"""
Simplified build script that works without complex dependencies.
"""

import sys
from pathlib import Path
import numpy as np
from PIL import Image
import json

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

def create_simple_demo_image(path: Path, size=(4096, 4096)):
    """Create a simple demo image."""
    if not path.exists():
        print(f"Creating demo image at {path}")
        w, h = size
        
        # Create a simple pattern
        x = np.linspace(0, 255, w, dtype=np.uint8)
        y = np.linspace(0, 255, h, dtype=np.uint8)
        xv, yv = np.meshgrid(x, y)
        base = (0.6 * xv + 0.4 * yv).astype(np.uint8)
        noise = np.random.default_rng(42).integers(0, 30, size=(h, w), dtype=np.uint8)
        img = Image.fromarray(np.clip(base + noise, 0, 255))
        img = img.convert("RGB")
        img.save(path)
        print(f"Demo image saved: {path}")
    
    return Image.open(path).convert("RGB")

def extract_simple_patches(img: Image.Image, patch_size=128, stride=128):
    """Extract patches with simple grid sampling."""
    w, h = img.size
    patches = []
    bboxes = []
    
    for y in range(0, h - patch_size + 1, stride):
        for x in range(0, w - patch_size + 1, stride):
            patch = img.crop((x, y, x + patch_size, y + patch_size))
            patches.append(patch)
            bboxes.append([x, y, patch_size, patch_size])
    
    return patches, bboxes

def create_dummy_embeddings(num_patches, embedding_dim=512):
    """Create dummy embeddings for testing."""
    # Create random normalized embeddings
    embeddings = np.random.randn(num_patches, embedding_dim).astype(np.float32)
    # Normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / norms
    return embeddings

def main():
    """Build a simple demo index."""
    print("🚀 Building simple demo index...")
    
    DATA_DIR = Path(__file__).parent / "data"
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    
    # Create demo image
    IMG_PATH = DATA_DIR / "demo_big.jpg"
    img = create_simple_demo_image(IMG_PATH, size=(2048, 2048))
    print(f"Image size: {img.size}")
    
    # Extract patches
    print("Extracting patches...")
    patches, bboxes = extract_simple_patches(img, patch_size=128, stride=128)
    print(f"Extracted {len(patches)} patches")
    
    # Create dummy embeddings
    print("Creating dummy embeddings...")
    embedding_dim = 512
    embeddings = create_dummy_embeddings(len(patches), embedding_dim)
    
    # Create simple metadata
    metadata = {
        "image_path": str(IMG_PATH.name),
        "patch_size": 128,
        "stride": 128,
        "bboxes": bboxes,
        "num_patches": len(patches),
        "embedding_dim": embedding_dim,
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    # Save metadata
    META_PATH = DATA_DIR / "metadata.json"
    with open(META_PATH, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Simple demo index created!")
    print(f"   Patches: {len(patches)}")
    print(f"   Embeddings: {embeddings.shape}")
    print(f"   Metadata: {META_PATH}")
    print(f"   Image: {IMG_PATH}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
