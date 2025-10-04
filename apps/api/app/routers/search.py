"""Search router - proxies to AI service."""

import httpx
from typing import Optional
from fastapi import APIRouter, Query, Request, HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import AI_URL, RATE_LIMIT_SEARCH

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("")
@limiter.limit(RATE_LIMIT_SEARCH)
async def search(
    request: Request,
    q: str = Query(..., description="Search query text"),
    datasetId: str = Query(..., description="Dataset to search"),
    topK: int = Query(20, description="Number of results to return"),
):
    """
    Search for regions in a dataset using AI semantic search.
    Rate limited to prevent abuse.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{AI_URL}/search",
                params={"q": q, "datasetId": datasetId, "topK": topK},
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "query": q,
                "datasetId": datasetId,
                "results": data.get("results", []),
                "total": data.get("total", 0),
            }
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service unavailable: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )

