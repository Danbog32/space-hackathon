# 🤖 Misha's AI Tasks - Step-by-Step Guide

**Role:** AI Engineer  
**Focus:** CLIP embeddings, FAISS indexing, semantic search, (stretch) SAM segmentation

---

## 📋 Overview

You're responsible for the AI microservice that powers semantic search over space imagery using:
- **CLIP** (Contrastive Language-Image Pre-training) for embeddings
- **FAISS** (Facebook AI Similarity Search) for vector indexing
- **SAM** (Segment Anything Model) for assisted annotation (stretch goal)

---

## 🎯 Your Deliverables

1. ✅ **CLIP Model Integration** - Load and run CLIP for text/image embeddings
2. ✅ **Patch-level Extraction** - Extract 128×128 patches from large images
3. ✅ **FAISS Index Building** - Create searchable vector index
4. ✅ **Text Search Endpoint** - `/search?q=<query>` returns ranked results
5. ⏳ **Performance Optimization** - Improve recall, reduce latency, add caching
6. 🎁 **SAM Integration** (Stretch) - Segmentation mask assist on selected ROI

**Status:** Most infrastructure is DONE! You need to test, optimize, and integrate with real data.

---

## ⏰ Hour-by-Hour Tasks

### **H2-H6: First Pixels (AI POC)** ⏱️ 4 hours

#### **Step 1: Environment Setup & Testing (30 mins)**

```bash
# Navigate to AI directory
cd C:\Users\miked\space-hackathon\ai

# Check Python version (should be 3.9+)
python --version

# Install dependencies (if not already done)
pip install -r requirements.txt

# Test CLIP model loading
python -c "from models.clip_model import ClipEncoder; clip = ClipEncoder(); print('✅ CLIP loaded:', clip.get_model_info())"

# Test FAISS
python -c "import faiss; print('✅ FAISS version:', faiss.__version__)"
```

**Expected Output:**
- Python 3.9+
- All packages install successfully
- CLIP loads (may download model first time ~350MB)
- FAISS imports correctly

---

#### **Step 2: Build Initial Index on Sample Data (1 hour)**

**Option A: Quick Demo Index (for testing)**

```bash
# Build demo index with synthetic data
python build_index.py --demo

# This creates:
# - data/demo.faiss
# - data/demo_metadata.json
# - data/demo_patches.json
```

**Option B: Build Index from Real Tiles (recommended)**

```bash
# Build index from Andromeda sample tiles
python build_real_index.py \
  --dataset-id andromeda \
  --tiles-dir ../infra/tiles \
  --patch-sizes 64 128 256 \
  --max-patches 500

# This processes all tiles in ../infra/tiles/andromeda/
```

**What's happening:**
1. Loads CLIP model (auto-detects GPU/CPU)
2. Reads tiles from `../infra/tiles/andromeda/`
3. Extracts patches at multiple scales (64x64, 128x128, 256x256)
4. Filters low-quality patches (uniform/blank regions)
5. Encodes patches with CLIP → 512-dim vectors
6. Builds FAISS index for fast similarity search
7. Saves index + metadata to `data/` directory

**Expected Output:**
```
INFO - Initializing CLIP model...
INFO - CLIP model loaded: ViT-B-32 on cpu (or cuda)
INFO - Processing DZI dataset: andromeda
INFO - Extracting 128x128 patches...
INFO - Extracted 450 patches at scale 128x128
INFO - Saved dataset andromeda to data/andromeda.faiss
```

---

#### **Step 3: Start AI Service & Test Search (30 mins)**

```bash
# Start the AI microservice
python app.py

# Or use the batch file (Windows)
start_ai.bat
```

**Service should start on:** `http://localhost:8001`

**Test endpoints:**

```bash
# 1. Health check
curl http://localhost:8001/health

# Expected: {"status": "ok", "datasets": 1, "total_vectors": 450, ...}

# 2. List datasets
curl http://localhost:8001/datasets

# Expected: {"datasets": [{"id": "andromeda", "num_vectors": 450, ...}]}

# 3. Search for features
curl "http://localhost:8001/search?q=star%20cluster&dataset_id=andromeda&k=10"

# Expected: JSON with top 10 results, each with bbox coordinates

# 4. Try different queries
curl "http://localhost:8001/search?q=bright%20region&dataset_id=andromeda&k=5"
curl "http://localhost:8001/search?q=dust%20cloud&dataset_id=andromeda&k=5"
curl "http://localhost:8001/search?q=galaxy%20core&dataset_id=andromeda&k=5"

# 5. Get text embedding
curl "http://localhost:8001/embed?text=nebula"

# Expected: {"text": "nebula", "embedding_dim": 512, "embedding": [...]}
```

**✅ Milestone 1 Achieved:** Basic search is working!

---

#### **Step 4: Integration Testing with API Service (1 hour)**

The main API service (port 8000) proxies search requests to your AI service.

**Start the full stack:**

```bash
# Terminal 1: AI service (if not already running)
cd ai
python app.py

# Terminal 2: API service
cd apps/api
uvicorn app.main:app --reload --port 8000

# Terminal 3: Web frontend
cd apps/web
npm run dev
```

**Test full integration:**

1. Open http://localhost:3000
2. Click on Andromeda dataset
3. Click "Search" in toolbar
4. Type: "bright star"
5. Should see results with pins on the image

**Verify in logs:**
- AI service logs: `Search completed: bright star -> X results in Y.YYYs`
- API service logs: Search request proxied successfully

---

### **H6-H12: Real Embeddings & Better Recall** ⏱️ 6 hours

#### **Step 5: Improve Patch Sampling Strategy (2 hours)**

**Current issue:** Random grid sampling may miss interesting features.

**Improvements to implement:**

1. **Interest Point Detection** (already in code!)
   ```python
   # Edit build_real_index.py to use interest points
   # Add after line 80:
   
   # Extract interest point patches
   interest_patches = self.patch_extractor.extract_interest_points(img, patch_size=128)
   for patch, metadata in interest_patches:
       metadata.update({'dataset_id': dataset_id, 'type': 'interest_point'})
       patch_batch.append(patch)
       metadata_batch.append(metadata)
   ```

2. **Hierarchical Sampling** (already implemented!)
   ```python
   # Use hierarchical patches for better coverage
   for patch, metadata in self.patch_extractor.extract_hierarchical_patches(img, levels=[0, 1, 2]):
       # Process patches
   ```

3. **Increase max patches** for better coverage:
   ```bash
   python build_real_index.py \
     --dataset-id andromeda \
     --tiles-dir ../infra/tiles \
     --max-patches 2000  # Increase from 500
   ```

**Test improvements:**
- Rebuild index with new strategy
- Test searches: "spiral arm", "bright core", "dust lane"
- Verify results cover more of the image

---

#### **Step 6: Optimize Search Performance (1.5 hours)**

**Goal:** <10ms search latency, better ranking

**Tasks:**

1. **Add result caching** (already implemented! ✅)
   - Check cache stats: `curl http://localhost:8001/search/cache_stats`
   - Cache hits should reduce latency significantly

2. **Non-Maximum Suppression (NMS)** for overlapping results:

   Create `ai/utils/nms.py`:
   ```python
   import numpy as np
   from typing import List, Tuple
   
   def non_max_suppression(boxes: List[List[int]], scores: List[float], 
                          iou_threshold: float = 0.5) -> List[int]:
       """
       Apply NMS to remove overlapping bounding boxes.
       
       Args:
           boxes: List of [x, y, width, height]
           scores: Similarity scores
           iou_threshold: IoU threshold for suppression
       
       Returns:
           Indices of boxes to keep
       """
       if len(boxes) == 0:
           return []
       
       boxes_array = np.array(boxes)
       x1 = boxes_array[:, 0]
       y1 = boxes_array[:, 1]
       x2 = x1 + boxes_array[:, 2]
       y2 = y1 + boxes_array[:, 3]
       
       areas = boxes_array[:, 2] * boxes_array[:, 3]
       order = np.argsort(scores)[::-1]
       
       keep = []
       while order.size > 0:
           i = order[0]
           keep.append(i)
           
           xx1 = np.maximum(x1[i], x1[order[1:]])
           yy1 = np.maximum(y1[i], y1[order[1:]])
           xx2 = np.minimum(x2[i], x2[order[1:]])
           yy2 = np.minimum(y2[i], y2[order[1:]])
           
           w = np.maximum(0, xx2 - xx1)
           h = np.maximum(0, yy2 - yy1)
           
           intersection = w * h
           iou = intersection / (areas[i] + areas[order[1:]] - intersection)
           
           inds = np.where(iou <= iou_threshold)[0]
           order = order[inds + 1]
       
       return keep
   ```

   Then update `app.py` search endpoint to use NMS:
   ```python
   from utils.nms import non_max_suppression
   
   # After getting results, apply NMS
   boxes = [r["bbox"] for r in results]
   scores = [r["score"] for r in results]
   keep_indices = non_max_suppression(boxes, scores, iou_threshold=0.3)
   results = [results[i] for i in keep_indices]
   ```

3. **Benchmark performance:**
   ```bash
   # Create test script
   python test_ai_service.py
   ```

   Test file should measure:
   - Cold start latency (first query)
   - Warm cache latency (repeated query)
   - Different query types
   - Results quality (manual inspection)

---

#### **Step 7: Multi-Dataset Support (1 hour)**

Currently you can index one dataset. Let's add multiple:

```bash
# Build index for different datasets/time periods
python build_real_index.py --dataset-id andromeda-2020 --tiles-dir ../infra/tiles/andromeda
python build_real_index.py --dataset-id andromeda-2021 --tiles-dir ../infra/tiles/andromeda_2021
```

**Verify:**
```bash
curl http://localhost:8001/datasets
# Should show: andromeda-2020, andromeda-2021

curl "http://localhost:8001/search?q=star&dataset_id=andromeda-2020"
curl "http://localhost:8001/search?q=star&dataset_id=andromeda-2021"
```

---

#### **Step 8: Return Spatial Coordinates Correctly (1.5 hours)**

**Important:** Results need to map back to original image coordinates for frontend display.

**Current metadata structure:**
```json
{
  "bbox": [x, y, width, height],  // Patch location in tile
  "center": [cx, cy],
  "tile_file": "1_2.jpg",  // Which tile
  "level": 2,  // Zoom level
  "patch_size": 128
}
```

**Frontend needs:**
- Global coordinates in original image space
- Or: tile + level + local coordinates

**Action:** Update metadata in `build_real_index.py` to include:
```python
metadata.update({
    'tile_coords': {
        'level': level,
        'tile_x': tile_x,  # Parse from filename
        'tile_y': tile_y
    },
    'global_coords': {
        'x': global_x,  # Calculate based on tile position
        'y': global_y
    }
})
```

**Coordinate conversion:**
```python
def tile_to_global_coords(tile_x, tile_y, local_x, local_y, level, tile_size=256):
    """Convert tile + local coords to global image coords."""
    global_x = (tile_x * tile_size) + local_x
    global_y = (tile_y * tile_size) + local_y
    
    # Scale to level 0 (full resolution)
    scale = 2 ** level
    global_x *= scale
    global_y *= scale
    
    return global_x, global_y
```

---

### **H12-H18: Advanced Features** ⏱️ 6 hours

#### **Step 9: Query Expansion & Synonyms (1 hour)**

Improve recall by expanding queries:

```python
# ai/utils/query_expander.py

QUERY_SYNONYMS = {
    'star': ['stellar', 'bright point', 'luminous object'],
    'galaxy': ['galactic', 'spiral', 'elliptical'],
    'dust': ['nebula', 'cloud', 'dark region'],
    'crater': ['impact', 'circular feature', 'depression'],
}

def expand_query(query: str) -> List[str]:
    """Expand query with synonyms."""
    queries = [query]
    for word, synonyms in QUERY_SYNONYMS.items():
        if word in query.lower():
            for syn in synonyms:
                queries.append(query.replace(word, syn))
    return queries

# In app.py search endpoint:
expanded_queries = expand_query(q)
all_results = []
for exp_q in expanded_queries[:3]:  # Max 3 expansions
    query_vector = CLIP.encode_text(exp_q).numpy()
    scores, indices = INDEX_MANAGER.search(dataset_id, query_vector, k)
    all_results.extend(zip(scores, indices))

# Deduplicate and re-rank
```

---

#### **Step 10: Batch Embedding for Faster Indexing (1 hour)**

Currently: One patch at a time (slow)  
Goal: Batch encoding (5-10x faster)

**Update `build_real_index.py`:**

```python
def _process_patch_batch(self, patches: List[Image.Image], 
                       metadata: List[Dict[str, Any]], dataset_id: str) -> None:
    """Process a batch of patches and add to index."""
    try:
        # Use batch encoding instead of loop
        embeddings = self.clip.encode_images_batch(patches)  # Already implemented!
        embeddings = embeddings.numpy()
        
        # Add to index
        self.index_manager.add_vectors(dataset_id, embeddings, metadata)
        
    except Exception as e:
        logger.error(f"Error processing patch batch: {e}")
```

**Test speedup:**
- Before: ~50 patches/sec (CPU)
- After: ~200 patches/sec (CPU), ~800 patches/sec (GPU)

---

#### **Step 11: Result Thumbnails (1 hour)**

Generate small preview thumbnails for search results:

```python
# In build_real_index.py, save patch thumbnails
def _save_patch_thumbnail(self, patch: Image.Image, dataset_id: str, patch_idx: int):
    """Save small thumbnail for search results."""
    thumb_dir = self.output_dir / "thumbnails" / dataset_id
    thumb_dir.mkdir(exist_ok=True, parents=True)
    
    # Resize to 64x64 thumbnail
    thumb = patch.resize((64, 64), Image.Resampling.LANCZOS)
    thumb_path = thumb_dir / f"{patch_idx}.jpg"
    thumb.save(thumb_path, quality=85)
    
    return f"/thumbnails/{dataset_id}/{patch_idx}.jpg"

# Update metadata with thumbnail URL
metadata['thumbnail_url'] = self._save_patch_thumbnail(patch, dataset_id, patch_idx)
```

**Update API to serve thumbnails:**
```python
# In apps/api/app/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/thumbnails", StaticFiles(directory="../../ai/data/thumbnails"), name="thumbnails")
```

---

#### **Step 12: Logging & Analytics (30 mins)**

Track search performance and popular queries:

```python
# ai/utils/analytics.py

import json
from pathlib import Path
from datetime import datetime

class SearchAnalytics:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(exist_ok=True, parents=True)
    
    def log_search(self, query: str, dataset_id: str, num_results: int, 
                   latency_ms: float, cached: bool):
        """Log search query and performance."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'dataset_id': dataset_id,
            'num_results': num_results,
            'latency_ms': latency_ms,
            'cached': cached
        }
        
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_popular_queries(self, top_k: int = 10):
        """Get most popular queries."""
        queries = {}
        with open(self.log_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                q = entry['query']
                queries[q] = queries.get(q, 0) + 1
        
        return sorted(queries.items(), key=lambda x: x[1], reverse=True)[:top_k]

# Add to app.py
analytics = SearchAnalytics(Path("data/search_analytics.jsonl"))

# In search endpoint, after returning results:
analytics.log_search(q, dataset_id, len(results), search_time * 1000, cached)
```

---

#### **Step 13: Advanced Search Filters (2.5 hours)**

Add filters for better control:

**Spatial filters:**
```python
# Search only within a region of interest
@app.get("/search/spatial")
def search_spatial(
    q: str,
    dataset_id: str,
    bbox: str = Query(..., description="x1,y1,x2,y2"),
    k: int = 10
):
    """Search within a spatial bounding box."""
    x1, y1, x2, y2 = map(int, bbox.split(','))
    
    # Get all results
    query_vector = CLIP.encode_text(q).numpy()
    scores, indices = INDEX_MANAGER.search(dataset_id, query_vector, k * 5)  # Get more
    
    # Filter by spatial bounds
    patch_metadata = INDEX_MANAGER.get_patch_metadata(dataset_id, indices.tolist())
    filtered_results = []
    
    for score, idx, meta in zip(scores, indices, patch_metadata):
        bbox_patch = meta.get('bbox', [0, 0, 0, 0])
        px, py = bbox_patch[0], bbox_patch[1]
        
        # Check if patch center is within bounds
        if x1 <= px <= x2 and y1 <= py <= y2:
            filtered_results.append({'score': float(score), 'bbox': bbox_patch, 'metadata': meta})
        
        if len(filtered_results) >= k:
            break
    
    return {'results': filtered_results}
```

**Scale filters:**
```python
# Search at specific scale (patch size)
@app.get("/search/scale")
def search_by_scale(
    q: str,
    dataset_id: str,
    min_patch_size: int = 64,
    max_patch_size: int = 256,
    k: int = 10
):
    """Search within specific scale range."""
    # Similar to spatial filter, but filter by patch_size in metadata
```

---

### **H18-H24: Polish & SAM (Stretch)** ⏱️ 6 hours

#### **Step 14: SAM Integration Setup (2 hours)**

**Only if you're ahead of schedule!**

1. **Download SAM checkpoints:**
   ```bash
   cd ai
   mkdir -p checkpoints
   
   # Download ViT-B (lightest, ~375MB)
   curl -L "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth" \
     -o checkpoints/sam_vit_b_01ec64.pth
   ```

2. **Test SAM loading:**
   ```bash
   python -c "from sam_integration import get_sam_instance; sam = get_sam_instance(); print(sam.get_model_info() if sam else 'SAM not loaded')"
   ```

3. **Test segmentation endpoint:**
   ```bash
   # Prepare test image
   python -c "
   from PIL import Image
   import base64
   from io import BytesIO
   
   # Load a sample patch
   img = Image.open('data/demo_big.jpg').resize((256, 256))
   buffer = BytesIO()
   img.save(buffer, format='JPEG')
   img_b64 = base64.b64encode(buffer.getvalue()).decode()
   
   # Save for curl test
   with open('test_image_b64.txt', 'w') as f:
       f.write(img_b64)
   "
   
   # Test segmentation with point
   curl -X POST http://localhost:8001/segment \
     -H "Content-Type: application/json" \
     -d "{\"image_data\": \"$(cat test_image_b64.txt)\", \"points\": [[100, 100]], \"labels\": [1]}"
   ```

4. **Integrate with annotation workflow:**
   - When user draws bounding box → automatically run SAM
   - Return refined mask overlay
   - User can accept/reject/edit mask

---

#### **Step 15: Performance Benchmarking (1 hour)**

Create comprehensive test suite:

```python
# ai/benchmark.py

import time
import numpy as np
from models.clip_model import ClipEncoder
from utils.faiss_helper import DatasetIndexManager
from pathlib import Path

def benchmark_clip_encoding():
    """Benchmark CLIP encoding speed."""
    clip = ClipEncoder()
    
    # Text encoding
    queries = ["star", "galaxy", "nebula", "crater", "dust cloud"] * 20
    start = time.time()
    for q in queries:
        _ = clip.encode_text(q)
    elapsed = time.time() - start
    print(f"Text encoding: {len(queries)/elapsed:.1f} queries/sec")
    
    # Image encoding (single)
    from PIL import Image
    img = Image.open("data/demo_big.jpg").resize((256, 256))
    start = time.time()
    for _ in range(100):
        _ = clip.encode_image(img)
    elapsed = time.time() - start
    print(f"Image encoding (single): {100/elapsed:.1f} images/sec")
    
    # Image encoding (batch)
    images = [img] * 32
    start = time.time()
    for _ in range(10):
        _ = clip.encode_images_batch(images)
    elapsed = time.time() - start
    print(f"Image encoding (batch=32): {320/elapsed:.1f} images/sec")

def benchmark_faiss_search():
    """Benchmark FAISS search speed."""
    manager = DatasetIndexManager(Path("data"))
    manager.load_dataset("andromeda")
    
    # Create random query vectors
    query = np.random.randn(1, 512).astype(np.float32)
    
    # Warm up
    for _ in range(10):
        _ = manager.search("andromeda", query, k=10)
    
    # Benchmark
    start = time.time()
    n_queries = 1000
    for _ in range(n_queries):
        _ = manager.search("andromeda", query, k=10)
    elapsed = time.time() - start
    print(f"FAISS search: {n_queries/elapsed:.1f} queries/sec")
    print(f"Avg latency: {elapsed/n_queries*1000:.2f}ms")

if __name__ == "__main__":
    print("=== CLIP Benchmark ===")
    benchmark_clip_encoding()
    print("\n=== FAISS Benchmark ===")
    benchmark_faiss_search()
```

Run: `python benchmark.py`

**Target performance:**
- Text encoding: >50 queries/sec (CPU), >200 (GPU)
- Image encoding: >50 img/sec (CPU), >200 (GPU)
- Batch encoding: >200 img/sec (CPU), >800 (GPU)
- FAISS search: >100 queries/sec, <10ms latency

---

#### **Step 16: Documentation & Demo Prep (1 hour)**

1. **Update README with examples:**
   ```markdown
   ## Example Queries
   
   - "bright star cluster" → Finds dense stellar regions
   - "spiral arm structure" → Finds galactic spiral features
   - "dust lane" → Finds dark nebulae and dust clouds
   - "galaxy core" → Finds central bulge regions
   ```

2. **Create demo script:**
   ```bash
   # ai/demo.sh
   
   echo "🚀 AI Service Demo"
   echo "=================="
   echo ""
   
   echo "1. Health Check"
   curl -s http://localhost:8001/health | jq
   echo ""
   
   echo "2. List Datasets"
   curl -s http://localhost:8001/datasets | jq
   echo ""
   
   echo "3. Search: 'star cluster'"
   curl -s "http://localhost:8001/search?q=star%20cluster&k=5" | jq '.results[0:3]'
   echo ""
   
   echo "4. Search: 'bright region'"
   curl -s "http://localhost:8001/search?q=bright%20region&k=5" | jq '.results[0:3]'
   echo ""
   
   echo "✅ Demo complete!"
   ```

3. **Prepare demo queries list:**
   - Keep a cheat sheet of queries that work well
   - Test with judges/demo audience
   - Have backup queries if primary ones don't work

---

#### **Step 17: Error Handling & Edge Cases (2 hours)**

Make service production-ready:

```python
# ai/app.py - Add better error handling

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Catch all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )

# Handle empty/invalid queries
@app.get("/search")
def search(q: str = Query(..., min_length=2, max_length=200)):
    """Search with validation."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Clean query
    q = q.strip().lower()
    
    # Check for invalid characters
    if any(c in q for c in ['<', '>', '{', '}', ';']):
        raise HTTPException(status_code=400, detail="Invalid characters in query")
    
    # ... rest of search logic

# Handle missing datasets gracefully
if dataset_id not in INDEX_MANAGER.list_datasets():
    available = INDEX_MANAGER.list_datasets()
    raise HTTPException(
        status_code=404, 
        detail=f"Dataset '{dataset_id}' not found. Available: {available}"
    )

# Handle CLIP/FAISS errors
try:
    query_vector = CLIP.encode_text(q).numpy()
except Exception as e:
    logger.error(f"CLIP encoding error: {e}")
    raise HTTPException(status_code=500, detail="Failed to encode query")

try:
    scores, indices = INDEX_MANAGER.search(dataset_id, query_vector, k)
except Exception as e:
    logger.error(f"FAISS search error: {e}")
    raise HTTPException(status_code=500, detail="Search failed")
```

---

### **H24-H30: Final Polish** ⏱️ 6 hours

#### **Step 18: Integration Testing (2 hours)**

Work with teammates to test full pipeline:

1. **With Backend (Edward):**
   - Verify API properly proxies to AI service
   - Check coordinate system alignment
   - Test rate limiting doesn't block AI service
   - Verify search results format matches API expectations

2. **With Frontend (Bohdan):**
   - Ensure search results display correctly on map
   - Verify "jump to result" works with returned coordinates
   - Test search loading states
   - Check result pins/highlights render properly

3. **With Data/Infra (Ivan):**
   - Verify tile coordinates map correctly to patches
   - Test with multiple datasets
   - Check FAISS index sizes are reasonable
   - Ensure volumes/mounts work in Docker

---

#### **Step 19: Performance Tuning (2 hours)**

Final optimizations:

1. **Tune cache settings:**
   ```python
   # Increase cache TTL for demo
   CACHE_TTL = 3600  # 1 hour instead of 5 minutes
   ```

2. **Pre-warm cache with common queries:**
   ```python
   # On startup, pre-compute common queries
   COMMON_QUERIES = [
       "star", "galaxy", "nebula", "bright", "dust", 
       "spiral", "cluster", "core"
   ]
   
   @app.on_event("startup")
   def prewarm_cache():
       for q in COMMON_QUERIES:
           try:
               # Encode and cache
               _ = CLIP.encode_text(q)
           except:
               pass
   ```

3. **Optimize k value:**
   - Too small: miss good results
   - Too large: slow, cluttered UI
   - Sweet spot: k=10-20 for initial results, then filter/rank

---

#### **Step 20: Final Testing & Documentation (2 hours)**

1. **Create test checklist:**
   ```markdown
   ## AI Service Test Checklist
   
   - [ ] Service starts without errors
   - [ ] Health endpoint returns OK
   - [ ] Datasets endpoint lists all indices
   - [ ] Search returns results in <100ms (warm)
   - [ ] Search returns results in <1s (cold)
   - [ ] At least 3 different queries work well
   - [ ] Coordinates map correctly to image
   - [ ] Cache hit rate >80% for repeated queries
   - [ ] No errors in logs during normal operation
   - [ ] SAM endpoint works (if implemented)
   - [ ] Service handles invalid input gracefully
   - [ ] Service recovers from errors
   ```

2. **Document known issues/limitations:**
   ```markdown
   ## Known Limitations
   
   - First search is slow (~1-2s) due to model loading
   - Requires ~2GB RAM for CLIP model
   - CPU inference is slower than GPU (expected)
   - Some abstract queries may not work well
   - Coordinate mapping assumes square tiles
   ```

3. **Prepare handoff notes:**
   - How to rebuild indices if data changes
   - How to add new datasets
   - Cache management recommendations
   - Performance tuning options

---

## 🎯 Success Criteria Checklist

By the end, you should have:

- [x] ✅ CLIP model loaded and working
- [x] ✅ FAISS index built from sample data
- [ ] ⏳ Search endpoint returns ranked results
- [ ] ⏳ Integration with API service works
- [ ] ⏳ Frontend can display search results
- [ ] ⏳ Performance: <100ms search (warm), <1s (cold)
- [ ] ⏳ At least 3 working demo queries
- [ ] ⏳ Coordinate system correctly maps patches to image
- [ ] 🎁 SAM segmentation working (stretch)
- [ ] 🎁 Result thumbnails (stretch)
- [ ] 🎁 Advanced filters (stretch)

---

## 🔧 Debugging Tips

**Issue: CLIP model won't load**
```bash
# Check CUDA availability
python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Try CPU explicitly
python -c "from models.clip_model import ClipEncoder; clip = ClipEncoder(device='cpu')"

# Clear cache and retry
rm -rf ~/.cache/clip
```

**Issue: Search returns no results**
```bash
# Check index size
python -c "
from utils.faiss_helper import DatasetIndexManager
from pathlib import Path
mgr = DatasetIndexManager(Path('data'))
mgr.load_dataset('andromeda')
print('Vectors:', mgr.get_dataset_info('andromeda'))
"

# Verify embeddings are normalized
# Check metadata exists
ls -lh data/*.json
```

**Issue: Coordinates don't match image**
- Double-check coordinate conversion logic
- Verify DZI info.xml tile size matches assumption
- Print bbox values and inspect manually
- Test with known tile (e.g., level 0, tile 0_0)

**Issue: Performance is slow**
- Check if GPU is being used: `nvidia-smi` (if available)
- Reduce batch size if OOM errors
- Enable caching: `use_cache=true` in API calls
- Pre-compute embeddings for common queries

---

## 📞 Coordination Points

**With Edward (Backend Lead):**
- Search result format (bbox coordinates)
- Rate limiting exemption for AI service
- Health check integration
- Error response format

**With Bohdan (Frontend Lead):**
- Search result display requirements
- Coordinate system (tile-based vs. global)
- Loading state expectations
- Result preview format (thumbnails?)

**With Ivan (Data/Infra):**
- Tile directory structure
- Dataset naming conventions
- Docker volume mounts for indices
- Sample data availability

**With Illia (Security):**
- Rate limiting on /search endpoint
- Input validation requirements
- CORS settings for AI service
- Authentication (if needed for admin endpoints)

---

## 🚀 Quick Reference Commands

```bash
# Start AI service
cd ai && python app.py

# Rebuild index
python build_real_index.py --dataset-id andromeda --tiles-dir ../infra/tiles

# Test search
curl "http://localhost:8001/search?q=star&dataset_id=andromeda&k=5" | jq

# Check health
curl http://localhost:8001/health

# View logs
tail -f ai/logs/app.log  # If logging to file

# Clear cache
curl -X POST http://localhost:8001/search/clear_cache

# Benchmark
cd ai && python benchmark.py
```

---

## 🎓 Learning Resources

- **CLIP Paper:** https://arxiv.org/abs/2103.00020
- **FAISS Wiki:** https://github.com/facebookresearch/faiss/wiki
- **OpenCLIP:** https://github.com/mlfoundations/open_clip
- **SAM Paper:** https://arxiv.org/abs/2304.02643

---

**Good luck, Misha! You've got this! 🚀✨**

*Remember: Perfect is the enemy of done. Get the core search working first, then optimize!*

