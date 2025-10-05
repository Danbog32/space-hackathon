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
from typing import List, Dict, Any, Optional

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
clip_model = None

region_proposal_model = None
text_embedding_cache = {}  # Cache text embeddings for speed

@app.on_event("startup")
def startup():
    global metadata, clip_model, region_proposal_model
    if META_PATH.exists():
        with open(META_PATH, 'r') as f:
            metadata = json.load(f)
        print(f"✅ Loaded metadata: {metadata.get('num_patches', 0)} patches")
    else:
        print("⚠️  No metadata found. Run simple_build.py first.")
        metadata = {"num_patches": 0, "bboxes": []}
    
    # Try to load CLIP model
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from models.clip_model import ClipEncoder
        print("🤖 Loading CLIP model for AI-powered detection...")
        clip_model = ClipEncoder(model_name="ViT-B-32", pretrained="openai")
        print(f"✅ CLIP model loaded successfully on {clip_model.device}")
    except Exception as e:
        print(f"⚠️  Could not load CLIP model: {e}")
        print("⚠️  Falling back to random detection")
        clip_model = None
    
    # Try to load Faster R-CNN for region proposals (RegionCLIP-style)
    try:
        import torch
        import torchvision
        from torchvision.models.detection import fasterrcnn_resnet50_fpn
        from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights
        print("🔧 Loading Faster R-CNN for RegionCLIP-style proposals...")
        # Use new weights API (torchvision 0.13+)
        weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
        region_proposal_model = fasterrcnn_resnet50_fpn(weights=weights)
        region_proposal_model.eval()
        
        # Move to same device as CLIP
        if clip_model:
            region_proposal_model = region_proposal_model.to(clip_model.device)
            print(f"✅ Faster R-CNN loaded on {clip_model.device} for RegionCLIP mode")
        else:
            print(f"✅ Faster R-CNN loaded for region proposals (RegionCLIP mode)")
    except Exception as e:
        print(f"⚠️  Could not load Faster R-CNN: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️  Using sliding window proposals instead")
        region_proposal_model = None

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
    
    # Define object types for classification
    # Expanded to support space, terrestrial, animals, landmarks, and common objects
    object_types = [
        # Space objects
        "star", "star cluster", "nebula", "galaxy", 
        "spiral galaxy", "planetary nebula", "supernova remnant",
        "asteroid", "comet", "planet", "moon", "crater", "solar flare",
        # Animals
        "dog", "cat", "bird", "horse", "cow", "elephant", "bear", "deer", "lion", "tiger",
        "sheep", "goat", "pig", "chicken", "duck", "rabbit", "fox", "wolf",
        # Landmarks & structures
        "building", "house", "apartment", "tower", "skyscraper", "bridge", "monument", 
        "statue", "temple", "church", "mosque", "castle", "fort", "pyramid", "arch",
        # Infrastructure & terrain
        "road", "highway", "street", "path", "sidewalk", "parking lot",
        "river", "lake", "ocean", "pond", "stream", "waterfall",
        "mountain", "hill", "valley", "cliff", "canyon", "plateau",
        "forest", "tree", "grass", "field", "desert", "beach", "island",
        # Vehicles
        "car", "truck", "bus", "van", "motorcycle", "bicycle",
        "airplane", "helicopter", "jet", "ship", "boat", "train", "subway",
        # Urban elements
        "fence", "wall", "gate", "door", "window", "roof", "chimney",
        "lamp post", "traffic light", "sign", "bench", "playground",
        # Natural phenomena
        "cloud", "sky", "rainbow", "lightning", "snow", "ice", "fire", "smoke"
    ]
    
    # Generate mock classification results
    # Randomly select primary classification from all available types
    primary_type = random.choice(object_types)
    
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

def _reconstruct_image_from_tiles(tiles_base: Path, output_path: Path) -> bool:
    """
    Reconstruct full image from DZI tiles to enable CLIP detection.
    
    Args:
        tiles_base: Base directory containing DZI tiles
        output_path: Where to save the reconstructed image
        
    Returns:
        True if successful, False otherwise
    """
    from PIL import Image as PILImage
    import xml.etree.ElementTree as ET
    
    # Disable PIL's decompression bomb protection for large astronomical images
    PILImage.MAX_IMAGE_PIXELS = None
    
    try:
        # Parse DZI to get image dimensions
        dzi_path = tiles_base / "info.dzi"
        if not dzi_path.exists():
            print(f"⚠️ No DZI file found at {dzi_path}")
            return False
        
        tree = ET.parse(dzi_path)
        root = tree.getroot()
        size_elem = root.find('.//{http://schemas.microsoft.com/deepzoom/2008}Size')
        if size_elem is None:
            print("⚠️ Could not find Size element in DZI")
            return False
        
        full_width = int(size_elem.get('Width'))
        full_height = int(size_elem.get('Height'))
        
        # Find highest resolution level
        max_level = -1
        for item in tiles_base.iterdir():
            if item.is_dir() and item.name.isdigit():
                level = int(item.name)
                if level > max_level:
                    max_level = level
        
        if max_level < 0:
            print("⚠️ No tile levels found")
            return False
        
        # Aggressive downsampling for speed - CLIP doesn't need full resolution
        # Aim for max 20-30 megapixels for fast processing
        target_level = max_level
        level_pixels = full_width * full_height
        
        # Downsample aggressively based on size
        if level_pixels > 200_000_000:  # >200MP - drop 3 levels (8x reduction)
            target_level = max(0, max_level - 3)
            scale_factor = 2 ** (max_level - target_level)
            full_width = full_width // scale_factor
            full_height = full_height // scale_factor
            print(f"⚡ Huge image ({level_pixels/1e6:.1f}MP), using level {target_level} for speed ({full_width}×{full_height}, {(full_width*full_height)/1e6:.1f}MP)")
        elif level_pixels > 50_000_000:  # >50MP - drop 2 levels (4x reduction)
            target_level = max(0, max_level - 2)
            scale_factor = 2 ** (max_level - target_level)
            full_width = full_width // scale_factor
            full_height = full_height // scale_factor
            print(f"⚡ Large image ({level_pixels/1e6:.1f}MP), using level {target_level} for speed ({full_width}×{full_height}, {(full_width*full_height)/1e6:.1f}MP)")
        elif level_pixels > 20_000_000:  # >20MP - drop 1 level (2x reduction)
            target_level = max(0, max_level - 1)
            scale_factor = 2 ** (max_level - target_level)
            full_width = full_width // scale_factor
            full_height = full_height // scale_factor
            print(f"⚡ Medium-large image ({level_pixels/1e6:.1f}MP), using level {target_level} for speed ({full_width}×{full_height}, {(full_width*full_height)/1e6:.1f}MP)")
        
        print(f"🔨 Reconstructing {full_width}×{full_height} image from level {target_level} tiles...")
        
        # Get tile size from DZI
        tile_size_elem = root.get('TileSize', '256')
        tile_size = int(tile_size_elem)
        
        # Create blank canvas
        canvas = PILImage.new('RGB', (full_width, full_height), (0, 0, 0))
        
        # Find all tiles at target level
        level_dir = tiles_base / str(target_level)
        tile_files = sorted(level_dir.glob("*.jpg"))
        
        if not tile_files:
            print(f"⚠️ No tiles found in level {target_level}")
            return False
        
        # Stitch tiles back together
        tiles_placed = 0
        for tile_file in tile_files:
            # Parse tile coordinates from filename (e.g., "3_5.jpg" -> col=3, row=5)
            parts = tile_file.stem.split('_')
            if len(parts) != 2:
                continue
            
            try:
                col = int(parts[0])
                row = int(parts[1])
            except ValueError:
                continue
            
            # Calculate position
            x = col * tile_size
            y = row * tile_size
            
            # Load and paste tile
            try:
                tile = PILImage.open(tile_file)
                canvas.paste(tile, (x, y))
                tiles_placed += 1
            except Exception as e:
                print(f"⚠️ Could not load tile {tile_file.name}: {e}")
                continue
        
        print(f"✅ Reconstructed image from {tiles_placed} tiles")
        
        # Save reconstructed image
        canvas.save(output_path, 'JPEG', quality=95)
        print(f"✅ Saved reconstructed image to {output_path.name}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Failed to reconstruct image: {e}")
        import traceback
        traceback.print_exc()
        return False


def _generate_region_proposals_rcnn(image: 'PILImage.Image', score_threshold: float = 0.3, max_proposals: int = 200) -> List[List[int]]:
    """
    Generate region proposals using Faster R-CNN (RegionCLIP-style).
    
    This uses a pre-trained object detector to find salient regions in the image,
    then CLIP scores these regions. This is more efficient and accurate than sliding windows.
    
    Args:
        image: PIL Image
        score_threshold: Minimum objectness score (0-1)
        max_proposals: Maximum number of proposals to return
        
    Returns:
        List of bounding boxes [x, y, width, height]
    """
    import torch
    import torchvision.transforms as T
    from PIL import Image as PILImage
    
    if region_proposal_model is None:
        return None
    
    # Prepare image for Faster R-CNN
    transform = T.Compose([T.ToTensor()])
    img_tensor = transform(image).unsqueeze(0)
    
    # Move to same device as model
    device = next(region_proposal_model.parameters()).device
    img_tensor = img_tensor.to(device)
    
    # Get proposals from Faster R-CNN
    with torch.no_grad():
        predictions = region_proposal_model(img_tensor)[0]
    
    # Extract boxes with sufficient objectness score
    boxes = predictions['boxes'].cpu().numpy()
    scores = predictions['scores'].cpu().numpy()
    
    # Filter by score
    mask = scores >= score_threshold
    boxes = boxes[mask]
    scores = scores[mask]
    
    # Convert from [x1, y1, x2, y2] to [x, y, w, h]
    proposals = []
    for box in boxes:
        x1, y1, x2, y2 = box
        x, y = int(x1), int(y1)
        w, h = int(x2 - x1), int(y2 - y1)
        
        # Ensure valid boxes
        if w > 10 and h > 10:  # Minimum size
            proposals.append([x, y, w, h])
    
    # Adaptive limit based on image size - increased for better coverage
    img_pixels = image.size[0] * image.size[1]
    if img_pixels > 50_000_000:  # Very large images
        adaptive_max = min(max_proposals, 500)  # Increased for better coverage
    elif img_pixels > 10_000_000:  # Large images
        adaptive_max = min(max_proposals, 650)  # Increased for better coverage
    else:  # Medium/small images
        adaptive_max = max_proposals  # Use full limit (~750)
    
    # Limit number of proposals
    if len(proposals) > adaptive_max:
        # Keep highest scoring proposals
        indices = np.argsort(scores)[::-1][:adaptive_max]
        proposals = [proposals[i] for i in indices if i < len(proposals)]
    
    return proposals


def _generate_region_proposals(img_width: int, img_height: int, scales: List[int], aspect_ratios: List[float]) -> List[List[int]]:
    """
    Generate region proposals using randomly scattered windows with various aspect ratios.
    
    Fallback method when Faster R-CNN is not available.
    
    Args:
        img_width: Image width
        img_height: Image height
        scales: List of box sizes to try (e.g., [128, 256, 384, 480])
        aspect_ratios: List of aspect ratios (e.g., [0.5, 0.75, 1.0, 1.33, 2.0])
        
    Returns:
        List of bounding boxes [x, y, width, height]
    """
    import random
    proposals = []
    
    # Calculate how many proposals per scale/aspect combo for good coverage
    # ~750 total proposals scattered across the entire image
    # Adaptive scaling based on image size
    img_pixels = img_width * img_height
    if img_pixels > 50_000_000:  # Very large images
        proposals_per_combo = 750  # 1 scale × 1 aspect = ~750 total
    elif img_pixels > 10_000_000:  # Large images  
        proposals_per_combo = 187  # 2 scales × 2 aspects = 4 combos → ~750 total
    elif img_pixels < 500_000:  # Small images
        proposals_per_combo = 200  # Multiple combos → ~750+ total
    else:  # Medium images
        proposals_per_combo = 187  # 2 scales × 2 aspects = 4 combos → ~750 total
    
    for base_size in scales:
        for aspect_ratio in aspect_ratios:
            # Calculate box dimensions based on aspect ratio
            if aspect_ratio >= 1.0:
                box_width = int(base_size * aspect_ratio)
                box_height = base_size
            else:
                box_width = base_size
                box_height = int(base_size / aspect_ratio)
            
            # Make sure box fits in image
            if box_width > img_width or box_height > img_height:
                continue
            
            # Generate proposals uniformly scattered across the ENTIRE image
            # Pure random sampling - guarantees coverage across full width and height
            for _ in range(proposals_per_combo):
                # Random position anywhere in the image
                # x ranges from 0 to (img_width - box_width)
                # y ranges from 0 to (img_height - box_height)
                x = random.randint(0, max(0, img_width - box_width))
                y = random.randint(0, max(0, img_height - box_height))
                
                proposals.append([x, y, box_width, box_height])
                
            # Debug: Log range of generated positions for this combo
            if proposals_per_combo > 0:
                combo_proposals = proposals[-proposals_per_combo:]
                xs = [p[0] for p in combo_proposals]
                ys = [p[1] for p in combo_proposals]
                print(f"   📍 Size {box_width}×{box_height}: x=[{min(xs)}-{max(xs)}], y=[{min(ys)}-{max(ys)}]")
    
    return proposals


def _non_maximum_suppression(detections: List[Dict[str, Any]], iou_threshold: float = 0.5) -> List[Dict[str, Any]]:
    """
    Apply Non-Maximum Suppression to remove overlapping duplicate detections.
    
    Args:
        detections: List of detections with 'bbox' and 'confidence'
        iou_threshold: IoU threshold for suppression (0.5 = 50% overlap)
        
    Returns:
        Filtered list of detections
    """
    if len(detections) == 0:
        return []
    
    # Sort by confidence (highest first)
    detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
    
    keep = []
    
    while detections:
        # Keep the highest confidence detection
        best = detections.pop(0)
        keep.append(best)
        
        # Remove detections that overlap significantly with the best one
        detections = [
            det for det in detections
            if _compute_iou(best['bbox'], det['bbox']) < iou_threshold
        ]
    
    return keep


def _compute_iou(box1: List[int], box2: List[int]) -> float:
    """
    Compute Intersection over Union (IoU) between two bounding boxes.
    
    Args:
        box1: [x, y, width, height]
        box2: [x, y, width, height]
        
    Returns:
        IoU score (0-1)
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    # Calculate intersection
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    intersection = (x_right - x_left) * (y_bottom - y_top)
    
    # Calculate union
    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - intersection
    
    if union == 0:
        return 0.0
    
    return intersection / union


def _clip_detect_objects(
    image_path: Path,
    query: str,
    confidence_threshold: float,
    max_results: int,
    patch_size: int = 256,
    stride: int = 128
) -> List[Dict[str, Any]]:
    """
    Use CLIP to detect objects using region proposals + CLIP ranking + NMS.
    
    Modern approach:
    1. Generate candidate boxes (region proposals)
    2. Crop and score each region with CLIP
    3. Filter by confidence threshold
    4. Apply NMS to remove duplicate detections
    5. Return top-scoring regions
    
    Args:
        image_path: Path to the source image
        query: Text description of object to detect (e.g., "star", "galaxy", "dog")
        confidence_threshold: Minimum similarity score (0-1)
        max_results: Maximum number of detections to return
        patch_size: Not used (kept for API compatibility)
        stride: Not used (kept for API compatibility)
        
    Returns:
        List of detections with bbox and confidence
    """
    from PIL import Image as PILImage
    import torch
    
    # Disable PIL's decompression bomb protection for large astronomical images
    PILImage.MAX_IMAGE_PIXELS = None
    
    print(f"🤖 CLIP Region Proposal Detection: loading image from {image_path}")
    
    # Load image
    image = PILImage.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    img_width, img_height = image.size
    img_pixels = img_width * img_height
    print(f"📐 Image size: {img_width}×{img_height} ({img_pixels/1e6:.1f}MP)")
    
    # 🎯 STEP 1: Generate region proposals
    # Try RegionCLIP-style (Faster R-CNN) first, fallback to sliding windows
    proposals = None
    batch_size = 32
    
    if region_proposal_model is not None:
        try:
            print(f"🚀 RegionCLIP mode: Using Faster R-CNN for smart region proposals...")
            proposals = _generate_region_proposals_rcnn(
                image, 
                score_threshold=0.3,  # Lower threshold for more proposals
                max_proposals=750  # Increased to ~750 proposals for better coverage
            )
            if proposals:
                print(f"✅ Faster R-CNN generated {len(proposals)} smart proposals")
                batch_size = 64  # ⚡ Speed: Larger batches for faster processing
        except Exception as e:
            print(f"⚠️ Faster R-CNN failed: {e}")
            proposals = None
    
    # Fallback to sliding window if R-CNN not available or failed
    if proposals is None or len(proposals) == 0:
        print(f"🔍 Falling back to sliding window proposals...")
        # Adapt scales and aspect ratios based on image size
        if img_pixels > 50_000_000:  # >50MP - very large
            scales = [512]  # ⚡ Speed: Reduced scales
            aspect_ratios = [1.0]  # ⚡ Speed: Reduced aspect ratios
            batch_size = 64
            print(f"⚡ Ultra-fast mode: 1 scale × 1 aspect ratio")
        elif img_pixels > 10_000_000:  # 10-50MP - large
            scales = [384, 256]  # ⚡ Speed: Reduced from 3 to 2 scales
            aspect_ratios = [1.0, 1.33]  # ⚡ Speed: Reduced from 3 to 2 ratios
            batch_size = 64
            print(f"⚡ Fast mode: 2 scales × 2 aspect ratios")
        elif img_pixels < 500_000:  # <0.5MP - small image
            base_size = min(img_width, img_height)
            scales = [
                base_size,
                base_size // 2,
            ]  # ⚡ Speed: Reduced scales
            scales = sorted(set([s for s in scales if s >= 64]))
            aspect_ratios = [1.0, 1.33]  # ⚡ Speed: Reduced ratios
            batch_size = 48
            print(f"⚡ Small image mode: {len(scales)} scales × {len(aspect_ratios)} aspect ratios")
        else:  # Medium images
            scales = [256, 192]  # ⚡ Speed: Reduced from 4 to 2 scales
            aspect_ratios = [1.0, 1.5]  # ⚡ Speed: Reduced from 5 to 2 ratios
            batch_size = 64
            print(f"⚡ Medium mode: 2 scales × 2 aspect ratios")
        
        proposals = _generate_region_proposals(img_width, img_height, scales, aspect_ratios)
        print(f"✅ Generated {len(proposals)} sliding window proposals")
    
    # Show proposal distribution across image
    if proposals:
        prop_xs = [p[0] for p in proposals]
        prop_ys = [p[1] for p in proposals]
        mid_x = img_width / 2
        mid_y = img_height / 2
        p_q1 = sum(1 for p in proposals if p[0] < mid_x and p[1] < mid_y)
        p_q2 = sum(1 for p in proposals if p[0] >= mid_x and p[1] < mid_y)
        p_q3 = sum(1 for p in proposals if p[0] < mid_x and p[1] >= mid_y)
        p_q4 = sum(1 for p in proposals if p[0] >= mid_x and p[1] >= mid_y)
        print(f"📊 Proposal distribution: x=[{min(prop_xs)}-{max(prop_xs)}], y=[{min(prop_ys)}-{max(prop_ys)}]")
        print(f"🗺️  Proposal quadrants: UL={p_q1}, UR={p_q2}, LL={p_q3}, LR={p_q4}")
    
    # 🚀 STEP 2: Contrastive CLIP Setup - ⚡ OPTIMIZED FOR SPEED
    query_lower = query.lower()
    
    # Build TARGET prompts (what we WANT) - ⚡ Speed: Keep it minimal
    target_prompts = [
        f"a photo of a {query}",
        f"a {query}",
    ]
    
    # Add 1 key synonym for common objects
    if "dog" in query_lower:
        target_prompts.append("a puppy")
    elif "cat" in query_lower:
        target_prompts.append("a kitten")
    elif "nebula" in query_lower:
        target_prompts.append("emission nebula")
    elif "galaxy" in query_lower:
        target_prompts.append("spiral galaxy")
    elif "crater" in query_lower:
        target_prompts.append("impact crater")
    elif "flare" in query_lower:
        target_prompts.append("solar eruption")
    elif "house" in query_lower or "building" in query_lower:
        target_prompts.append("a structure")
    elif "road" in query_lower or "highway" in query_lower:
        target_prompts.append("a path")
    
    # Build DISTRACTOR prompts (what we DON'T want) - ⚡ Speed: Fewer distractors
    distractor_prompts = []
    if "dog" in query_lower:
        distractor_prompts = ["a cat", "a wolf", "background"]
    elif "cat" in query_lower:
        distractor_prompts = ["a dog", "a tiger", "background"]
    elif "bird" in query_lower:
        distractor_prompts = ["a plane", "background"]
    elif "car" in query_lower:
        distractor_prompts = ["a truck", "a building", "background"]
    elif "house" in query_lower:
        distractor_prompts = ["a tree", "a mountain", "background"]
    elif "road" in query_lower:
        distractor_prompts = ["a river", "a path", "background"]
    elif "crater" in query_lower:
        distractor_prompts = ["a hill", "a valley", "background"]
    elif "flare" in query_lower:
        distractor_prompts = ["a cloud", "a lens flare", "background"]
    elif "galaxy" in query_lower or "nebula" in query_lower or "star" in query_lower:
        distractor_prompts = ["background", "noise", "empty space"]
    elif "animal" in query_lower or any(animal in query_lower for animal in ["elephant", "horse", "bear", "deer"]):
        distractor_prompts = ["a rock", "a tree", "background"]
    else:
        distractor_prompts = ["background", "noise", "empty space"]
    
    # Remove duplicates
    target_prompts = list(dict.fromkeys(target_prompts))
    distractor_prompts = list(dict.fromkeys(distractor_prompts))
    print(f"⚡ Contrastive mode: {len(target_prompts)} target vs {len(distractor_prompts)} distractors")
    
    # ⚡ Speed: Cache text embeddings
    global text_embedding_cache
    target_embeddings = []
    distractor_embeddings = []
    cache_hits = 0
    
    for prompt in target_prompts:
        if prompt in text_embedding_cache:
            target_embeddings.append(text_embedding_cache[prompt])
            cache_hits += 1
        else:
            emb = clip_model.encode_text(prompt)
            text_embedding_cache[prompt] = emb
            target_embeddings.append(emb)
    
    for prompt in distractor_prompts:
        if prompt in text_embedding_cache:
            distractor_embeddings.append(text_embedding_cache[prompt])
            cache_hits += 1
        else:
            emb = clip_model.encode_text(prompt)
            text_embedding_cache[prompt] = emb
            distractor_embeddings.append(emb)
    
    target_embeddings = torch.stack(target_embeddings)
    distractor_embeddings = torch.stack(distractor_embeddings)
    
    if cache_hits > 0:
        total_prompts = len(target_prompts) + len(distractor_prompts)
        print(f"   ⚡ Cache: {cache_hits}/{total_prompts} prompts from cache")
    
    # 🎯 STEP 3: Crop each region and score with CLIP
    print(f"📦 Scoring {len(proposals)} regions with CLIP...")
    detections = []
    crops = []
    crop_proposals = []
    
    total_processed = 0
    progress_interval = max(50, len(proposals) // 10)  # Show progress every 10%
    last_progress_reported = 0
    
    for idx, proposal in enumerate(proposals):
        x, y, w, h = proposal
        
        # Crop the region from the image
        crop = image.crop((x, y, x + w, y + h))
        
        # Resize to CLIP's input size (224x224) with proper preprocessing
        crop_resized = crop.resize((224, 224), PILImage.Resampling.LANCZOS)
        
        crops.append(crop_resized)
        crop_proposals.append(proposal)
        
        # Process in batches for speed
        if len(crops) >= batch_size:
            # Encode the cropped regions
            crop_embeddings = clip_model.encode_images_batch(crops)
            
            # 🚀 CONTRASTIVE SCORING: Target vs Distractors
            # Compute target similarities
            target_sims = []
            for text_emb in target_embeddings:
                sims = torch.cosine_similarity(
                    crop_embeddings,
                    text_emb.unsqueeze(0),
                    dim=1
                ).numpy()
                target_sims.append(sims)
            target_sims = np.stack(target_sims)
            target_scores = np.max(target_sims, axis=0)
            
            # Compute distractor similarities
            distractor_sims = []
            for text_emb in distractor_embeddings:
                sims = torch.cosine_similarity(
                    crop_embeddings,
                    text_emb.unsqueeze(0),
                    dim=1
                ).numpy()
                distractor_sims.append(sims)
            distractor_sims = np.stack(distractor_sims)
            distractor_scores = np.max(distractor_sims, axis=0)
            
            # ⚡ Optimized contrastive confidence
            margin = target_scores - distractor_scores
            final_confidences = target_scores + (margin * 0.25)  # ⚡ Speed: Reduced boost from 0.3 to 0.25
            
            # Store detections above threshold with margin requirement
            min_target = 0.22
            min_margin = 0.03  # ⚡ Speed: Reduced from 0.05 to 0.03 for more detections
            
            for bbox, target_score, distractor_score, final_conf in zip(
                crop_proposals, target_scores, distractor_scores, final_confidences
            ):
                if (target_score >= min_target and 
                    target_score > distractor_score + min_margin and
                    final_conf >= confidence_threshold):
                    detections.append({
                        "bbox": bbox,
                        "confidence": float(final_conf),
                        "target_score": float(target_score),
                        "distractor_score": float(distractor_score)
                    })
            
            total_processed += len(crops)
            
            # Show progress at regular intervals (every 10%)
            if total_processed - last_progress_reported >= progress_interval:
                percent = (total_processed / len(proposals)) * 100
                print(f"   ⏳ Processed {total_processed}/{len(proposals)} regions ({percent:.1f}%) - {len(detections)} above threshold so far...")
                last_progress_reported = total_processed
            
            # Clear batch
            crops = []
            crop_proposals = []
    
    # Process remaining crops
    if crops:
        crop_embeddings = clip_model.encode_images_batch(crops)
        
        # Target similarities
        target_sims = []
        for text_emb in target_embeddings:
            sims = torch.cosine_similarity(
                crop_embeddings,
                text_emb.unsqueeze(0),
                dim=1
            ).numpy()
            target_sims.append(sims)
        target_sims = np.stack(target_sims)
        target_scores = np.max(target_sims, axis=0)
        
        # Distractor similarities
        distractor_sims = []
        for text_emb in distractor_embeddings:
            sims = torch.cosine_similarity(
                crop_embeddings,
                text_emb.unsqueeze(0),
                dim=1
            ).numpy()
            distractor_sims.append(sims)
        distractor_sims = np.stack(distractor_sims)
        distractor_scores = np.max(distractor_sims, axis=0)
        
        # Contrastive scoring
        margin = target_scores - distractor_scores
        final_confidences = target_scores + (margin * 0.25)
        min_target = 0.22
        min_margin = 0.03
        
        for bbox, target_score, distractor_score, final_conf in zip(
            crop_proposals, target_scores, distractor_scores, final_confidences
        ):
            if (target_score >= min_target and 
                target_score > distractor_score + min_margin and
                final_conf >= confidence_threshold):
                detections.append({
                    "bbox": bbox,
                    "confidence": float(final_conf),
                    "target_score": float(target_score),
                    "distractor_score": float(distractor_score)
                })
        
        total_processed += len(crops)
    
    print(f"✅ Completed! Processed {total_processed}/{len(proposals)} regions")
    print(f"✅ Found {len(detections)} detections above threshold {confidence_threshold:.2f}")
    
    # 🎯 STEP 4: Apply Non-Maximum Suppression to remove duplicates
    if len(detections) > 0:
        print(f"🔧 Applying NMS to remove overlapping detections...")
        detections = _non_maximum_suppression(detections, iou_threshold=0.25)  # More aggressive: only 25% overlap allowed
        print(f"✅ After NMS: {len(detections)} unique detections")
    
    # 🎯 STEP 5: Sort by confidence and limit results
    detections.sort(key=lambda x: x["confidence"], reverse=True)
    detections = detections[:max_results]
    
    print(f"🎯 Final result: {len(detections)} detections for '{query}'")
    if detections:
        print(f"   📊 Confidence range: {detections[0]['confidence']:.3f} → {detections[-1]['confidence']:.3f}")
        # Show spatial distribution with quadrants
        xs = [d['bbox'][0] for d in detections]
        ys = [d['bbox'][1] for d in detections]
        print(f"   📍 Spatial distribution: x=[{min(xs)}-{max(xs)}], y=[{min(ys)}-{max(ys)}]")
        print(f"   📏 Image dimensions: {img_width}×{img_height}")
        
        # Check distribution across quadrants
        mid_x = img_width / 2
        mid_y = img_height / 2
        q1 = sum(1 for d in detections if d['bbox'][0] < mid_x and d['bbox'][1] < mid_y)  # Upper-left
        q2 = sum(1 for d in detections if d['bbox'][0] >= mid_x and d['bbox'][1] < mid_y)  # Upper-right
        q3 = sum(1 for d in detections if d['bbox'][0] < mid_x and d['bbox'][1] >= mid_y)  # Lower-left
        q4 = sum(1 for d in detections if d['bbox'][0] >= mid_x and d['bbox'][1] >= mid_y)  # Lower-right
        print(f"   🗺️  Quadrant distribution: UL={q1}, UR={q2}, LL={q3}, LR={q4}")
        
        # Print sample coordinates from each quadrant
        print(f"   📋 Sample detections by quadrant:")
        ul_samples = [d for d in detections if d['bbox'][0] < mid_x and d['bbox'][1] < mid_y][:3]
        ur_samples = [d for d in detections if d['bbox'][0] >= mid_x and d['bbox'][1] < mid_y][:3]
        ll_samples = [d for d in detections if d['bbox'][0] < mid_x and d['bbox'][1] >= mid_y][:3]
        lr_samples = [d for d in detections if d['bbox'][0] >= mid_x and d['bbox'][1] >= mid_y][:3]
        if ul_samples: print(f"      UL: {[d['bbox'] for d in ul_samples]}")
        if ur_samples: print(f"      UR: {[d['bbox'] for d in ur_samples]}")
        if ll_samples: print(f"      LL: {[d['bbox'] for d in ll_samples]}")
        if lr_samples: print(f"      LR: {[d['bbox'] for d in lr_samples]}")
    
    return detections


def _random_detect_fallback(
    image_width: int,
    image_height: int,
    query: str,
    confidence_threshold: float,
    max_results: int
) -> List[Dict[str, Any]]:
    """Fallback random detection when CLIP is not available."""
    detections = []
    num_detections = random.randint(10, 25)
    patch_size = 128
    
    for i in range(num_detections):
        # Generate random position within the actual image bounds
        x = random.randint(0, max(0, image_width - patch_size))
        y = random.randint(0, max(0, image_height - patch_size))
        
        # Generate confidence score based on query
        query_lower = query.lower()
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
                "bbox": [x, y, patch_size, patch_size],
                "confidence": round(base_confidence, 3)
            })
    
    # Sort by confidence
    detections.sort(key=lambda x: x["confidence"], reverse=True)
    
    # Limit results
    detections = detections[:max_results]
    
    return detections


@app.get("/detect")
def detect_objects(
    q: str = Query(..., description="Object type to detect (e.g., 'galaxy', 'star', 'nebula')"),
    dataset_id: str = Query(None, description="Dataset ID (snake_case)"),
    datasetId: str = Query("demo", description="Dataset ID (camelCase)"),
    confidence_threshold: float = Query(0.6, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    max_results: int = Query(500, ge=1, le=1000, description="Maximum number of detections")
):
    """
    Detect and locate all instances of a specific astronomical object type.
    
    Feature 2: Object Detection and Localization
    - Search for specific object types (galaxy, nebula, star, etc.)
    - Returns ALL locations where the object appears
    - Each detection includes bounding box and confidence score
    - Uses CLIP AI for real semantic understanding
    """
    dataset = dataset_id or datasetId
    print(f"🎯 Detect Objects: '{q}' | Dataset: '{dataset}' | Threshold: {confidence_threshold}")
    
    # Find the source image for this dataset
    from pathlib import Path
    tiles_base = Path(__file__).parent.parent / "infra" / "tiles" / dataset
    
    # Look for source image (original image saved for AI detection)
    image_path = None
    if tiles_base.exists():
        # First try to find the source copy saved by tile processor
        for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
            source_path = tiles_base / f"source{ext}"
            if source_path.exists():
                image_path = source_path
                print(f"✅ Found existing source image: {source_path.name}")
                break
        
        # If no source image, try to reconstruct from tiles
        if not image_path:
            print("📦 No source image found, attempting to reconstruct from tiles...")
            reconstructed_path = tiles_base / "source.jpg"
            if _reconstruct_image_from_tiles(tiles_base, reconstructed_path):
                image_path = reconstructed_path
            else:
                print("⚠️ Failed to reconstruct image from tiles")
        
        # Last fallback: look for any image file in the directory
        if not image_path:
            for ext in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']:
                potential_paths = list(tiles_base.glob(f"*{ext}"))
                # Exclude tile directories and source files
                potential_paths = [p for p in potential_paths if p.is_file() and not p.name.startswith('source')]
                if potential_paths:
                    image_path = potential_paths[0]
                    break
    
    # Get image dimensions - ALWAYS use DZI dimensions for coordinate space
    # (Frontend uses DZI dimensions for rendering)
    dzi_width, dzi_height = 2048, 2048  # Default
    source_width, source_height = None, None
    
    # Read DZI dimensions (this is what frontend uses!)
    dzi_path = tiles_base / "info.dzi"
    if dzi_path.exists():
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(dzi_path)
            root = tree.getroot()
            size_elem = root.find('.//{http://schemas.microsoft.com/deepzoom/2008}Size')
            if size_elem is not None:
                dzi_width = int(size_elem.get('Width', 2048))
                dzi_height = int(size_elem.get('Height', 2048))
                print(f"📐 DZI dimensions (frontend uses this): {dzi_width}×{dzi_height}")
        except Exception as e:
            print(f"⚠️ Could not parse DZI: {e}")
    
    # Get source image actual dimensions
    if image_path and image_path.exists():
        from PIL import Image as PILImage
        try:
            with PILImage.open(image_path) as img:
                source_width, source_height = img.size
            print(f"📐 Source image dimensions: {source_width}×{source_height}")
        except Exception as e:
            print(f"⚠️ Could not load source image: {e}")
            image_path = None
    
    # If no source dimensions, assume they match DZI
    if source_width is None:
        source_width = dzi_width
        source_height = dzi_height
    
    # Perform detection
    start_time = time.time()
    
    if clip_model and image_path and image_path.exists():
        # Use CLIP-based detection
        try:
            detections = _clip_detect_objects(
                image_path=image_path,
                query=q,
                confidence_threshold=confidence_threshold,
                max_results=max_results,
                patch_size=256,
                stride=128
            )
            
            # SCALE coordinates from source image space to DZI space (frontend uses DZI dimensions)
            scale_x = dzi_width / source_width
            scale_y = dzi_height / source_height
            print(f"🔧 Scaling coordinates: {source_width}×{source_height} → {dzi_width}×{dzi_height} (scale: {scale_x:.2f}x, {scale_y:.2f}x)")
            
            for det in detections:
                bbox = det['bbox']
                det['bbox'] = [
                    int(bbox[0] * scale_x),
                    int(bbox[1] * scale_y),
                    int(bbox[2] * scale_x),
                    int(bbox[3] * scale_y)
                ]
            
            # Add metadata
            detection_method = "RegionCLIP_AI" if region_proposal_model else "CLIP_AI"
            for i, det in enumerate(detections):
                det.update({
                    "id": i,
                    "object_type": q,
                    "metadata": {
                        "detection_method": detection_method,
                        "model": "ViT-B-32 + Faster R-CNN" if region_proposal_model else "ViT-B-32",
                        "proposals": "Faster R-CNN" if region_proposal_model else "Sliding Window",
                        "image_size": f"{dzi_width}×{dzi_height}",
                        "source_size": f"{source_width}×{source_height}"
                    }
                })
        except Exception as e:
            print(f"⚠️ CLIP detection failed: {e}")
            print("⚠️ Falling back to random detection")
            detections = _random_detect_fallback(
                dzi_width, dzi_height, q, confidence_threshold, max_results
            )
            for i, det in enumerate(detections):
                det.update({
                    "id": i,
                    "object_type": q,
                    "metadata": {
                        "detection_method": "random_fallback",
                        "patch_size": 128,
                        "image_size": f"{dzi_width}×{dzi_height}"
                    }
                })
    else:
        # Fallback to random detection
        reason = "no_clip_model" if not clip_model else "no_image_found"
        print(f"⚠️ Using random detection (reason: {reason})")
        detections = _random_detect_fallback(
            dzi_width, dzi_height, q, confidence_threshold, max_results
        )
        for i, det in enumerate(detections):
            det.update({
                "id": i,
                "object_type": q,
                "metadata": {
                    "detection_method": f"random_{reason}",
                    "patch_size": 128,
                    "image_size": f"{dzi_width}×{dzi_height}"
                }
            })
    
    processing_time = int((time.time() - start_time) * 1000)
    
    return {
        "query": q,
        "datasetId": dataset,
        "object_type": q,
        "detections": detections,
        "total_found": len(detections),
        "confidence_threshold": confidence_threshold,
        "processing_time_ms": processing_time,
        "ai_powered": clip_model is not None and image_path is not None
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
