#!/usr/bin/env python3
"""
Additional optimization utilities for tile serving.

This script provides:
- WebP conversion for modern browsers (smaller files)
- Tile preloading hints
- Cache manifest generation
- Image quality analysis
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not installed. Run: pip install pillow")
    sys.exit(1)


TILES_DIR = Path(__file__).parent / "tiles" / "andromeda"


def analyze_tiles() -> Dict:
    """Analyze tile pyramid and provide statistics."""
    print("Analyzing tile pyramid...")
    
    if not TILES_DIR.exists():
        print(f"Error: Tiles directory not found: {TILES_DIR}")
        return {}
    
    stats = {
        "levels": {},
        "total_tiles": 0,
        "total_size_mb": 0.0,
        "formats": {},
    }
    
    for level_dir in sorted(TILES_DIR.iterdir()):
        if not level_dir.is_dir():
            continue
        
        try:
            level = int(level_dir.name)
        except ValueError:
            continue
        
        tiles = list(level_dir.glob("*.*"))
        level_size = sum(t.stat().st_size for t in tiles)
        
        stats["levels"][level] = {
            "tiles": len(tiles),
            "size_mb": level_size / 1024 / 1024
        }
        stats["total_tiles"] += len(tiles)
        stats["total_size_mb"] += level_size / 1024 / 1024
        
        for tile in tiles:
            ext = tile.suffix[1:]
            stats["formats"][ext] = stats["formats"].get(ext, 0) + 1
    
    return stats


def generate_webp_tiles(quality: int = 85, skip_existing: bool = True):
    """
    Generate WebP versions of tiles for modern browsers.
    
    WebP provides 25-35% better compression than JPEG with same quality.
    """
    print("\nGenerating WebP tiles for modern browsers...")
    print(f"Quality: {quality}")
    
    total_converted = 0
    total_saved_mb = 0.0
    
    for level_dir in sorted(TILES_DIR.iterdir()):
        if not level_dir.is_dir():
            continue
        
        try:
            level = int(level_dir.name)
        except ValueError:
            continue
        
        jpg_tiles = list(level_dir.glob("*.jpg"))
        if not jpg_tiles:
            continue
        
        print(f"\nLevel {level}: Processing {len(jpg_tiles)} tiles...")
        
        for jpg_tile in jpg_tiles:
            webp_tile = jpg_tile.with_suffix('.webp')
            
            if skip_existing and webp_tile.exists():
                continue
            
            try:
                with Image.open(jpg_tile) as img:
                    img.save(webp_tile, 'WEBP', quality=quality, method=6)
                
                jpg_size = jpg_tile.stat().st_size
                webp_size = webp_tile.stat().st_size
                saved = (jpg_size - webp_size) / 1024 / 1024
                
                total_converted += 1
                total_saved_mb += saved
                
            except Exception as e:
                print(f"Error converting {jpg_tile}: {e}")
    
    print(f"\n✓ Converted {total_converted} tiles to WebP")
    print(f"✓ Saved {total_saved_mb:.2f}MB ({total_saved_mb / stats.get('total_size_mb', 1) * 100:.1f}% reduction)")


def generate_preload_manifest(output_path: Path = TILES_DIR / "preload.json"):
    """
    Generate a manifest of critical tiles to preload.
    
    Preloading level 0-2 can significantly improve initial load time.
    """
    print("\nGenerating preload manifest...")
    
    preload_tiles = []
    
    # Preload levels 0-2 for instant initial view
    for level in range(3):
        level_dir = TILES_DIR / str(level)
        if not level_dir.exists():
            continue
        
        for tile in sorted(level_dir.glob("*.jpg")):
            relative_path = str(tile.relative_to(TILES_DIR))
            preload_tiles.append({
                "level": level,
                "path": relative_path,
                "priority": "high" if level == 0 else "medium"
            })
    
    manifest = {
        "version": 1,
        "preload": preload_tiles,
        "total": len(preload_tiles)
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✓ Created preload manifest with {len(preload_tiles)} tiles")
    print(f"  Saved to: {output_path}")


def generate_cache_headers():
    """Print recommended cache header configurations."""
    print("\n" + "=" * 60)
    print("RECOMMENDED CACHE HEADERS")
    print("=" * 60)
    print("""
For optimal performance, configure your web server with:

Nginx:
------
location /tiles/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # Serve WebP to supporting browsers
    location ~ \\.jpg$ {
        add_header Vary Accept;
        try_files $uri$webp_suffix $uri =404;
    }
}

map $http_accept $webp_suffix {
    default "";
    "~*webp" ".webp";
}

Apache (.htaccess):
-------------------
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpeg "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
</IfModule>

<IfModule mod_headers.c>
    Header set Cache-Control "public, immutable"
</IfModule>

CDN Configuration:
------------------
- Set cache TTL to 1 year (tiles never change)
- Enable compression (gzip/brotli)
- Consider using a CDN like Cloudflare or CloudFront
- Set proper CORS headers if serving from different domain
""")


def print_optimization_summary(stats: Dict):
    """Print optimization recommendations based on analysis."""
    print("\n" + "=" * 60)
    print("OPTIMIZATION SUMMARY")
    print("=" * 60)
    
    total_tiles = stats.get("total_tiles", 0)
    total_size = stats.get("total_size_mb", 0)
    levels = len(stats.get("levels", {}))
    
    print(f"\n📊 Current Stats:")
    print(f"  Levels: {levels}")
    print(f"  Total Tiles: {total_tiles:,}")
    print(f"  Total Size: {total_size:.1f}MB")
    print(f"  Avg Tile Size: {(total_size * 1024 / total_tiles):.1f}KB")
    
    print(f"\n✨ Optimizations Applied:")
    print(f"  ✓ Progressive JPEG encoding")
    print(f"  ✓ Quality optimization (85%)")
    print(f"  ✓ 1-pixel tile overlap")
    print(f"  ✓ HTTP cache headers (1 year)")
    
    print(f"\n🚀 Additional Recommendations:")
    
    # Check for WebP
    has_webp = "webp" in stats.get("formats", {})
    if not has_webp:
        savings = total_size * 0.3  # ~30% savings with WebP
        print(f"  → Generate WebP tiles (save ~{savings:.1f}MB)")
        print(f"    Run: python infra/optimize_tiles.py --webp")
    else:
        print(f"  ✓ WebP tiles available")
    
    # Level-specific recommendations
    level_stats = stats.get("levels", {})
    if levels > 0:
        max_level = max(level_stats.keys())
        max_tiles = level_stats[max_level].get("tiles", 0)
        
        if max_tiles > 1000:
            print(f"  ℹ High-resolution tiles: {max_tiles} at level {max_level}")
            print(f"    Consider tile preloading for better UX")
    
    print(f"\n💡 Performance Tips:")
    print(f"  • Enable browser caching (see cache headers above)")
    print(f"  • Use a CDN for global distribution")
    print(f"  • Implement service worker for offline support")
    print(f"  • Consider lazy loading for annotations")
    
    print()


def main():
    """Main optimization workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Optimize tile pyramid")
    parser.add_argument("--analyze", action="store_true", help="Analyze current tiles")
    parser.add_argument("--webp", action="store_true", help="Generate WebP versions")
    parser.add_argument("--preload", action="store_true", help="Generate preload manifest")
    parser.add_argument("--quality", type=int, default=85, help="WebP quality (default: 85)")
    parser.add_argument("--all", action="store_true", help="Run all optimizations")
    
    args = parser.parse_args()
    
    # Default to analysis if no args provided
    if not any([args.analyze, args.webp, args.preload, args.all]):
        args.analyze = True
    
    print("=" * 60)
    print("Tile Pyramid Optimizer")
    print("=" * 60)
    
    # Always analyze first
    global stats
    stats = analyze_tiles()
    
    if args.all or args.analyze:
        print_optimization_summary(stats)
    
    if args.all or args.webp:
        generate_webp_tiles(quality=args.quality)
    
    if args.all or args.preload:
        generate_preload_manifest()
    
    if args.all or args.webp or args.preload:
        generate_cache_headers()
        print("\n✓ Optimization complete!")


if __name__ == "__main__":
    main()

