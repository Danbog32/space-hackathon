#!/usr/bin/env python3
"""
Process the NASA Earth image (Suomi NPP) and generate optimized Deep Zoom tiles.

Usage:
    python process_earth_image.py

This script will:
- Use a known direct image URL (preferred) or resolve from the NASA page
- Download to infra/downloads/earth_suomi_original.jpg
- Generate tiles into infra/tiles/earth/
- Create DZI metadata

Requirements:
    pip install -r infra/requirements_tiling.txt

"""
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: Required dependencies not installed. Please run: pip install requests")
    sys.exit(1)

# Local helpers from the generic tiler
from process_real_image import (
    DOWNLOAD_DIR,
    DATASETS_ROOT,
    download_image,
    get_image_info,
    generate_tiles_optimized,
)

NASA_PAGE_URL = (
    "https://images.nasa.gov/details/a-sky-view-of-earth-from-suomi-npp_16611703184_o"
)
# Provided direct original image URL (preferred)
DIRECT_IMAGE_URL = (
    "https://images-assets.nasa.gov/image/a-sky-view-of-earth-from-suomi-npp_16611703184_o/"
    "a-sky-view-of-earth-from-suomi-npp_16611703184_o~orig.jpg"
)
DEFAULT_FILENAME = "earth_suomi_original.jpg"
DATASET_ID = "earth"


def resolve_direct_image_url(page_url: str) -> str:
    """Attempt to find a direct image URL (jpg/jpeg/png) on the NASA page.

    Heuristics:
    - Fetch page HTML (with sensible timeout)
    - Find absolute URLs ending with common image extensions
    - Prefer URLs containing 'orig'/'original' or largest-looking dimensions in name
    - Fallback to the first match
    """
    resp = requests.get(page_url, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    html = resp.text

    # Collect candidate image links
    candidates = re.findall(r"https?://[^\s\"']+\.(?:jpg|jpeg|png)", html, re.IGNORECASE)
    if not candidates:
        # Some pages store asset JSON with escaped URLs; try unescaping then search again
        unescaped = html.encode("utf-8").decode("unicode_escape", errors="ignore")
        candidates = re.findall(r"https?://[^\s\"']+\.(?:jpg|jpeg|png)", unescaped, re.IGNORECASE)

    if not candidates:
        raise RuntimeError("Could not locate a direct image URL on the NASA page.")

    # Rank: prefer 'orig'/'original' and higher resolution hints
    def score(url: str) -> tuple:
        url_l = url.lower()
        s1 = 1 if ("orig" in url_l or "original" in url_l) else 0
        nums = [int(n) for n in re.findall(r"(\d{3,5})", url_l)]
        s2 = max(nums) if nums else 0
        return (s1, s2)

    best = sorted(set(candidates), key=score, reverse=True)[0]
    return best


def pick_image_url() -> str:
    """Prefer the known direct URL; fall back to resolving from the page."""
    # Try the direct URL first
    try:
        head = requests.head(DIRECT_IMAGE_URL, timeout=15, allow_redirects=True)
        if head.ok and int(head.headers.get("content-length", "1")) > 0:
            return DIRECT_IMAGE_URL
    except Exception:
        pass

    # Fallback: resolve from page
    return resolve_direct_image_url(NASA_PAGE_URL)


def main() -> None:
    print("=" * 60)
    print("NASA Earth Image Tile Generator (Suomi NPP)")
    print("=" * 60)
    print()

    # Resolve image URL
    try:
        image_url = pick_image_url()
        print(f"Using image: {image_url}")
    except Exception as e:
        print(f"Error determining image URL: {e}")
        print("Please open the NASA page, copy the Original image URL, and try:")
        print("  python process_real_image.py earth <DIRECT_IMAGE_URL> earth_suomi_original.jpg")
        sys.exit(1)

    # Prepare paths
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    image_path = DOWNLOAD_DIR / DEFAULT_FILENAME
    tiles_dir = DATASETS_ROOT / DATASET_ID

    # Download
    try:
        download_image(image_url, image_path)
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
    print("Next: restart API to seed Earth dataset if not present.")


if __name__ == "__main__":
    main()
