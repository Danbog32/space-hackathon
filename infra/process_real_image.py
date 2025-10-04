#!/usr/bin/env python3
"""
Process the actual NASA Andromeda image and generate optimized tile pyramid.

Features:
- Downloads the 209MB NASA Andromeda image
- Generates multi-resolution tile pyramid
- Optimizes for web delivery (progressive JPEG, quality settings)
- Creates proper DZI metadata
- Supports resume of interrupted downloads
"""

import math
import os
import sys
from pathlib import Path
from typing import Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom

try:
    import requests
    from PIL import Image
    from tqdm import tqdm
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Please run: pip install requests pillow tqdm")
    sys.exit(1)

# Disable PIL's decompression bomb protection for very large NASA images
# The Andromeda image is 42208x9870 = 416M pixels which exceeds the default 178M limit
Image.MAX_IMAGE_PIXELS = None


# Configuration
IMAGE_URL = "https://assets.science.nasa.gov/content/dam/science/missions/hubble/galaxies/andromeda/Hubble_M31Mosaic_2025_42208x9870_STScI-01JGY8MZB6RAYKZ1V4CHGN37Q6.jpg"
TILES_DIR = Path(__file__).parent / "tiles" / "andromeda"
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
TILE_SIZE = 256
TILE_OVERLAP = 1  # 1 pixel overlap for seamless rendering
TILE_FORMAT = "jpg"
TILE_QUALITY = 85  # JPEG quality (0-100)
MAX_IMAGE_DIMENSION = 42208  # For memory safety, process in chunks if needed


def download_image(url: str, output_path: Path, force: bool = False) -> Path:
    """Download the NASA image with progress bar and resume support."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.exists() and not force:
        print(f"✓ Image already downloaded: {output_path}")
        return output_path
    
    print(f"Downloading NASA Andromeda image ({url})...")
    print("This may take several minutes (209MB)...")
    
    # Get file size
    response = requests.head(url, allow_redirects=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Check if we have a partial download
    resume_header = {}
    initial_pos = 0
    if output_path.exists():
        initial_pos = output_path.stat().st_size
        if initial_pos < total_size:
            resume_header = {'Range': f'bytes={initial_pos}-'}
            print(f"Resuming download from {initial_pos / 1024 / 1024:.1f}MB...")
    
    # Download with progress bar
    response = requests.get(url, headers=resume_header, stream=True)
    response.raise_for_status()
    
    mode = 'ab' if initial_pos > 0 else 'wb'
    with open(output_path, mode) as f:
        with tqdm(
            total=total_size,
            initial=initial_pos,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading"
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
    
    print(f"✓ Download complete: {output_path}")
    return output_path


def get_image_info(image_path: Path) -> Tuple[int, int]:
    """Get image dimensions without loading entire image into memory."""
    with Image.open(image_path) as img:
        return img.size


def calculate_pyramid_levels(width: int, height: int, tile_size: int) -> int:
    """Calculate number of zoom levels needed."""
    max_dimension = max(width, height)
    levels = math.ceil(math.log2(max_dimension / tile_size)) + 1
    return levels


def create_dzi_xml(width: int, height: int, tile_size: int, overlap: int, format: str) -> str:
    """Create DZI XML descriptor."""
    image = ET.Element('Image', {
        'xmlns': 'http://schemas.microsoft.com/deepzoom/2008',
        'Format': format,
        'Overlap': str(overlap),
        'TileSize': str(tile_size)
    })
    
    size = ET.SubElement(image, 'Size', {
        'Width': str(width),
        'Height': str(height)
    })
    
    # Pretty print
    xml_str = ET.tostring(image, encoding='unicode')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ')


def generate_tiles_optimized(image_path: Path, output_dir: Path, tile_size: int = TILE_SIZE, 
                             overlap: int = TILE_OVERLAP, quality: int = TILE_QUALITY):
    """
    Generate optimized tile pyramid from source image.
    
    Optimizations:
    - Progressive JPEG for faster loading
    - Optimal quality settings
    - Memory-efficient processing
    - Only generates necessary levels
    """
    print(f"\nProcessing image: {image_path}")
    
    # Get image dimensions
    with Image.open(image_path) as img:
        original_width, original_height = img.size
        print(f"Image dimensions: {original_width} x {original_height}")
        
        # Calculate pyramid levels
        num_levels = calculate_pyramid_levels(original_width, original_height, tile_size)
        print(f"Generating {num_levels} zoom levels...")
        
        # Clear existing tiles
        if output_dir.exists():
            import shutil
            print("Removing old tiles...")
            shutil.rmtree(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate DZI metadata
        dzi_xml = create_dzi_xml(original_width, original_height, tile_size, overlap, TILE_FORMAT)
        dzi_path = output_dir / "info.dzi"
        with open(dzi_path, 'w') as f:
            f.write(dzi_xml)
        print(f"✓ Created DZI metadata: {dzi_path}")
        
        # Generate pyramid levels from highest to lowest resolution
        current_img = img.copy()
        current_width, current_height = original_width, original_height
        
        total_tiles = 0
        
        for level in range(num_levels - 1, -1, -1):
            level_dir = output_dir / str(level)
            level_dir.mkdir(exist_ok=True)
            
            # Calculate dimensions for this level
            scale = 2 ** (num_levels - 1 - level)
            level_width = max(1, original_width // scale)
            level_height = max(1, original_height // scale)
            
            # Resize image for this level if needed
            if level < num_levels - 1:
                current_img = current_img.resize(
                    (level_width, level_height),
                    Image.Resampling.LANCZOS
                )
            
            # Calculate number of tiles for this level
            cols = math.ceil(level_width / tile_size)
            rows = math.ceil(level_height / tile_size)
            
            print(f"Level {level}: {level_width}x{level_height} ({cols}x{rows} tiles)")
            
            # Generate tiles for this level
            for col in range(cols):
                for row in range(rows):
                    # Calculate tile boundaries
                    x = col * tile_size
                    y = row * tile_size
                    
                    # Add overlap
                    x1 = max(0, x - overlap)
                    y1 = max(0, y - overlap)
                    x2 = min(level_width, x + tile_size + overlap)
                    y2 = min(level_height, y + tile_size + overlap)
                    
                    # Extract tile
                    tile = current_img.crop((x1, y1, x2, y2))
                    
                    # Save as progressive JPEG for better web performance
                    tile_path = level_dir / f"{col}_{row}.{TILE_FORMAT}"
                    tile.save(
                        tile_path,
                        format='JPEG',
                        quality=quality,
                        optimize=True,
                        progressive=True
                    )
                    total_tiles += 1
            
            print(f"  ✓ Generated {cols * rows} tiles")
        
        print(f"\n✓ Total tiles generated: {total_tiles}")
        print(f"✓ Tiles saved to: {output_dir}")


def main():
    """Main processing pipeline."""
    print("=" * 60)
    print("NASA Andromeda Image Tile Generator")
    print("=" * 60)
    print()
    
    # Step 1: Download image
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_filename = "andromeda_hubble_2025.jpg"
    image_path = DOWNLOAD_DIR / image_filename
    
    try:
        download_image(IMAGE_URL, image_path)
    except Exception as e:
        print(f"Error downloading image: {e}")
        print("\nYou can manually download the image from:")
        print(IMAGE_URL)
        print(f"And place it at: {image_path}")
        sys.exit(1)
    
    # Step 2: Verify image
    try:
        width, height = get_image_info(image_path)
        print(f"\n✓ Image verified: {width}x{height} pixels")
        print(f"  File size: {image_path.stat().st_size / 1024 / 1024:.1f}MB")
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)
    
    # Step 3: Generate tiles
    print("\nGenerating optimized tile pyramid...")
    print("This may take 10-30 minutes depending on your CPU...")
    
    try:
        generate_tiles_optimized(image_path, TILES_DIR)
    except Exception as e:
        print(f"Error generating tiles: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ COMPLETE!")
    print("=" * 60)
    print(f"\nTiles are ready in: {TILES_DIR}")
    print("\nNext steps:")
    print("1. Start the API server: cd apps/api && make dev")
    print("2. Start the web app: cd apps/web && pnpm dev")
    print("3. Open http://localhost:3000")
    print()


if __name__ == "__main__":
    main()

