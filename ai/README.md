# AI Microservice for Space Imagery Analysis

Advanced AI-powered search and analysis for space imagery using CLIP embeddings, FAISS indexing, and SAM segmentation.

## Features

### 🔍 **Advanced Search**
- **Multi-scale patch extraction** (64x64, 128x128, 256x256)
- **CLIP-powered semantic search** with text queries
- **Quality filtering** to avoid uniform patches
- **Hierarchical sampling** for better coverage
- **Search result caching** for performance

### 🗂️ **Dataset Management**
- **Multi-dataset support** with separate indices
- **DZI tile processing** for deep zoom imagery
- **Metadata tracking** for patches and datasets
- **Incremental indexing** for new data

### 🎯 **Segmentation (SAM)**
- **Point-based segmentation** for precise annotations
- **Bounding box segmentation** for quick regions
- **Combined prompts** for complex shapes
- **Automatic mask generation** for assisted annotation

## Quick Start

### 1. Install Dependencies

```bash
cd ai
pip install -r requirements.txt
```

### 2. Build Index

```bash
# Build demo index (synthetic data)
python build_index.py --demo

# Build real index from space imagery
python build_index.py --real --dataset-id andromeda --tiles-dir ../infra/tiles
```

### 3. Start Service

```bash
python app.py
```

The service will be available at `http://localhost:8001`

## API Endpoints

### Search

```bash
# Basic search
curl "http://localhost:8001/search?q=star%20cluster&k=10"

# Search with filters
curl "http://localhost:8001/search?q=galaxy&dataset_id=andromeda&min_score=0.7&k=5"

# Get embedding for text
curl "http://localhost:8001/embed?text=spiral%20galaxy"
```

### Datasets

```bash
# List available datasets
curl "http://localhost:8001/datasets"

# Get model information
curl "http://localhost:8001/models/info"
```

### Segmentation (SAM)

```bash
# Check SAM status
curl "http://localhost:8001/sam/status"

# Generate segmentation mask
curl -X POST "http://localhost:8001/segment" \
  -H "Content-Type: application/json" \
  -d '{
    "image_data": "base64_encoded_image",
    "points": [[100, 100], [200, 200]],
    "labels": [1, 0],
    "bbox": [50, 50, 300, 300]
  }'
```

## Architecture

### Components

1. **CLIP Model** (`models/clip_model.py`)
   - Auto-device detection (CPU/CUDA/MPS)
   - Model caching and error handling
   - Batch processing support
   - Multiple model variants

2. **Patch Extractor** (`utils/patch_extractor.py`)
   - Multi-scale patch extraction
   - Quality filtering (variance, edge detection)
   - Interest point detection
   - Hierarchical sampling

3. **FAISS Manager** (`utils/faiss_helper.py`)
   - Multi-dataset index management
   - Metadata tracking
   - Incremental updates
   - Performance optimization

4. **SAM Integration** (`sam_integration.py`)
   - Point-based segmentation
   - Bounding box segmentation
   - Combined prompt support
   - Automatic checkpoint management

### Data Flow

```
Space Imagery → Patch Extraction → CLIP Encoding → FAISS Index
                     ↓
Text Query → CLIP Encoding → FAISS Search → Ranked Results
                     ↓
Results → Metadata Lookup → Bounding Boxes → Frontend
```

## Configuration

### Environment Variables

```bash
# Optional: Set device explicitly
export CUDA_VISIBLE_DEVICES=0

# Optional: Set cache directory
export CLIP_CACHE_DIR=~/.cache/clip
```

### Model Configuration

```python
# In models/clip_model.py
encoder = ClipEncoder(
    device="cuda",  # or "cpu", "mps", or None for auto
    model_name="ViT-B-32",  # or "ViT-L-14", "ViT-H-14"
    pretrained="laion2b_s34b_b79k"
)
```

### Patch Configuration

```python
# In build_real_index.py
extractor = PatchExtractor(
    patch_sizes=[64, 128, 256],
    stride_ratios=[0.5, 0.75, 1.0],
    quality_threshold=0.05,
    max_patches_per_scale=1000
)
```

## Performance

### Benchmarks

- **Patch Extraction**: ~1000 patches/second
- **CLIP Encoding**: ~50 patches/second (CPU), ~200 patches/second (GPU)
- **FAISS Search**: <10ms for 100K vectors
- **Search Cache**: 95% hit rate for repeated queries

### Memory Usage

- **CLIP Model**: ~1GB (ViT-B-32)
- **FAISS Index**: ~100MB per 10K vectors
- **Search Cache**: ~10MB for 1000 cached queries

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   ```bash
   # Use CPU instead
   export CUDA_VISIBLE_DEVICES=""
   python app.py
   ```

2. **SAM Model Not Found**
   ```bash
   # Download checkpoints
   mkdir -p checkpoints
   wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth -O checkpoints/
   ```

3. **No Datasets Found**
   ```bash
   # Build index first
   python build_index.py --demo
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python app.py
```

## Development

### Adding New Features

1. **New Patch Extractors**: Extend `PatchExtractor` class
2. **New Search Methods**: Add endpoints in `app.py`
3. **New Models**: Implement in `models/` directory
4. **New Datasets**: Use `DatasetIndexManager`

### Testing

```bash
# Run tests
python -m pytest tests/

# Test specific component
python -c "from models.clip_model import ClipEncoder; print('CLIP OK')"
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Open an issue on GitHub
- Contact the development team
