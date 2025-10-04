# Tile Generation Guide

This guide explains how to process the real NASA Andromeda image and generate an optimized tile pyramid for the Astro-Zoom viewer.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements_tiling.txt

# 2. Run the tile generator
python process_real_image.py
```

The script will:

1. Download the 209MB NASA Andromeda image (42208x9870 pixels)
2. Generate a multi-resolution tile pyramid
3. Create optimized JPEG tiles (progressive, quality 85)
4. Update the DZI metadata with actual dimensions

**Processing time:** 10-30 minutes depending on CPU

## What Gets Generated

### Image Details

- **Source:** NASA Hubble Andromeda Mosaic 2025
- **Dimensions:** 42208 x 9870 pixels
- **File size:** ~209MB original
- **URL:** https://assets.science.nasa.gov/content/dam/science/missions/hubble/galaxies/andromeda/Hubble_M31Mosaic_2025_42208x9870_STScI-01JGY8MZB6RAYKZ1V4CHGN37Q6.jpg

### Tile Pyramid Structure

```
tiles/andromeda/
├── info.dzi           # Deep Zoom Image metadata
├── 0/                 # Level 0 (lowest resolution, 1 tile)
│   └── 0_0.jpg
├── 1/                 # Level 1 (2x2 tiles)
│   ├── 0_0.jpg
│   ├── 0_1.jpg
│   ├── 1_0.jpg
│   └── 1_1.jpg
├── 2/                 # Level 2 (4x4 tiles)
├── 3/                 # Level 3 (8x8 tiles)
...
└── N/                 # Level N (highest resolution)
```

### Optimization Features

1. **Progressive JPEG**
   - Tiles load progressively for better perceived performance
   - Ideal for web delivery

2. **Quality Settings**
   - 85% JPEG quality (good balance of size vs quality)
   - Optimize flag enabled for smaller file sizes

3. **Tile Overlap**
   - 1-pixel overlap prevents seams at tile boundaries
   - Ensures smooth zooming experience

4. **Memory Efficient**
   - Processes levels sequentially
   - Doesn't load entire image at once
   - Suitable for machines with limited RAM

5. **Resume Support**
   - Download can be resumed if interrupted
   - Existing tiles are not regenerated

## Advanced Options

### Custom Configuration

Edit the script to change these settings:

```python
TILE_SIZE = 256          # Size of each tile (default: 256x256)
TILE_OVERLAP = 1         # Overlap in pixels (default: 1)
TILE_QUALITY = 85        # JPEG quality 0-100 (default: 85)
TILE_FORMAT = "jpg"      # Format: jpg, png, webp
```

### Manual Download

If automatic download fails, manually download from:
https://assets.science.nasa.gov/content/dam/science/missions/hubble/galaxies/andromeda/Hubble_M31Mosaic_2025_42208x9870_STScI-01JGY8MZB6RAYKZ1V4CHGN37Q6.jpg

Save as: `infra/downloads/andromeda_hubble_2025.jpg`

Then run the script again.

## Performance Tips

### For Faster Processing

1. **Use SSD storage** - Significant speedup vs HDD
2. **More CPU cores** - Pillow uses multiple cores for image operations
3. **Adequate RAM** - Recommended 8GB+ for smooth processing
4. **Close other apps** - Free up system resources

### Expected Processing Times

| System             | Approx. Time |
| ------------------ | ------------ |
| Mac M1/M2          | 10-15 min    |
| Modern Intel i7/i9 | 15-20 min    |
| Older systems      | 20-30 min    |

## Troubleshooting

### Out of Memory

If you get memory errors:

1. Close other applications
2. Restart and try again
3. Consider using a machine with more RAM

### Slow Download

The image is 209MB. On slow connections:

- Be patient, it may take 10-30 minutes
- Download can be resumed if interrupted
- Consider manual download (see above)

### Corrupted Image

If the image fails to process:

```bash
# Delete and re-download
rm infra/downloads/andromeda_hubble_2025.jpg
python process_real_image.py
```

## Comparing Old vs New

### Old (Mock Data)

- Dimensions: 1024 x 1024
- Tiles: 21 (3 zoom levels)
- Generated star field pattern
- Demo purposes only

### New (Real NASA Image)

- Dimensions: 42208 x 9870
- Tiles: 1000+ (multiple zoom levels)
- Actual Hubble Space Telescope data
- Production quality

## Verification

After generation completes:

```bash
# Check DZI metadata
cat infra/tiles/andromeda/info.dzi

# Count tiles
find infra/tiles/andromeda -name "*.jpg" | wc -l

# Check highest zoom level
ls infra/tiles/andromeda/ | sort -n | tail -1
```

## Next Steps

1. **Start the services:**

   ```bash
   pnpm dev
   ```

2. **Open the viewer:**
   http://localhost:3000

3. **Enjoy exploring!**
   - Pan/zoom the real Andromeda galaxy
   - Notice the incredible detail
   - Try AI search: "bright star cluster"
   - Add annotations to interesting features

## Technical Details

### DZI Format

The Deep Zoom Image format uses a pyramid of tiles:

- Each level is half the dimensions of the next
- Level 0 is the smallest (base tile)
- Top level is the full resolution
- OpenSeadragon requests tiles as needed

### Why This Works

For a 42208x9870 image:

- Full resolution would be ~400MB in browser
- With tiles, only visible portion is loaded
- Smooth zooming by switching tile levels
- Thousands of tiles but only ~10-20 loaded at once

## Resources

- [OpenSeadragon Docs](https://openseadragon.github.io/)
- [Deep Zoom Format](<https://docs.microsoft.com/en-us/previous-versions/windows/silverlight/dotnet-windows-silverlight/cc645050(v=vs.95)>)
- [Pillow Documentation](https://pillow.readthedocs.io/)
