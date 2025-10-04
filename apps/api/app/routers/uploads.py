"""Upload and processing router."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    BackgroundTasks,
)
from sqlmodel import Session

from app.config import DATA_DIR, TILES_DIR
from app.db import get_session
from app.models import Dataset
from app.tile_processor import TileProcessor, TileProcessingError

router = APIRouter()

# Setup directories
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)

# Initialize tile processor
tile_processor = TileProcessor(tiles_base_dir=TILES_DIR)

# In-memory storage for processing status (in production, use Redis or database)
processing_status: dict = {}


class UploadResponse:
    """Response model for upload endpoint."""
    
    @staticmethod
    def format(dataset_id: str, status: str, message: str, **kwargs) -> dict:
        """Format upload response."""
        return {
            "datasetId": dataset_id,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }


def process_image_background(
    dataset_id: str,
    image_path: Path,
    name: str,
    description: Optional[str],
    session: Session,
):
    """
    Background task to process uploaded image and create dataset.
    
    Args:
        dataset_id: Unique identifier for the dataset
        image_path: Path to uploaded image
        name: Dataset name
        description: Optional dataset description
        session: Database session
    """
    try:
        # Update status
        processing_status[dataset_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Starting tile generation...",
        }
        
        def progress_callback(current: int, total: int, message: str):
            """Update processing progress."""
            progress = int((current / total) * 100) if total > 0 else 0
            processing_status[dataset_id] = {
                "status": "processing",
                "progress": progress,
                "message": message,
            }
        
        # Generate tiles
        result = tile_processor.generate_tiles(
            image_path=image_path,
            dataset_id=dataset_id,
            progress_callback=progress_callback,
        )
        
        # Create dataset entry
        dataset = Dataset(
            id=dataset_id,
            name=name,
            description=description or f"Uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            tile_type="dzi",
            tile_url=result["tile_url"],
            levels=json.dumps([i for i in range(result["levels"])]),
            pixel_size=json.dumps([result["width"], result["height"]]),
            metadata_={
                "original_filename": image_path.name,
                "upload_date": datetime.now().isoformat(),
                "width": result["width"],
                "height": result["height"],
                "total_tiles": result["total_tiles"],
                "is_uploaded": True,
            },
        )
        
        session.add(dataset)
        session.commit()
        
        # Update status
        processing_status[dataset_id] = {
            "status": "complete",
            "progress": 100,
            "message": "Processing complete!",
            "result": {
                "width": result["width"],
                "height": result["height"],
                "levels": result["levels"],
                "totalTiles": result["total_tiles"],
            },
        }
        
    except TileProcessingError as e:
        processing_status[dataset_id] = {
            "status": "error",
            "progress": 0,
            "message": str(e),
        }
    except Exception as e:
        processing_status[dataset_id] = {
            "status": "error",
            "progress": 0,
            "message": f"Unexpected error: {str(e)}",
        }


@router.post("/upload", response_model=dict, status_code=202)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Image file to upload"),
    name: str = Form(..., description="Dataset name"),
    description: Optional[str] = Form(None, description="Dataset description"),
    session: Session = Depends(get_session),
):
    """
    Upload an image and process it into tiles.
    
    The image will be validated, saved, and processed in the background.
    Use the status endpoint to check processing progress.
    
    - **file**: Image file (JPG, PNG, TIFF) - max 500MB
    - **name**: Display name for the dataset
    - **description**: Optional description
    
    Returns a dataset ID that can be used to check processing status.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only image files are allowed.",
        )
    
    # Generate unique dataset ID
    dataset_id = str(uuid.uuid4())
    
    # Determine file extension
    original_filename = file.filename or "upload.jpg"
    file_ext = Path(original_filename).suffix.lower()
    if not file_ext:
        file_ext = ".jpg"
    
    # Save uploaded file
    upload_path = UPLOAD_DIR / f"{dataset_id}{file_ext}"
    
    try:
        # Stream file to disk (memory efficient for large files)
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                buffer.write(chunk)
        
        # Quick validation
        try:
            tile_processor.validate_image(upload_path)
        except TileProcessingError as e:
            upload_path.unlink()  # Clean up invalid file
            raise HTTPException(status_code=400, detail=str(e))
        
        # Initialize processing status
        processing_status[dataset_id] = {
            "status": "queued",
            "progress": 0,
            "message": "Upload complete. Queued for processing...",
        }
        
        # Queue background processing
        # Note: We need to create a new session for the background task
        # since FastAPI sessions are request-scoped
        from app.db import engine
        from sqlmodel import Session as SQLSession
        
        def run_processing():
            with SQLSession(engine) as bg_session:
                process_image_background(
                    dataset_id=dataset_id,
                    image_path=upload_path,
                    name=name,
                    description=description,
                    session=bg_session,
                )
        
        background_tasks.add_task(run_processing)
        
        return UploadResponse.format(
            dataset_id=dataset_id,
            status="accepted",
            message="Image uploaded successfully. Processing started.",
            statusUrl=f"/uploads/status/{dataset_id}",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}",
        )


@router.get("/status/{dataset_id}", response_model=dict)
async def get_processing_status(dataset_id: str):
    """
    Get the processing status of an uploaded image.
    
    Returns:
    - **status**: One of: queued, processing, complete, error
    - **progress**: Percentage complete (0-100)
    - **message**: Current status message
    - **result**: Processing results (when complete)
    """
    if dataset_id not in processing_status:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found or processing not started",
        )
    
    status = processing_status[dataset_id]
    
    return {
        "datasetId": dataset_id,
        **status,
        "timestamp": datetime.now().isoformat(),
    }


@router.delete("/{dataset_id}", response_model=dict)
async def delete_dataset(
    dataset_id: str,
    session: Session = Depends(get_session),
):
    """
    Delete a dataset and its tiles.
    
    This will remove:
    - Database entry
    - All generated tiles
    - Original uploaded image
    """
    # Get dataset
    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Delete tiles
        tiles_dir = TILES_DIR / dataset_id
        if tiles_dir.exists():
            import shutil
            shutil.rmtree(tiles_dir)
        
        # Delete uploaded image
        for ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
            upload_file = UPLOAD_DIR / f"{dataset_id}{ext}"
            if upload_file.exists():
                upload_file.unlink()
        
        # Delete database entry
        session.delete(dataset)
        session.commit()
        
        # Clean up processing status
        if dataset_id in processing_status:
            del processing_status[dataset_id]
        
        return {
            "message": "Dataset deleted successfully",
            "datasetId": dataset_id,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete dataset: {str(e)}",
        )


@router.get("/health")
async def health_check():
    """Check upload service health."""
    return {
        "status": "ok",
        "upload_dir": str(UPLOAD_DIR),
        "tiles_dir": str(TILES_DIR),
        "active_processing": len([
            k for k, v in processing_status.items()
            if v["status"] in ["queued", "processing"]
        ]),
    }

