"""Main AI service application."""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

from app.indexer import ImageIndexer, build_index_for_dataset

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

