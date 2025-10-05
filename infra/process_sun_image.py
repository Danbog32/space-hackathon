#!/usr/bin/env python3
"""
Process a NASA Sun image and generate optimized Deep Zoom tiles.

Usage:
    python process_sun_image.py

This will:
- Download the provided original Sun image to infra/downloads/sun_sdo_original.jpg
- Generate tiles into infra/tiles/sun/
- Create DZI metadata

Requirements:
    pip install -r infra/requirements_tiling.txt
"""
import sys
from pathlib import Path

try:
    import requests  # noqa: F401 (ensures dependency is present for parity with other scripts)
except ImportError:
    print("Error: Required dependencies not installed. Please run: pip install requests")
    sys.exit(1)

from process_real_image import (
    DOWNLOAD_DIR,
    DATASETS_ROOT,
    download_image,
    get_image_info,
    generate_tiles_optimized,
)

DIRECT_IMAGE_URL = (
    "https://images-assets.nasa.gov/image/GSFC_20171208_Archive_e000790/GSFC_20171208_Archive_e000790~orig.jpg"
)
DEFAULT_FILENAME = "sun_sdo_original.jpg"
DATASET_ID = "sun"


def main() -> None:
    print("=" * 60)
    print("NASA Sun Image Tile Generator")
    print("=" * 60)
    print()

    # Prepare paths
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path = DOWNLOAD_DIR / DEFAULT_FILENAME
    tiles_dir = DATASETS_ROOT / DATASET_ID

    # Download
    try:
        print(f"Downloading: {DIRECT_IMAGE_URL}")
        download_image(DIRECT_IMAGE_URL, image_path)
    except Exception as e:
        print(f"Error downloading image: {e}")
        print("You can manually download and place it at:")
        print(f"  {image_path}")
        sys.exit(1)

    # Verify
    try:
        width, height = get_image_info(image_path)
        print(f"\n✓ Image verified: {width}x{height} pixels")
        print(f"  File size: {image_path.stat().st_size / 1024 / 1024:.1f}MB")
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)

    # Generate tiles
    print("\nGenerating optimized tile pyramid...")
    try:
        generate_tiles_optimized(image_path, tiles_dir)
    except Exception as e:
        print(f"Error generating tiles: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✓ COMPLETE!")
    print("=" * 60)
    print(f"\nTiles are ready in: {tiles_dir}")


if __name__ == "__main__":
    main()
