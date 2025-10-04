# Dataset Upgrade: From Mock to Real NASA Data

This document explains the dataset upgrade from mock sample tiles to the real 209MB NASA Andromeda image.

## Summary

The system has been upgraded to support the actual NASA Hubble Andromeda mosaic image:

- **Original Mock:** 1024x1024 pixels, 21 synthetic tiles
- **Real NASA Data:** 42208x9870 pixels, 1000+ high-resolution tiles
- **File Size:** 209MB original image
- **Source:** NASA Hubble Space Telescope

## What Was Changed

### 1. Tile Generation Script (`infra/process_real_image.py`)

A comprehensive tile generation system that:

- Downloads the NASA image automatically (with resume support)
- Generates multi-level tile pyramid (Deep Zoom Image format)
- Optimizes tiles for web delivery (progressive JPEG, quality 85)
- Creates proper DZI metadata with actual dimensions
- Memory-efficient processing for large images

**Key Features:**

- Progress bars for download and processing
- Error handling and retry logic
- Configurable tile size, overlap, and quality
- Automatic DZI descriptor generation

### 2. Tile Optimization Script (`infra/optimize_tiles.py`)

Additional optimizations for performance:

- WebP conversion (25-35% smaller than JPEG)
- Tile analysis and statistics
- Preload manifest generation for critical tiles
- Cache header recommendations

**Usage:**

```bash
# Analyze current tiles
python infra/optimize_tiles.py --analyze

# Generate WebP versions
python infra/optimize_tiles.py --webp

# Generate preload manifest
python infra/optimize_tiles.py --preload

# Run all optimizations
python infra/optimize_tiles.py --all
```

### 3. Smart Dataset Detection (`apps/api/app/seed.py`)

The database seeding now automatically detects whether real or mock data is being used:

- Reads the DZI file to determine image dimensions
- Sets appropriate metadata (name, description, date)
- Marks dataset as real or mock for analytics

**Auto-detection:**

- Real image: 42208x9870 → "Andromeda Galaxy (NASA Hubble 2025)"
- Mock image: 1024x1024 → "Andromeda Galaxy (Sample)"

### 4. WebP Content Negotiation (`apps/api/app/routers/tiles.py`)

Enhanced tile serving with:

- Automatic WebP serving to supporting browsers
- Proper cache headers (`immutable`, 1-year expiry)
- Vary header for correct proxy caching
- Transparent fallback to JPEG

**Benefits:**

- 25-35% bandwidth reduction with WebP
- Faster load times
- Better browser caching
- No client-side changes required

## How to Use

### Option 1: Use Mock Data (Default)

The project works out of the box with mock sample tiles:

```bash
pnpm dev
```

### Option 2: Upgrade to Real NASA Data

Process the real image:

```bash
# Install tiling dependencies
pip install -r infra/requirements_tiling.txt

# Download and process (10-30 minutes)
python infra/process_real_image.py

# Optional: Generate WebP tiles for extra optimization
python infra/optimize_tiles.py --webp

# Restart services to pick up new tiles
pnpm dev
```

## Performance Comparison

### Before (Mock Data)

- Image: 1024x1024 pixels
- Tiles: 21 files
- Total Size: ~5MB
- Zoom Levels: 3
- Load Time: <1s

### After (Real NASA Data)

- Image: 42208x9870 pixels
- Tiles: 1000+ files
- Total Size: ~200MB (all tiles), ~20MB (level 0-4)
- Zoom Levels: 10+
- Load Time: ~2-3s (only visible tiles loaded)

**With WebP optimization:**

- Total Size: ~140MB (30% reduction)
- Load Time: ~1.5-2s
- Bandwidth savings: 60MB per full view

## Optimizations Implemented

### 1. Progressive JPEG

- Tiles load in multiple passes
- Better perceived performance
- No additional code required

### 2. Tile Overlap

- 1-pixel overlap prevents seams
- Ensures smooth zooming
- Standard DZI practice

### 3. Cache Headers

- 1-year expiry for immutable tiles
- `Cache-Control: public, immutable`
- Browser and proxy caching

### 4. WebP Support

- Transparent content negotiation
- 25-35% smaller than JPEG
- Same visual quality
- Automatic fallback

### 5. Lazy Loading

- Only visible tiles are loaded
- OpenSeadragon handles efficiently
- Reduces initial bandwidth

### 6. Level-of-Detail (LOD)

- Multiple resolution levels
- Quick low-res preview
- High-res on demand
- Smooth zoom transitions

## Technical Details

### DZI Format

Deep Zoom Image format pyramid:

```
Level 0:  1 tile   (256x256)    → Full image at 1/512 scale
Level 1:  4 tiles  (2x2)        → 1/256 scale
Level 2:  16 tiles (4x4)        → 1/128 scale
...
Level N:  Many tiles            → Full resolution
```

### Tile Naming Convention

```
{dataset_id}/{level}/{col}_{row}.{ext}

Example:
andromeda/8/42_13.jpg
```

### HTTP Response Headers

```http
Cache-Control: public, max-age=31536000, immutable
Vary: Accept
Content-Type: image/webp
```

## Monitoring Performance

### Browser DevTools

Check Network tab:

- Tiles should have `304 Not Modified` on reload
- WebP tiles for Chrome/Edge/Firefox
- JPEG fallback for Safari (pre-2020)

### Server Logs

Monitor tile requests:

- High cache hit rate is good
- Watch for 404s (missing tiles)
- Check for WebP usage

### Expected Metrics

First view:

- ~10-20 tile requests
- ~2-5MB transferred
- ~2-3s load time

Subsequent views:

- 0 tile requests (cached)
- 0 bytes transferred
- Instant load

## Troubleshooting

### Problem: Tiles not loading

**Solution:**

1. Check DZI file exists: `infra/tiles/andromeda/info.dzi`
2. Verify tile structure: `ls infra/tiles/andromeda/`
3. Check API logs for errors
4. Confirm TILE_BASE environment variable

### Problem: Out of memory during generation

**Solution:**

1. Close other applications
2. Use a machine with more RAM (8GB+ recommended)
3. Process in smaller chunks (contact for custom script)

### Problem: Slow download

**Solution:**

1. Use manual download (see TILE_GENERATION.md)
2. Wait patiently (209MB takes time)
3. Resume is automatic if interrupted

### Problem: WebP not serving

**Solution:**

1. Verify WebP tiles exist: `ls infra/tiles/andromeda/*/*.webp`
2. Check browser supports WebP (Chrome, Firefox, Edge)
3. Inspect response headers for `Content-Type: image/webp`

## Future Enhancements

Potential improvements:

- [ ] HTTP/2 push for critical tiles
- [ ] Brotli compression for tile metadata
- [ ] Service worker for offline caching
- [ ] AVIF format support (even smaller)
- [ ] Adaptive quality based on network speed
- [ ] Tile preloading based on pan velocity
- [ ] WebAssembly JPEG decoder for faster client rendering

## References

- [NASA Image Source](https://assets.science.nasa.gov/content/dam/science/missions/hubble/galaxies/andromeda/)
- [Deep Zoom Format Specification](<https://docs.microsoft.com/en-us/previous-versions/windows/silverlight/dotnet-windows-silverlight/cc645050(v=vs.95)>)
- [OpenSeadragon Documentation](https://openseadragon.github.io/)
- [WebP Format](https://developers.google.com/speed/webp)
- [Progressive JPEG](https://www.industrialempathy.com/posts/progressive-jpegs/)

## Questions?

See also:

- `infra/TILE_GENERATION.md` - Detailed tile generation guide
- `README.md` - General project documentation
- `PROJECT_OVERVIEW.md` - Architecture overview
