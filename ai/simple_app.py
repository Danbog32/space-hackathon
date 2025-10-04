#!/usr/bin/env python3
"""
Simplified AI service that works without complex dependencies.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import numpy as np
import json
import time
import random
from typing import List, Dict, Any

app = FastAPI(title="AI Microservice (Simple)", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
META_PATH = DATA_DIR / "metadata.json"

# Load metadata
metadata = None

@app.on_event("startup")
def startup():
    global metadata
    if META_PATH.exists():
        with open(META_PATH, 'r') as f:
            metadata = json.load(f)
        print(f"✅ Loaded metadata: {metadata.get('num_patches', 0)} patches")
    else:
        print("⚠️  No metadata found. Run simple_build.py first.")
        metadata = {"num_patches": 0, "bboxes": []}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "patches": metadata.get("num_patches", 0),
        "service": "simple_ai"
    }

@app.get("/datasets")
def list_datasets():
    return {
        "datasets": [{
            "id": "demo",
            "num_vectors": metadata.get("num_patches", 0),
            "embedding_dim": metadata.get("embedding_dim", 512),
            "created_at": metadata.get("created_at", ""),
            "last_updated": metadata.get("created_at", "")
        }]
    }

@app.get("/search")
def search(
    q: str = Query(..., description="Search query"),
    dataset_id: str = Query(None, description="Dataset ID (snake_case)"),
    datasetId: str = Query("demo", description="Dataset ID (camelCase) - Platform uses this"),
    k: int = Query(10, ge=1, le=100, description="Number of results"),
    topK: int = Query(None, description="Alternative param for k"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Minimum similarity score")
):
    """
    AI Search - Compatible with Astro-Zoom Platform
    
    Integration Points:
    - Frontend -> API Backend (port 8000) -> AI Service (port 8001)
    - API expects: { results: [...], total: number }
    - Frontend displays results on OpenSeadragon viewer
    """
    # Support both parameter names (platform uses camelCase)
    dataset = dataset_id or datasetId
    num_results = topK or k
    
    print(f"🔍 AI Search: '{q}' | Dataset: '{dataset}' | Results: {num_results}")
    
    if dataset != "demo":
        raise HTTPException(status_code=404, detail=f"Dataset {dataset} not found")
    
    # Simulate search processing time
    time.sleep(0.1)
    
    # Generate mock results based on query keywords
    query_lower = q.lower()
    bboxes = metadata.get("bboxes", [])
    
    # Create mock results with different scores based on keywords
    results = []
    for i, bbox in enumerate(bboxes[:num_results*2]):  # Get more than needed to filter
        # Simulate different scores based on query content
        base_score = random.uniform(0.3, 0.9)
        
        # Boost score for certain keywords
        if any(keyword in query_lower for keyword in ["star", "galaxy", "cluster"]):
            base_score += 0.1
        if any(keyword in query_lower for keyword in ["bright", "spiral", "dust"]):
            base_score += 0.05
        if any(keyword in query_lower for keyword in ["crater", "moon", "planet"]):
            base_score += 0.08
            
        base_score = min(base_score, 0.95)  # Cap at 0.95
        
        if base_score >= min_score:
            results.append({
                "id": i,
                "rank": len(results) + 1,
                "score": round(base_score, 3),
                "bbox": bbox,
                "previewThumb": None,
                "metadata": {
                    "patch_size": 128,
                    "type": "mock_result",
                    "query_matched": True
                }
            })
            
            if len(results) >= num_results:
                break
    
    # Platform-compatible response format
    return {
        "query": q,
        "datasetId": dataset,  # Platform uses camelCase
        "results": results,  # Required by platform
        "total": len(results),  # Required by platform
        "count": len(results),
        "k": num_results,
        "min_score": min_score,
        "search_time_ms": 100,
        "cached": False
    }

@app.get("/embed")
def embed_text(text: str = Query(..., description="Text to embed")):
    """Mock text embedding."""
    # Create a mock embedding
    embedding_dim = metadata.get("embedding_dim", 512)
    embedding = np.random.randn(embedding_dim).astype(np.float32)
    # Normalize
    embedding = embedding / np.linalg.norm(embedding)
    
    return {
        "text": text,
        "embedding_dim": embedding_dim,
        "embedding": embedding.tolist()
    }

@app.get("/models/info")
def get_model_info():
    """Get mock model information."""
    return {
        "clip": {
            "model_name": "mock_clip",
            "device": "cpu",
            "embedding_dim": metadata.get("embedding_dim", 512),
            "status": "mock_mode"
        },
        "sam": None,
        "datasets": ["demo"]
    }

@app.get("/sam/status")
def get_sam_status():
    """SAM status (not available in simple mode)."""
    return {
        "available": False,
        "message": "SAM not available in simple mode"
    }

@app.post("/search/clear_cache")
def clear_search_cache():
    """Clear cache (no-op in simple mode)."""
    return {"message": "Cache cleared (simple mode)"}

@app.get("/search/cache_stats")
def get_cache_stats():
    """Get cache statistics (no-op in simple mode)."""
    return {
        "cache_size": 0,
        "cache_ttl_seconds": 0
    }

@app.post("/classify")
def classify_region(
    dataset_id: str = Query("demo", description="Dataset ID"),
    bbox: List[int] = Query(..., description="Bounding box [x, y, width, height]")
):
    """
    Classify what astronomical object is in the given region.
    
    Feature 1: Object Classification for Annotated Frames
    - Takes a bounding box from an annotation
    - Returns classification (star, nebula, galaxy, etc.) with confidence scores
    """
    print(f"🔬 Classify Region: Dataset={dataset_id}, BBox={bbox}")
    
    # Simulate classification processing
    time.sleep(0.15)
    
    # Define astronomical object types with mock probabilities
    # In a real implementation, this would use CLIP zero-shot classification
    object_types = [
        "star", "star cluster", "nebula", "galaxy", 
        "spiral galaxy", "planetary nebula", "supernova remnant",
        "asteroid", "comet", "planet", "moon crater"
    ]
    
    # Generate mock classification results
    # Randomly select primary classification
    primary_type = random.choice(object_types[:4])  # Focus on common types
    
    classifications = []
    total_prob = 1.0
    
    # Primary classification (highest confidence)
    primary_confidence = random.uniform(0.65, 0.92)
    classifications.append({
        "type": primary_type,
        "confidence": round(primary_confidence, 3),
        "rank": 1
    })
    total_prob -= primary_confidence
    
    # Secondary classifications (lower confidence)
    num_secondary = random.randint(2, 4)
    remaining_types = [t for t in object_types if t != primary_type]
    random.shuffle(remaining_types)
    
    for i, obj_type in enumerate(remaining_types[:num_secondary]):
        confidence = total_prob * random.uniform(0.2, 0.8)
        classifications.append({
            "type": obj_type,
            "confidence": round(confidence, 3),
            "rank": i + 2
        })
        total_prob -= confidence
        if total_prob <= 0:
            break
    
    # Sort by confidence
    classifications.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Platform-compatible response
    return {
        "datasetId": dataset_id,
        "bbox": bbox,
        "primary_classification": classifications[0]["type"],
        "confidence": classifications[0]["confidence"],
        "all_classifications": classifications,
        "processing_time_ms": 150
    }

@app.get("/detect")
def detect_objects(
    q: str = Query(..., description="Object type to detect (e.g., 'galaxy', 'star', 'nebula')"),
    dataset_id: str = Query(None, description="Dataset ID (snake_case)"),
    datasetId: str = Query("demo", description="Dataset ID (camelCase)"),
    confidence_threshold: float = Query(0.6, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    max_results: int = Query(50, ge=1, le=200, description="Maximum number of detections")
):
    """
    Detect and locate all instances of a specific astronomical object type.
    
    Feature 2: Object Detection and Localization
    - Search for specific object types (galaxy, nebula, star, etc.)
    - Returns ALL locations where the object appears
    - Each detection includes bounding box and confidence score
    """
    dataset = dataset_id or datasetId
    print(f"🎯 Detect Objects: '{q}' | Dataset: '{dataset}' | Threshold: {confidence_threshold}")
    
    if dataset != "demo":
        raise HTTPException(status_code=404, detail=f"Dataset {dataset} not found")
    
    # Simulate object detection processing
    time.sleep(0.2)
    
    bboxes = metadata.get("bboxes", [])
    
    # Simulate detection results
    detections = []
    num_detections = min(random.randint(5, 25), len(bboxes))
    
    # Randomly select patches as detections
    selected_indices = random.sample(range(len(bboxes)), num_detections)
    
    for idx in selected_indices:
        bbox = bboxes[idx]
        
        # Generate confidence score based on query
        # Higher confidence for exact matches
        query_lower = q.lower()
        base_confidence = random.uniform(0.5, 0.95)
        
        # Boost confidence for common astronomical objects
        if any(keyword in query_lower for keyword in ["star", "galaxy", "nebula"]):
            base_confidence += 0.05
        if any(keyword in query_lower for keyword in ["cluster", "spiral", "bright"]):
            base_confidence += 0.03
            
        base_confidence = min(base_confidence, 0.98)
        
        # Only include if above threshold
        if base_confidence >= confidence_threshold:
            detections.append({
                "id": idx,
                "bbox": bbox,
                "confidence": round(base_confidence, 3),
                "object_type": q,
                "metadata": {
                    "detection_method": "semantic_search",
                    "patch_size": 128
                }
            })
    
    # Sort by confidence
    detections.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Limit results
    detections = detections[:max_results]
    
    return {
        "query": q,
        "datasetId": dataset,
        "object_type": q,
        "detections": detections,
        "total_found": len(detections),
        "confidence_threshold": confidence_threshold,
        "processing_time_ms": 200
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple AI Service...")
    print("📊 Available endpoints:")
    print("   GET  /health - Health check")
    print("   GET  /datasets - List datasets")
    print("   GET  /search?q=query - Search")
    print("   POST /classify?bbox=[x,y,w,h] - Classify region (NEW!)")
    print("   GET  /detect?q=object_type - Detect objects (NEW!)")
    print("   GET  /embed?text=text - Get embedding")
    print("   GET  /models/info - Model information")
    print("   GET  /docs - API documentation")
    print()
    print("🌐 Service will be available at: http://localhost:8001")
    print("📚 API docs at: http://localhost:8001/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
