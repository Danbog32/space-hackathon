# Universal COG Conversion System

This implementation provides a complete Cloud Optimized GeoTIFF (COG) conversion and serving system that can handle multiple input formats including .IMG, .TIF, .JPG, .PNG, and other standard image formats.

## 🌟 Features

### Universal Format Support
- **.IMG files** (PDS/Planetary Data System format)
- **.TIF/.TIFF files** (GeoTIFF format)
- **.JPG/.JPEG files** (Standard JPEG images)
- **.PNG files** (Portable Network Graphics)
- **.BMP, .GIF, .WebP** (Additional standard formats)

### COG Optimization
- **Internal tiling** (512x512 blocks for optimal performance)
- **Automatic overviews** (Multiple zoom levels)
- **Compression** (LZW, DEFLATE, JPEG, WebP options)
- **HTTP range request support** (Efficient web serving)
- **Metadata preservation** (All scientific data maintained)

### API Integration
- **Seamless integration** with existing DZI system
- **Automatic fallback** (COG → DZI → Error)
- **Performance optimization** (WebP content negotiation)
- **Validation endpoints** (COG compliance checking)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install COG-specific dependencies
pip install -r infra/requirements-cog.txt

# Or install individually
pip install rasterio rio-cogeo Pillow numpy
```

### 2. Convert Images to COG

```bash
# Convert a single file
python3 infra/universal_cog_converter.py mars_scan.img

# Convert with specific compression
python3 infra/universal_cog_converter.py planetary_data.tif -c lzw

# Batch convert directory
python3 infra/universal_cog_converter.py infra/source_images/ -b
```

### 3. Validate COG Files

```bash
# Validate a single COG
python3 infra/cog_validator.py mars_scan.cog.tif

# Batch validate directory
python3 infra/cog_validator.py infra/cogs/ -b

# Generate detailed report
python3 infra/cog_validator.py mars_scan.cog.tif --report
```

### 4. Start Your API

```bash
# Start the development server
pnpm dev
```

### 5. Test COG Endpoints

```bash
# Test COG info endpoint
curl http://localhost:8000/tiles/mars_scan/cog/info

# Test COG validation
curl http://localhost:8000/tiles/mars_scan/cog/validate

# Test COG tile serving
curl http://localhost:8000/tiles/mars_scan/cog/0/0_0.jpg
```

## 📁 File Structure

```
infra/
├── universal_cog_converter.py    # Main conversion script
├── cog_validator.py              # COG validation utilities
├── cog_examples.py               # Usage examples
├── requirements-cog.txt          # COG dependencies
└── cogs/                         # Output directory for COG files
    ├── mars_scan.cog.tif
    ├── planetary_data.cog.tif
    └── conversion_report.md
```

## 🔧 API Endpoints

### COG-Specific Endpoints

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /tiles/{id}/cog/info` | COG metadata | `/tiles/mars_scan/cog/info` |
| `GET /tiles/{id}/cog/validate` | COG validation | `/tiles/mars_scan/cog/validate` |
| `GET /tiles/{id}/cog/{level}/{col}_{row}.{ext}` | COG tiles | `/tiles/mars_scan/cog/0/0_0.jpg` |

### Enhanced Existing Endpoints

| Endpoint | Enhancement | Description |
|----------|-------------|-------------|
| `GET /tiles/{id}/info.dzi` | COG support | Generates DZI from COG metadata |
| `GET /tiles/{id}/{level}/{col}_{row}.{ext}` | COG fallback | Serves COG tiles if available |
| `GET /tiles/{id}/thumbnail.jpg` | COG support | Generates thumbnails from COG |

## 💾 Database Schema Updates

The `Dataset` model has been enhanced with COG support:

```python
class Dataset(SQLModel, table=True):
    # ... existing fields ...
    tile_type: str = Field(default="dzi")  # Now supports "cog"
    source_format: Optional[str] = None     # Original format (IMG, TIF, etc.)
    source_file: Optional[str] = None       # Path to source file
    cog_file: Optional[str] = None          # Path to COG file
    is_dynamic: bool = Field(default=False) # Dynamic processing flag
```

## 🎯 Usage Examples

### Convert Planetary .IMG File

```python
from universal_cog_converter import UniversalCOGConverter

converter = UniversalCOGConverter(output_dir="infra/cogs")

# Convert .IMG to COG
result = converter.convert_image(
    "mars_orbital_scan.img",
    compression="lzw"  # Lossless for scientific data
)

if result["success"]:
    print(f"✓ Created: {result['output_path']}")
```

### Batch Convert Multiple Formats

```python
# Convert all supported files in directory
results = converter.batch_convert(
    "infra/source_images/",
    pattern="*",
    compression="lzw"
)

# Generate conversion report
report = converter.generate_conversion_report(results)
```

### Validate COG Files

```python
from cog_validator import COGValidator

validator = COGValidator()

# Validate single COG
result = validator.validate_cog("mars_scan.cog.tif")

if result["valid"]:
    print("✓ Valid COG")
else:
    print("✗ Invalid COG")
    print(f"Error: {result['error']}")
```

### API Integration

```python
# Your existing DeepZoomViewer will work unchanged!
# Just point it to datasets with COG files

const tileSource = `${API_URL}/tiles/${datasetId}/info.dzi`;
// Automatically serves COG tiles if available
```

## 🔍 Validation Features

### COG Compliance Checks
- ✅ **Tiled structure** (Internal 512x512 blocks)
- ✅ **Compression** (LZW, DEFLATE, etc.)
- ✅ **Overviews** (Multiple zoom levels)
- ✅ **Performance** (Tile reading speed test)
- ✅ **Metadata** (Coordinate system, bounds, etc.)

### Optimization Recommendations
- Block size optimization
- Compression suggestions
- Overview level recommendations
- Performance improvements

## 📊 Performance Benefits

### Storage Efficiency
| Format | File Count | Storage | Overhead |
|--------|------------|---------|----------|
| **DZI Tiles** | 10,000+ files | 2-3x original | High |
| **COG** | 1 file | 1.2-1.5x original | Low |

### Serving Performance
| Metric | DZI Tiles | COG | Improvement |
|--------|-----------|-----|-------------|
| **Initial Load** | 200-500ms | 50-100ms | 3-5x faster |
| **Pan/Zoom** | 50-100ms | 10-30ms | 2-3x faster |
| **CDN Compatibility** | Poor | Excellent | Global distribution |
| **Bandwidth** | High | 30-50% less | Significant savings |

## 🛠️ Advanced Configuration

### Compression Options

```python
# Lossless compression (recommended for scientific data)
compression="lzw"

# Lossy compression (smaller files)
compression="jpeg"

# Modern compression
compression="webp"
```

### Custom COG Profiles

```python
# Custom profile for specific use cases
profile = {
    'driver': 'GTiff',
    'tiled': True,
    'blockxsize': 512,
    'blockysize': 512,
    'compress': 'lzw',
    'interleave': 'pixel',
    'bigtiff': 'yes'  # For files > 4GB
}
```

## 🔧 Troubleshooting

### Common Issues

1. **"COG support not available"**
   ```bash
   pip install rasterio rio-cogeo
   ```

2. **"File not found" errors**
   - Check file paths
   - Ensure COG files are in `infra/cogs/`
   - Verify file permissions

3. **Slow tile serving**
   - Validate COG files: `python3 infra/cog_validator.py infra/cogs/`
   - Check block size (should be 512x512)
   - Verify compression settings

4. **Memory issues with large files**
   - Use `in_memory=False` in conversion
   - Enable BigTIFF for files > 4GB
   - Process files in smaller batches

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
converter = UniversalCOGConverter()
converter.convert_image("your_file.img")
```

## 📈 Monitoring and Analytics

### COG Metrics
- File size reduction
- Conversion success rate
- Validation compliance rate
- Serving performance metrics

### API Monitoring
- Tile request latency
- Cache hit rates
- Error rates by format
- Bandwidth usage

## 🚀 Production Deployment

### CDN Integration
```python
# COG files work perfectly with CDNs
cdn_config = {
    "cache_control": "public, max-age=31536000",
    "range_requests": True,
    "global_distribution": True
}
```

### Scaling Considerations
- COG files are CDN-friendly
- Single file per dataset
- HTTP range request support
- Automatic overview generation

## 📚 Additional Resources

- [Cloud Optimized GeoTIFF Specification](https://www.cogeo.org/)
- [rasterio Documentation](https://rasterio.readthedocs.io/)
- [rio-cogeo Documentation](https://github.com/cogeotiff/rio-cogeo)
- [GDAL COG Driver](https://gdal.org/drivers/raster/cog.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This implementation is part of the Astro-Zoom project and follows the same license terms.
