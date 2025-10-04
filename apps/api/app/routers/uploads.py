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
    cleanup_upload: bool = True,
):
    """
    Background task to process uploaded image and create dataset.
    
    Args:
        dataset_id: Unique identifier for the dataset
        image_path: Path to uploaded image
        name: Dataset name
        description: Optional dataset description
        session: Database session
        cleanup_upload: Whether to delete the original upload after processing (default: True)
    """
    import logging
    import shutil
    
    logger = logging.getLogger(__name__)
    
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
                "upload_cleaned": cleanup_upload,
            },
        )
        
        session.add(dataset)
        session.commit()
        
        # Clean up original upload file to save disk space (optional)
        if cleanup_upload:
            try:
                if image_path.exists():
                    image_path.unlink()
                    logger.info(f"Cleaned up upload file: {image_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up upload file {image_path}: {e}")
        
        # Clean up any temp directories created by PIL/Pillow
        try:
            temp_dir = UPLOAD_DIR / "temp"
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory: {e}")
        
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
        # Clean up upload file on error
        try:
            if image_path.exists():
                image_path.unlink()
                logger.info(f"Cleaned up upload file after error: {image_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up upload file after error: {cleanup_error}")
            
    except Exception as e:
        processing_status[dataset_id] = {
            "status": "error",
            "progress": 0,
            "message": f"Unexpected error: {str(e)}",
        }
        # Clean up upload file on error
        try:
            if image_path.exists():
                image_path.unlink()
                logger.info(f"Cleaned up upload file after error: {image_path}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up upload file after error: {cleanup_error}")


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
    Delete a dataset and its tiles (robust deletion).
    
    This will attempt to remove all traces of the dataset:
    - Database entry
    - All generated tiles
    - Original uploaded image
    - Processing status
    
    The deletion is robust - it continues even if some parts fail,
    ensuring maximum cleanup even for corrupted datasets.
    """
    import shutil
    import logging
    
    logger = logging.getLogger(__name__)
    errors = []
    success_count = 0
    
    # Try to get dataset from database
    dataset = session.get(Dataset, dataset_id)
    dataset_existed = dataset is not None
    
    # 1. Delete tiles directory (even if dataset not in DB)
    try:
        tiles_dir = TILES_DIR / dataset_id
        if tiles_dir.exists():
            shutil.rmtree(tiles_dir, ignore_errors=True)
            success_count += 1
            logger.info(f"Deleted tiles directory: {tiles_dir}")
        else:
            logger.info(f"Tiles directory not found: {tiles_dir}")
    except Exception as e:
        errors.append(f"Tiles deletion error: {str(e)}")
        logger.warning(f"Failed to delete tiles for {dataset_id}: {e}")
    
    # 2. Delete uploaded image (try all possible extensions)
    for ext in [".jpg", ".jpeg", ".png", ".tiff", ".tif"]:
        try:
            upload_file = UPLOAD_DIR / f"{dataset_id}{ext}"
            if upload_file.exists():
                upload_file.unlink()
                success_count += 1
                logger.info(f"Deleted upload file: {upload_file}")
        except Exception as e:
            errors.append(f"Upload file {ext} deletion error: {str(e)}")
            logger.warning(f"Failed to delete upload file {dataset_id}{ext}: {e}")
    
    # 2.5. Clean up any temp directories
    try:
        temp_upload_dir = UPLOAD_DIR / "temp" / dataset_id
        if temp_upload_dir.exists():
            shutil.rmtree(temp_upload_dir, ignore_errors=True)
            success_count += 1
            logger.info(f"Deleted temp directory: {temp_upload_dir}")
    except Exception as e:
        errors.append(f"Temp directory deletion error: {str(e)}")
        logger.warning(f"Failed to delete temp directory for {dataset_id}: {e}")
    
    # 3. Delete database entry
    if dataset:
        try:
            session.delete(dataset)
            session.commit()
            success_count += 1
            logger.info(f"Deleted database entry for: {dataset_id}")
        except Exception as e:
            errors.append(f"Database deletion error: {str(e)}")
            logger.warning(f"Failed to delete database entry for {dataset_id}: {e}")
            # Try to rollback
            try:
                session.rollback()
            except:
                pass
    else:
        logger.info(f"Dataset not found in database: {dataset_id}")
    
    # 4. Clean up processing status (always succeeds)
    try:
        if dataset_id in processing_status:
            del processing_status[dataset_id]
            success_count += 1
            logger.info(f"Cleared processing status for: {dataset_id}")
    except Exception as e:
        errors.append(f"Status cleanup error: {str(e)}")
        logger.warning(f"Failed to clear processing status for {dataset_id}: {e}")
    
    # Determine response
    if not dataset_existed and success_count == 0:
        # Nothing was found at all
        raise HTTPException(
            status_code=404, 
            detail="Dataset not found - no files or database entry exists"
        )
    
    # Build response
    response = {
        "message": "Dataset deleted successfully" if not errors else "Dataset partially deleted",
        "datasetId": dataset_id,
        "deleted": {
            "database": dataset_existed,
            "filesRemoved": success_count,
        }
    }
    
    if errors:
        response["warnings"] = errors
        logger.warning(f"Dataset {dataset_id} deleted with errors: {errors}")
    
    return response


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

