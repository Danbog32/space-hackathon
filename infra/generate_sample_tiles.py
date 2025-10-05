#!/usr/bin/env python3
"""
Generate sample tile images for the Andromeda dataset.
Creates a simple gradient/star field pattern for demo purposes.
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw
import random

TILES_DIR = Path(__file__).parent / "tiles" / "andromeda"
TILE_SIZE = 256

def create_star_field_tile(width=256, height=256, star_count=20):
    """Create a tile with a gradient and stars."""
    # Create base image with dark gradient
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Add subtle gradient
    for y in range(height):
        brightness = int(5 + (y / height) * 20)
        for x in range(width):
            r = brightness + random.randint(-5, 5)
            g = brightness + random.randint(-5, 5)
            b = brightness + random.randint(0, 10)
            draw.point((x, y), fill=(max(0, r), max(0, g), max(0, b)))
    
    # Add random stars
    for _ in range(star_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        brightness = random.randint(150, 255)
        size = random.choice([1, 1, 1, 2])
        
        for dx in range(-size, size + 1):
            for dy in range(-size, size + 1):
                if 0 <= x + dx < width and 0 <= y + dy < height:
                    draw.point((x + dx, y + dy), fill=(brightness, brightness, brightness))
    
    return img

def generate_tiles():
    """Generate tiles for levels 0-2."""
    print("Generating sample tiles for Andromeda dataset...")
    
    # Level 0: Single tile (full image at lowest resolution)
    level_0_dir = TILES_DIR / "0"
    level_0_dir.mkdir(parents=True, exist_ok=True)
    
    tile = create_star_field_tile(256, 256, star_count=30)
    tile.save(level_0_dir / "0_0.jpg", "JPEG", quality=85)
    print(f"Created level 0: 1 tile")
    
    # Level 1: 2x2 tiles
    level_1_dir = TILES_DIR / "1"
    level_1_dir.mkdir(parents=True, exist_ok=True)
    
    for col in range(2):
        for row in range(2):
            tile = create_star_field_tile(256, 256, star_count=25)
            tile.save(level_1_dir / f"{col}_{row}.jpg", "JPEG", quality=85)
    print(f"Created level 1: 4 tiles")
    
    # Level 2: 4x4 tiles
    level_2_dir = TILES_DIR / "2"
    level_2_dir.mkdir(parents=True, exist_ok=True)
    
    for col in range(4):
        for row in range(4):
            # Add some variation based on position
            star_count = random.randint(20, 40)
            if col in [1, 2] and row in [1, 2]:  # Center area brighter
                star_count += 20
            
            tile = create_star_field_tile(256, 256, star_count=star_count)
            tile.save(level_2_dir / f"{col}_{row}.jpg", "JPEG", quality=85)
    print(f"Created level 2: 16 tiles")
    
    print(f"\nTotal: 21 tiles generated in {TILES_DIR}")
    print("DZI descriptor already exists at:", TILES_DIR / "info.dzi")

if __name__ == "__main__":
    generate_tiles()

