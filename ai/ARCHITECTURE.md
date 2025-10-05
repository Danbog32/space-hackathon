# 🏗️ AI Service Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│                     http://localhost:3000                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                          │
│  - OpenSeadragon Viewer                                          │
│  - Search UI Component                                           │
│  - Annotation Tools                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    API SERVICE (FastAPI)                         │
│                   http://localhost:8000                          │
│                                                                   │
│  Routes:                                                         │
│  • GET  /datasets          → List datasets                       │
│  • GET  /datasets/{id}     → Dataset details                     │
│  • GET  /search            → Proxy to AI service ───────┐       │
│  • GET  /tiles/*           → Serve DZI tiles            │       │
│  • POST /annotations       → Save annotations           │       │
│  • GET  /annotations       → List annotations           │       │
└─────────────────────────────────────────────────────────────────┘
                                                          │
                             ┌────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    AI SERVICE (FastAPI)                          │
│                   http://localhost:8001                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    CLIP MODEL                             │  │
│  │  • Encode text queries   → 512-dim vectors               │  │
│  │  • Encode image patches  → 512-dim vectors               │  │
│  │  • Auto device detection (CUDA/CPU/MPS)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  FAISS INDEX                              │  │
│  │  • Fast vector similarity search                         │  │
│  │  • <10ms query latency                                   │  │
│  │  • Stores embeddings for all patches                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 METADATA STORE                            │  │
│  │  • Patch locations (bbox)                                │  │
│  │  • Tile coordinates                                      │  │
│  │  • Zoom levels                                           │  │
│  │  • Quality metrics                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            SAM (Segment Anything) - STRETCH               │  │
│  │  • Point-based segmentation                              │  │
│  │  • Bounding box segmentation                             │  │
│  │  • Assisted annotation masks                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         DATA STORAGE                             │
│                                                                   │
│  📁 infra/tiles/                                                 │
│     └── andromeda/                                               │
│         ├── info.dzi          ← DZI descriptor                   │
│         ├── 0/0_0.jpg         ← Zoom level 0 (1 tile)           │
│         ├── 1/               ← Zoom level 1 (4 tiles)           │
│         │   ├── 0_0.jpg                                          │
│         │   ├── 0_1.jpg                                          │
│         │   ├── 1_0.jpg                                          │
│         │   └── 1_1.jpg                                          │
│         └── 2/               ← Zoom level 2 (16 tiles)          │
│                                                                   │
│  📁 ai/data/                                                     │
│     ├── andromeda.faiss      ← Vector index                      │
│     ├── andromeda_metadata.json  ← Dataset info                 │
│     ├── andromeda_patches.json   ← Patch metadata               │
│     └── thumbnails/          ← Result preview images            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Search Query

```
1. USER TYPES: "star cluster"
        ↓
2. FRONTEND sends: GET /search?q=star%20cluster&datasetId=andromeda
        ↓
3. API SERVICE proxies to AI service
        ↓
4. AI SERVICE:
   a) CLIP encodes "star cluster" → [0.23, -0.45, 0.12, ...] (512 dims)
   b) FAISS searches index → finds top-k similar patches
   c) Looks up metadata → gets bbox coordinates
   d) Returns: [
        {
          "rank": 1,
          "score": 0.87,
          "bbox": [512, 256, 128, 128],  // x, y, width, height
          "metadata": {...}
        },
        ...
      ]
        ↓
5. FRONTEND receives results
   → Converts bbox to OpenSeadragon coordinates
   → Draws pins/highlights on image
   → User can click to "jump to" result
```

---

## Data Flow: Index Building

```
1. LARGE IMAGE (e.g., 10,000 × 10,000 px)
        ↓
2. TILE GENERATOR creates DZI pyramid
   → Level 0: 1 tile (256×256)
   → Level 1: 4 tiles (2×2 grid)
   → Level 2: 16 tiles (4×4 grid)
   → ...
        ↓
3. PATCH EXTRACTOR (your code!)
   For each tile:
   a) Extract patches at multiple scales (64×64, 128×128, 256×256)
   b) Filter low-quality patches (uniform regions, blank areas)
   c) Optional: Use interest point detection (corners, edges)
        ↓
4. CLIP ENCODER (your code!)
   For each patch:
   a) Resize/normalize image
   b) Encode with CLIP → 512-dim vector
   c) Store in batch for efficiency
        ↓
5. FAISS INDEXER (your code!)
   a) Collect all vectors: shape = (N, 512)
   b) Build FAISS index (IndexFlatIP for inner product similarity)
   c) Save to disk: andromeda.faiss
        ↓
6. METADATA MANAGER (your code!)
   a) Save patch locations, tile coords, zoom levels
   b) Save to JSON: andromeda_patches.json
        ↓
7. INDEX READY for search! ✅
```

---

## Component Responsibilities

### 🔧 Your Code (Misha)

**models/clip_model.py**
- Load CLIP model
- Encode text queries
- Encode image patches
- Auto-detect GPU/CPU

**utils/patch_extractor.py**
- Extract patches from images
- Multi-scale sampling (64, 128, 256)
- Quality filtering (variance, edges)
- Interest point detection
- Hierarchical sampling

**utils/faiss_helper.py**
- Create FAISS indices
- Add vectors to index
- Search similar vectors
- Manage multiple datasets
- Load/save indices

**app.py** (main service)
- `/search` endpoint
- `/datasets` endpoint
- `/embed` endpoint
- Result caching
- Error handling

**build_real_index.py**
- Index building pipeline
- Process DZI tiles
- Batch encoding
- Metadata management

**sam_integration.py** (stretch)
- Load SAM model
- Point-based segmentation
- Bbox-based segmentation

---

## Key Algorithms

### 1. CLIP Text-Image Similarity

```python
# Text query
text_embed = CLIP.encode_text("star cluster")  # → [512 dims]

# Image patches
patch_embeds = [CLIP.encode_image(patch) for patch in patches]  # → N × [512 dims]

# Similarity (cosine similarity via dot product, vectors are normalized)
similarities = [np.dot(text_embed, patch_embed) for patch_embed in patch_embeds]

# Higher score = more similar
```

### 2. FAISS Similarity Search

```python
# Build index
index = faiss.IndexFlatIP(512)  # Inner Product (for normalized vectors = cosine sim)
index.add(patch_embeds)  # Add all N patch embeddings

# Search
query_vector = CLIP.encode_text("star cluster")
k = 10
scores, indices = index.search(query_vector.reshape(1, -1), k)
# Returns: top-k most similar patches with scores
```

### 3. Non-Maximum Suppression (NMS)

```python
# Problem: Many overlapping results at same location
# Solution: Keep highest-scoring result, suppress nearby ones

def nms(boxes, scores, iou_threshold=0.5):
    """
    boxes: [[x, y, w, h], ...]
    scores: [0.9, 0.8, 0.7, ...]
    """
    # Sort by score (descending)
    order = np.argsort(scores)[::-1]
    
    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)  # Keep highest score
        
        # Calculate IoU with remaining boxes
        ious = calculate_iou(boxes[i], boxes[order[1:]])
        
        # Remove overlapping boxes
        order = order[1:][ious < iou_threshold]
    
    return keep
```

---

## Coordinate Systems

### DZI Tile Coordinates

```
Level 0: 1 tile (256×256)
  [0, 0]

Level 1: 4 tiles (512×512 total)
  [0, 0]  [1, 0]
  [0, 1]  [1, 1]

Level 2: 16 tiles (1024×1024 total)
  [0,0] [1,0] [2,0] [3,0]
  [0,1] [1,1] [2,1] [3,1]
  [0,2] [1,2] [2,2] [3,2]
  [0,3] [1,3] [2,3] [3,3]
```

### Patch to Global Coordinates

```python
# Patch in tile
tile_x, tile_y = 1, 1  # Which tile
local_x, local_y = 64, 32  # Position within tile
patch_size = 128
level = 2  # Zoom level

# Convert to global image coordinates
tile_size = 256
scale = 2 ** level

global_x = (tile_x * tile_size + local_x) * scale
global_y = (tile_y * tile_size + local_y) * scale

# This gives position in the full-resolution image
```

### OpenSeadragon Coordinates

```javascript
// OpenSeadragon uses normalized coordinates [0, 1]
// Convert global pixel coords to OSD coords:

const imageWidth = 1024;  // Full image width
const imageHeight = 1024;

const osdX = globalX / imageWidth;  // 0.0 to 1.0
const osdY = globalY / imageHeight;

// In OSD:
viewer.viewport.panTo(new OpenSeadragon.Point(osdX, osdY));
```

---

## Performance Targets

| Operation              | Target         | Typical (CPU) | Typical (GPU) |
| ---------------------- | -------------- | ------------- | ------------- |
| CLIP text encode       | <20ms          | 15ms          | 5ms           |
| CLIP image encode      | <50ms          | 40ms          | 10ms          |
| CLIP batch (32 images) | <500ms         | 800ms         | 150ms         |
| FAISS search (10k vecs)| <10ms          | 5ms           | 5ms           |
| Search (cached)        | <10ms          | 8ms           | 8ms           |
| Search (cold)          | <1000ms        | 800ms         | 200ms         |
| Index build (1000 imgs)| <5min          | 8min          | 2min          |

---

## File Sizes (Approximate)

| Item                      | Size           |
| ------------------------- | -------------- |
| CLIP model (ViT-B-32)     | ~350 MB        |
| FAISS index (10k vectors) | ~20 MB         |
| Metadata JSON (10k)       | ~5 MB          |
| Sample tiles (21 tiles)   | ~2 MB          |
| SAM checkpoint (ViT-B)    | ~375 MB        |

---

## API Endpoints (Your Responsibility)

### GET `/health`
```json
{
  "status": "ok",
  "datasets": 1,
  "total_vectors": 1500,
  "clip_ready": true,
  "index_manager_ready": true
}
```

### GET `/datasets`
```json
{
  "datasets": [
    {
      "id": "andromeda",
      "num_vectors": 1500,
      "embedding_dim": 512,
      "created_at": "2025-10-04T12:00:00",
      "last_updated": "2025-10-04T14:30:00"
    }
  ]
}
```

### GET `/search?q=star&dataset_id=andromeda&k=10`
```json
{
  "query": "star",
  "dataset_id": "andromeda",
  "k": 10,
  "count": 8,
  "results": [
    {
      "id": 42,
      "rank": 1,
      "score": 0.87,
      "bbox": [512, 256, 128, 128],
      "previewThumb": null,
      "metadata": {
        "tile_file": "2_1.jpg",
        "level": 2,
        "patch_size": 128,
        "center": [576, 320]
      }
    },
    ...
  ],
  "search_time_ms": 45.2,
  "cached": false
}
```

### GET `/embed?text=galaxy`
```json
{
  "text": "galaxy",
  "embedding_dim": 512,
  "embedding": [0.23, -0.45, 0.12, ..., 0.67]
}
```

### POST `/segment` (stretch)
```json
{
  "image_data": "base64_encoded_image",
  "points": [[100, 100], [200, 200]],
  "labels": [1, 0],
  "bbox": [50, 50, 300, 300]
}
```

Response:
```json
{
  "success": true,
  "mask": "base64_encoded_mask_image",
  "points": [[100, 100], [200, 200]],
  "labels": [1, 0]
}
```

---

## Dependencies

```
fastapi         →  Web framework
uvicorn         →  ASGI server
open_clip_torch →  CLIP model
torch           →  Deep learning framework
faiss-cpu       →  Vector similarity search
pillow          →  Image processing
numpy           →  Numerical computing
opencv-python   →  Image processing (optional)
scikit-image    →  Interest point detection (optional)
segment-anything → SAM segmentation (stretch)
```

---

## Testing Strategy

### Unit Tests
- `test_clip_model.py` - CLIP encoding works
- `test_patch_extractor.py` - Patches extracted correctly
- `test_faiss_helper.py` - Index creation/search works

### Integration Tests
- `test_ai_service.py` - API endpoints return correct format
- `test_search_quality.py` - Search results are relevant

### Manual Tests
- Search for "star" → results make sense
- Search for "dust" → different results
- Coordinates display correctly on map
- Performance is acceptable

---

## Common Pitfalls & Solutions

### ❌ Problem: CUDA out of memory
**Solution:** Use CPU or smaller batch size
```python
clip = ClipEncoder(device="cpu")
batch_size = 8  # Instead of 32
```

### ❌ Problem: Search returns random results
**Solution:** Check vectors are normalized
```python
# In CLIP encoder, ensure:
feats = feats / feats.norm(dim=-1, keepdim=True)
```

### ❌ Problem: Coordinates don't match image
**Solution:** Verify tile size and level calculation
```python
# Check DZI info.dzi for tile size
# Ensure scale factor is correct: 2 ** level
```

### ❌ Problem: Service is slow
**Solutions:**
1. Enable caching (already implemented)
2. Use GPU if available
3. Reduce number of patches indexed
4. Use smaller CLIP model (ViT-B-32 vs ViT-L-14)

---

**This architecture is WORKING! Focus on optimization & integration! 🚀**

