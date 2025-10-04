"""Classification router - proxies to AI service for object classification."""

import httpx
from typing import List
from fastapi import APIRouter, Query, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import AI_URL, RATE_LIMIT_SEARCH

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("")
@limiter.limit(RATE_LIMIT_SEARCH)
async def classify_region(
    request: Request,
    datasetId: str = Query(..., description="Dataset ID"),
    bbox: str = Query(..., description="Bounding box as 'x,y,width,height'"),
):
    """
    Classify what astronomical object is in a given region.
    
    This endpoint enables Feature 1: Object Classification
    - User annotates a region on the image
    - AI identifies what's in that region (star, nebula, galaxy, etc.)
    - Returns classification with confidence scores
    """
    try:
        # Parse bbox string to list
        bbox_parts = [int(x.strip()) for x in bbox.split(',')]
        if len(bbox_parts) != 4:
            raise ValueError("bbox must have 4 values: x,y,width,height")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{AI_URL}/classify",
                params={"dataset_id": datasetId, "bbox": bbox_parts},
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "datasetId": datasetId,
                "bbox": bbox_parts,
                "primary_classification": data.get("primary_classification"),
                "confidence": data.get("confidence"),
                "all_classifications": data.get("all_classifications", []),
                "processing_time_ms": data.get("processing_time_ms", 0)
            }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid bbox format: {str(e)}",
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}",
        )

