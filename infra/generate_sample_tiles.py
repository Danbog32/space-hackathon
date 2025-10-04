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

def calculate_levels(image_width, image_height, tile_size=256):
    """Calculate the number of levels needed for deep zoom."""
    import math
    
    # Calculate how many levels we need
    max_dimension = max(image_width, image_height)
    num_levels = int(math.ceil(math.log2(max_dimension / tile_size))) + 1
    
    levels = []
    for level in range(num_levels):
        scale = 2 ** level
        level_width = int(math.ceil(image_width / scale))
        level_height = int(math.ceil(image_height / scale))
        
        tiles_x = int(math.ceil(level_width / tile_size))
        tiles_y = int(math.ceil(level_height / tile_size))
        
        levels.append({
            'level': level,
            'width': level_width,
            'height': level_height,
            'tiles_x': tiles_x,
            'tiles_y': tiles_y,
            'scale': scale
        })
    
    return levels

def generate_dzi_xml(image_width, image_height, tile_size=256, overlap=1):
    """Generate DZI XML descriptor."""
    xml = f'''<?xml version="1.0" ?>
<Image xmlns="http://schemas.microsoft.com/deepzoom/2008" Format="jpg" Overlap="{overlap}" TileSize="{tile_size}">
  <Size Width="{image_width}" Height="{image_height}"/>
</Image>'''
    return xml

def generate_tiles():
    """Generate tiles for multiple levels with realistic deep zoom structure."""
    print("Generating sample tiles for Andromeda dataset...")
    
    # Simulate a large image (like the Hubble image dimensions)
    image_width = 42208
    image_height = 9870
    
    print(f"Simulating image size: {image_width}x{image_height}")
    
    # Calculate levels needed
    levels = calculate_levels(image_width, image_height, TILE_SIZE)
    
    # Limit to reasonable number of levels for demo (8 levels max)
    levels = levels[:8]
    
    print(f"Will generate {len(levels)} levels")
    
    total_tiles = 0
    
    # Generate tiles for each level
    for level_info in levels:
        level = level_info['level']
        tiles_x = level_info['tiles_x']
        tiles_y = level_info['tiles_y']
        
        print(f"Generating level {level}: {tiles_x}x{tiles_y} = {tiles_x * tiles_y} tiles")
        
        # Create level directory
        level_dir = TILES_DIR / str(level)
        level_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate tiles for this level
        for col in range(tiles_x):
            for row in range(tiles_y):
                # Add variation based on position and level
                base_stars = 20 + (level * 5)  # More stars at higher levels
                star_count = random.randint(base_stars, base_stars + 20)
                
                # Center area gets more stars (galaxy center effect)
                center_x = tiles_x // 2
                center_y = tiles_y // 2
                distance_from_center = abs(col - center_x) + abs(row - center_y)
                if distance_from_center <= 1:
                    star_count += 30
                
                tile = create_star_field_tile(TILE_SIZE, TILE_SIZE, star_count=star_count)
                tile.save(level_dir / f"{col}_{row}.jpg", "JPEG", quality=85)
        
        level_tiles = tiles_x * tiles_y
        total_tiles += level_tiles
        print(f"  ✓ Generated {level_tiles} tiles")
    
    # Generate DZI XML descriptor
    dzi_xml = generate_dzi_xml(image_width, image_height, TILE_SIZE, 1)
    dzi_path = TILES_DIR / "info.dzi"
    with open(dzi_path, 'w') as f:
        f.write(dzi_xml)
    
    print(f"\n✓ Total: {total_tiles} tiles generated in {TILES_DIR}")
    print(f"✓ DZI descriptor saved to: {dzi_path}")

if __name__ == "__main__":
    generate_tiles()
