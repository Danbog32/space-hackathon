from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import numpy as np
import logging
from typing import List, Dict, Any, Optional
import time
import json
from datetime import datetime, timedelta
import hashlib
from PIL import Image

from models.clip_model import ClipEncoder
from utils.faiss_helper import DatasetIndexManager, load_index, load_metadata
from sam_integration import get_sam_instance, segment_patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Microservice", version="0.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
INDEX_MANAGER = None
CLIP = None

# Simple in-memory cache for search results
SEARCH_CACHE = {}
CACHE_TTL = 300  # 5 minutes

class SearchCache:
    """Simple search result cache."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if not expired."""
        if key in self.cache:
            result, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Dict[str, Any]) -> None:
        """Cache a result."""
        self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()

search_cache = SearchCache(CACHE_TTL)

@app.on_event("startup")
def startup():
    global INDEX_MANAGER, CLIP
    
    logger.info("Initializing AI microservice...")
    
    # Initialize CLIP
    try:
        CLIP = ClipEncoder(device=None)  # Auto-detect device
        logger.info(f"CLIP model loaded: {CLIP.get_model_info()}")
    except Exception as e:
        logger.error(f"Failed to load CLIP model: {e}")
        raise RuntimeError(f"Could not initialize CLIP model: {e}")
    
    # Initialize index manager
    try:
        INDEX_MANAGER = DatasetIndexManager(DATA_DIR)
        
        # Try to load available datasets
        available_datasets = []
        for dataset_file in DATA_DIR.glob("*_metadata.json"):
            dataset_id = dataset_file.stem.replace("_metadata", "")
            if INDEX_MANAGER.load_dataset(dataset_id):
                available_datasets.append(dataset_id)
        
        logger.info(f"Loaded {len(available_datasets)} datasets: {available_datasets}")
        
        if not available_datasets:
            logger.warning("No datasets found. Run build_index.py first.")
        
    except Exception as e:
        logger.error(f"Failed to initialize index manager: {e}")
        raise RuntimeError(f"Could not initialize index manager: {e}")

@app.get("/health")
def health():
    """Health check endpoint."""
    dataset_count = len(INDEX_MANAGER.list_datasets()) if INDEX_MANAGER else 0
    total_vectors = 0
    
    if INDEX_MANAGER:
        for dataset_id in INDEX_MANAGER.list_datasets():
            info = INDEX_MANAGER.get_dataset_info(dataset_id)
            if info:
                total_vectors += info.get("num_vectors", 0)
    
    return {
        "status": "ok",
        "datasets": dataset_count,
        "total_vectors": total_vectors,
        "clip_ready": CLIP is not None,
        "index_manager_ready": INDEX_MANAGER is not None
    }

@app.get("/datasets")
def list_datasets():
    """List available datasets."""
    if not INDEX_MANAGER:
        raise HTTPException(status_code=503, detail="Index manager not ready")
    
    datasets = []
    for dataset_id in INDEX_MANAGER.list_datasets():
        info = INDEX_MANAGER.get_dataset_info(dataset_id)
        if info:
            datasets.append({
                "id": dataset_id,
                "num_vectors": info.get("num_vectors", 0),
                "embedding_dim": info.get("embedding_dim", 0),
                "created_at": info.get("created_at", ""),
                "last_updated": info.get("last_updated", "")
            })
    
    return {"datasets": datasets}

@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    dataset_id: str = Query("demo", description="Dataset ID to search"),
    k: int = Query(10, ge=1, le=100, description="Number of results"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score"),
    use_cache: bool = Query(True, description="Use search result cache")
):
    """Advanced text search with ranking and caching."""
    if not INDEX_MANAGER or not CLIP:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Check if dataset exists
    if dataset_id not in INDEX_MANAGER.list_datasets():
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    
    # Create cache key
    cache_key = f"{dataset_id}:{q}:{k}:{min_score}"
    
    # Check cache first
    if use_cache:
        cached_result = search_cache.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {q}")
            return cached_result
    
    start_time = time.time()
    
    try:
        # Encode query
        query_vector = CLIP.encode_text(q).numpy()
        
        # Search in dataset
        scores, indices = INDEX_MANAGER.search(dataset_id, query_vector, k)
        
        # Get patch metadata
        patch_metadata = INDEX_MANAGER.get_patch_metadata(dataset_id, indices.tolist())
        
        # Filter by minimum score and format results
        results = []
        for rank, (idx, score) in enumerate(zip(indices, scores)):
            if idx < 0 or score < min_score:
                continue
            
            if rank < len(patch_metadata):
                metadata = patch_metadata[rank]
                bbox = metadata.get('bbox', [0, 0, 0, 0])
            else:
                bbox = [0, 0, 0, 0]
            
            results.append({
                "id": int(idx),
                "rank": len(results) + 1,
                "score": float(score),
                "bbox": bbox,
                "previewThumb": None,
                "metadata": metadata if rank < len(patch_metadata) else {}
            })
        
        # Calculate search time
        search_time = time.time() - start_time
        
        response = {
            "query": q,
            "dataset_id": dataset_id,
            "k": k,
            "min_score": min_score,
            "count": len(results),
            "results": results,
            "search_time_ms": round(search_time * 1000, 2),
            "cached": False
        }
        
        # Cache result
        if use_cache:
            search_cache.set(cache_key, response)
            response["cached"] = True
        
        logger.info(f"Search completed: {q} -> {len(results)} results in {search_time:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search/similar")
def search_similar(
    image_id: str = Query(..., description="Image/patch ID to find similar to"),
    dataset_id: str = Query("demo", description="Dataset ID"),
    k: int = Query(10, ge=1, le=100, description="Number of results")
):
    """Find similar patches to a given patch ID."""
    if not INDEX_MANAGER:
        raise HTTPException(status_code=503, detail="Index manager not ready")
    
    # This would require storing patch embeddings for similarity search
    # For now, return a placeholder
    raise HTTPException(status_code=501, detail="Similarity search not yet implemented")

@app.post("/search/clear_cache")
def clear_search_cache():
    """Clear the search result cache."""
    search_cache.clear()
    return {"message": "Search cache cleared"}

@app.get("/search/cache_stats")
def get_cache_stats():
    """Get cache statistics."""
    cache_size = len(search_cache.cache)
    return {
        "cache_size": cache_size,
        "cache_ttl_seconds": CACHE_TTL
    }

@app.get("/embed")
def embed_text(text: str = Query(..., description="Text to embed")):
    """Get CLIP embedding for text."""
    if not CLIP:
        raise HTTPException(status_code=503, detail="CLIP model not ready")
    
    try:
        embedding = CLIP.encode_text(text)
        return {
            "text": text,
            "embedding_dim": len(embedding),
            "embedding": embedding.numpy().tolist()
        }
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")

@app.get("/models/info")
def get_model_info():
    """Get information about loaded models."""
    if not CLIP:
        raise HTTPException(status_code=503, detail="CLIP model not ready")
    
    sam_info = None
    sam = get_sam_instance()
    if sam:
        sam_info = sam.get_model_info()
    
    return {
        "clip": CLIP.get_model_info(),
        "sam": sam_info,
        "datasets": INDEX_MANAGER.list_datasets() if INDEX_MANAGER else []
    }

@app.post("/segment")
def segment_image(
    image_data: str,  # Base64 encoded image
    points: List[List[int]] = [],  # [[x1, y1], [x2, y2], ...]
    labels: List[int] = [],  # [1, 0, 1, ...] (1=foreground, 0=background)
    bbox: Optional[List[int]] = None  # [x1, y1, x2, y2]
):
    """Generate segmentation mask using SAM."""
    sam = get_sam_instance()
    if not sam:
        raise HTTPException(status_code=503, detail="SAM model not available")
    
    try:
        import base64
        from io import BytesIO
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert points to tuples
        point_tuples = [tuple(p) for p in points] if points else []
        
        # Convert bbox to tuple
        bbox_tuple = tuple(bbox) if bbox else None
        
        # Generate segmentation
        mask = segment_patch(image, point_tuples, labels, bbox_tuple)
        
        if mask is None:
            raise HTTPException(status_code=500, detail="Segmentation failed")
        
        # Convert mask to base64
        mask_pil = Image.fromarray(mask)
        buffer = BytesIO()
        mask_pil.save(buffer, format='PNG')
        mask_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "success": True,
            "mask": mask_b64,
            "points": points,
            "labels": labels,
            "bbox": bbox
        }
        
    except Exception as e:
        logger.error(f"Segmentation error: {e}")
        raise HTTPException(status_code=500, detail=f"Segmentation failed: {str(e)}")

@app.get("/sam/status")
def get_sam_status():
    """Get SAM model status."""
    sam = get_sam_instance()
    if sam:
        return {
            "available": True,
            "info": sam.get_model_info()
        }
    else:
        return {
            "available": False,
            "message": "SAM model not loaded. Install segment-anything and download checkpoints."
        }
