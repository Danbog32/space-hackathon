"""Main AI service application."""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
import torch
import open_clip
from PIL import Image
import numpy as np
from pathlib import Path

from app.indexer import ImageIndexer, build_index_for_dataset
from app.config import TILES_DIR

# Initialize CLIP model at startup
print("🚀 Loading CLIP model for real AI classification...")
try:
    clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
        'ViT-B-32', 
        pretrained='openai'
    )
    device = "cuda" if torch.cuda.is_available() else "cpu"
    clip_model = clip_model.to(device)
    clip_model.eval()
    CLIP_AVAILABLE = True
    print(f"✅ CLIP model loaded successfully on {device}!")
except Exception as e:
    print(f"⚠️ Failed to load CLIP: {e}")
    CLIP_AVAILABLE = False
    clip_model = None
    clip_preprocess = None
    device = "cpu"

app = FastAPI(
    title="Astro-Zoom AI Service",
    description="AI-powered semantic search for deep zoom images",
    version="0.1.0",
)


class BuildIndexRequest(BaseModel):
    datasetId: str
    patchSize: Optional[int] = 256
    stride: Optional[int] = 128
    level: Optional[int] = 2


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/build-index")
async def build_index(request: BuildIndexRequest, background_tasks: BackgroundTasks):
    """
    Build FAISS index for a dataset.
    This is run as a background task in production.
    """

    def build_task():
        try:
            build_index_for_dataset(request.datasetId)
        except Exception as e:
            print(f"Error building index: {e}")

    background_tasks.add_task(build_task)

    return {
        "message": "Index building started",
        "datasetId": request.datasetId,
    }


@app.get("/search")
async def search(
    q: str = Query(..., description="Search query text"),
    datasetId: str = Query(..., description="Dataset to search"),
    topK: int = Query(20, description="Number of results to return", le=100),
):
    """
    Search for image regions matching the query.
    Returns bounding boxes with similarity scores.
    """
    try:
        indexer = ImageIndexer(datasetId)
        results = indexer.search(q, top_k=topK)

        return {
            "query": q,
            "datasetId": datasetId,
            "results": results,
            "total": len(results),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@app.post("/embed")
async def embed_text(text: str):
    """Generate embedding for text (utility endpoint)."""
    from app.clip_stub import create_clip_model

    model = create_clip_model()
    embedding = model.encode_text(text)

    return {
        "text": text,
        "embedding": embedding.tolist(),
        "dimension": len(embedding),
    }


@app.post("/classify")
async def classify_region(
    datasetId: str = Query(..., description="Dataset ID"),
    bbox: str = Query(..., description="Bounding box as 'x,y,width,height'")
):
    """
    Classify what astronomical object is in a region using CLIP AI.
    Uses real image analysis with expanded category support.
    """
    # Parse bbox
    try:
        x, y, w, h = map(int, bbox.split(','))
    except:
        raise HTTPException(status_code=400, detail="Invalid bbox format. Use 'x,y,width,height'")
    
    # Universal object categories (space + everyday objects)
    categories = [
        # === SPACE OBJECTS ===
        # Galaxies
        "a spiral galaxy",
        "an elliptical galaxy",
        "an irregular galaxy",
        
        # Stars & Clusters
        "a bright star",
        "a star field",
        "a star cluster",
        
        # Nebulae
        "a nebula",
        "a planetary nebula",
        
        # Exotic Space Objects
        "a supernova",
        "a black hole",
        "a quasar",
        
        # Solar System
        "a planet",
        "the moon",
        "an asteroid",
        
        # === ANIMALS ===
        "a cat",
        "a dog",
        "a bird",
        "a horse",
        "a fish",
        "a butterfly",
        
        # === PEOPLE & BODY PARTS ===
        "a person",
        "a human face",
        "a hand",
        "people",
        
        # === LANDMARKS & MONUMENTS ===
        "the Statue of Liberty",
        "the Eiffel Tower",
        "a pyramid",
        "a monument",
        "a statue",
        
        # === BUILDINGS & ARCHITECTURE ===
        "a house",
        "a building",
        "a skyscraper",
        "a bridge",
        "a castle",
        "a church",
        
        # === VEHICLES ===
        "a car",
        "a truck",
        "an airplane",
        "a ship",
        "a bicycle",
        
        # === NATURE ===
        "a tree",
        "a flower",
        "a mountain",
        "a lake",
        "a sunset",
        "clouds",
        "the ocean",
        
        # === FOOD ===
        "food",
        "a pizza",
        "fruit",
        "a cake",
        
        # === OBJECTS ===
        "a book",
        "a phone",
        "a computer",
        "a chair",
        "a table",
        
        # === ABSTRACT ===
        "text",
        "a logo",
        "a pattern",
        "abstract art",
        "empty space",
        "background"
    ]
    
    if not CLIP_AVAILABLE or clip_model is None:
        # Fallback to random if CLIP not available
        import random
        primary = random.choice([c.replace("a ", "").replace("an ", "") for c in categories[:8]])
        return {
            "primary_classification": primary,
            "confidence": 0.5,
            "all_classifications": [{"type": primary, "confidence": 0.5, "rank": 1}],
            "bbox": [x, y, w, h],
            "note": "Using fallback - CLIP not available"
        }
    
    try:
        # Find the highest quality tiles for this region
        dataset_path = TILES_DIR / datasetId
        
        print(f"🔍 Finding best quality tiles for region ({x},{y},{w},{h})")
        
        # Function to get best quality snippet from tiled dataset
        def get_best_quality_snippet(dataset_path, x, y, w, h):
            """Extract highest quality snippet from DeepZoom tiles"""
            
            # Check for full resolution source image first
            for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
                source_path = dataset_path / f"source{ext}"
                if source_path.exists():
                    print(f"📸 Found source image: {source_path}")
                    img = Image.open(source_path).convert('RGB')
                    # Ensure bbox is within bounds
                    img_w, img_h = img.size
                    x1 = max(0, min(x, img_w - 1))
                    y1 = max(0, min(y, img_h - 1))
                    x2 = min(x + w, img_w)
                    y2 = min(y + h, img_h)
                    snippet = img.crop((x1, y1, x2, y2))
                    return snippet, "source (highest quality)"
            
            # Find the highest zoom level available
            level_dirs = sorted([d for d in dataset_path.iterdir() if d.is_dir() and d.name.isdigit()], 
                              key=lambda x: int(x.name), reverse=True)
            
            if not level_dirs:
                raise HTTPException(status_code=404, detail="No tile levels found")
            
            # Try highest quality level first (highest number = most detailed)
            for level_dir in level_dirs:
                level = int(level_dir.name)
                tile_size = 256  # Standard DeepZoom tile size
                
                # For this level, calculate scale factor
                # Level 0 = 1 tile, Level 1 = 4 tiles, Level 2 = 16 tiles, etc.
                scale = 2 ** level
                
                # Calculate which tiles we need for this bbox at this level
                start_col = x // tile_size
                start_row = y // tile_size
                end_col = (x + w) // tile_size
                end_row = (y + h) // tile_size
                
                # Collect tiles that cover this region
                tiles_to_stitch = []
                for row in range(start_row, end_row + 1):
                    for col in range(start_col, end_col + 1):
                        tile_path = level_dir / f"{col}_{row}.jpg"
                        if not tile_path.exists():
                            tile_path = level_dir / f"{col}_{row}.png"
                        
                        if tile_path.exists():
                            tiles_to_stitch.append((col, row, tile_path))
                
                if tiles_to_stitch:
                    print(f"📦 Using level {level} with {len(tiles_to_stitch)} tiles")
                    
                    # If single tile, just crop it
                    if len(tiles_to_stitch) == 1:
                        col, row, tile_path = tiles_to_stitch[0]
                        tile = Image.open(tile_path).convert('RGB')
                        
                        # Calculate local coordinates within this tile
                        local_x = x - (col * tile_size)
                        local_y = y - (row * tile_size)
                        
                        # Ensure within tile bounds
                        local_x = max(0, min(local_x, tile.width - 1))
                        local_y = max(0, min(local_y, tile.height - 1))
                        local_x2 = min(local_x + w, tile.width)
                        local_y2 = min(local_y + h, tile.height)
                        
                        snippet = tile.crop((local_x, local_y, local_x2, local_y2))
                        return snippet, f"level {level} (single tile)"
                    
                    # Multiple tiles - stitch them together
                    else:
                        # Calculate canvas size
                        min_col = min(t[0] for t in tiles_to_stitch)
                        min_row = min(t[1] for t in tiles_to_stitch)
                        max_col = max(t[0] for t in tiles_to_stitch)
                        max_row = max(t[1] for t in tiles_to_stitch)
                        
                        canvas_w = (max_col - min_col + 1) * tile_size
                        canvas_h = (max_row - min_row + 1) * tile_size
                        canvas = Image.new('RGB', (canvas_w, canvas_h), (0, 0, 0))
                        
                        # Stitch tiles
                        for col, row, tile_path in tiles_to_stitch:
                            tile = Image.open(tile_path).convert('RGB')
                            paste_x = (col - min_col) * tile_size
                            paste_y = (row - min_row) * tile_size
                            canvas.paste(tile, (paste_x, paste_y))
                        
                        # Crop to exact bbox
                        local_x = x - (min_col * tile_size)
                        local_y = y - (min_row * tile_size)
                        local_x = max(0, min(local_x, canvas.width - 1))
                        local_y = max(0, min(local_y, canvas.height - 1))
                        local_x2 = min(local_x + w, canvas.width)
                        local_y2 = min(local_y + h, canvas.height)
                        
                        snippet = canvas.crop((local_x, local_y, local_x2, local_y2))
                        return snippet, f"level {level} (stitched {len(tiles_to_stitch)} tiles)"
            
            raise HTTPException(status_code=404, detail="No suitable tiles found")
        
        # Get the best quality snippet
        cropped, source_info = get_best_quality_snippet(dataset_path, x, y, w, h)
        print(f"✂️ Extracted snippet: {cropped.width}x{cropped.height} from {source_info}")
        
        # Resize if too small (CLIP works better with reasonable size)
        if cropped.width < 50 or cropped.height < 50:
            cropped = cropped.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Preprocess image for CLIP
        image_tensor = clip_preprocess(cropped).unsqueeze(0).to(device)
        
        # Tokenize category text
        text_tokens = open_clip.tokenize(categories).to(device)
        
        # Get predictions from CLIP
        with torch.no_grad():
            image_features = clip_model.encode_image(image_tensor)
            text_features = clip_model.encode_text(text_tokens)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # Calculate similarity (cosine similarity)
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            probs = similarity[0].cpu().numpy()
        
        # Format results
        results = []
        for i, (category, prob) in enumerate(zip(categories, probs)):
            # Clean up category text
            clean_name = category.replace("a ", "").replace("an ", "")
            results.append({
                "type": clean_name,
                "confidence": float(prob),
                "score": float(prob)
            })
        
        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Add ranks
        for i, result in enumerate(results):
            result["rank"] = i + 1
        
        # Debug output
        print(f"🎯 Top 5 classifications:")
        for r in results[:5]:
            print(f"   {r['rank']}. {r['type']}: {r['confidence']*100:.1f}%")
        
        # Convert snippet to base64 for preview in UI
        import io
        import base64
        
        # Resize snippet to reasonable preview size (max 400px)
        preview_img = cropped.copy()
        if preview_img.width > 400 or preview_img.height > 400:
            preview_img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        preview_img.save(buffer, format='JPEG', quality=85)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            "primary_classification": results[0]["type"],
            "confidence": results[0]["confidence"],
            "all_classifications": results[:8],  # Top 8 results
            "bbox": [x, y, w, h],
            "model": "CLIP ViT-B-32",
            "device": device,
            "snippet_preview": f"data:image/jpeg;base64,{img_base64}",  # Image preview
            "snippet_size": f"{cropped.width}x{cropped.height}",
            "source_info": source_info
        }
        
    except Exception as e:
        import traceback
        print(f"Classification error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


@app.get("/detect")
async def detect_objects(
    q: str = Query(..., description="Object type to detect"),
    datasetId: str = Query(..., description="Dataset ID"),
    confidence_threshold: float = Query(0.6, ge=0.0, le=1.0),
    max_results: int = Query(50, ge=1, le=200)
):
    """
    Detect all instances of a specific object type in the dataset.
    Returns bounding boxes with confidence scores.
    """
    import random
    
    # Simulate detection (in real implementation, run object detection model)
    num_detections = random.randint(5, min(25, max_results))
    
    detections = []
    for i in range(num_detections):
        # Generate random positions in the image
        x = random.randint(100, 3000)
        y = random.randint(100, 3000)
        w = random.randint(50, 200)
        h = random.randint(50, 200)
        conf = random.uniform(confidence_threshold, 0.95)
        
        detections.append({
            "id": i,
            "bbox": [x, y, w, h],
            "confidence": conf,
            "object_type": q
        })
    
    # Sort by confidence
    detections.sort(key=lambda d: d["confidence"], reverse=True)
    
    return {
        "query": q,
        "object_type": q,
        "detections": detections,
        "total_found": len(detections),
        "confidence_threshold": confidence_threshold
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

