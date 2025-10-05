"""Detection router - proxies to AI service for object detection."""

import httpx
from fastapi import APIRouter, Query, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import AI_URL, RATE_LIMIT_SEARCH

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("")
@limiter.limit(RATE_LIMIT_SEARCH)
async def detect_objects(
    request: Request,
    q: str = Query(..., description="Object type to detect (e.g., 'galaxy', 'star', 'nebula')"),
    datasetId: str = Query(..., description="Dataset to search"),
    confidence_threshold: float = Query(0.6, ge=0.0, le=1.0, description="Minimum confidence"),
    max_results: int = Query(500, ge=1, le=1000, description="Max detections to return"),
):
    """
    Detect and locate all instances of a specific astronomical object.
    
    This endpoint enables Feature 2: Object Detection
    - User searches for a specific object type (e.g., "galaxy", "nebula")
    - AI finds and pinpoints ALL such objects in the image
    - Returns all locations with bounding boxes and confidence scores
    """
    try:
        # Pass dataset ID directly to AI service (AI service handles all datasets now)
        ai_dataset_id = datasetId
        
        # Very long timeout for CLIP detection (may need to reconstruct + analyze large images)
        # First detection can take 2-3 minutes for huge images
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.get(
                f"{AI_URL}/detect",
                params={
                    "q": q,
                    "datasetId": ai_dataset_id,
                    "confidence_threshold": confidence_threshold,
                    "max_results": max_results
                },
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "query": q,
                "datasetId": datasetId,
                "object_type": data.get("object_type"),
                "detections": data.get("detections", []),
                "total_found": data.get("total_found", 0),
                "confidence_threshold": confidence_threshold,
            }
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Detection failed: {str(e)}",
        )

