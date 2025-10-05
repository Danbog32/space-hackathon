"""Overlay management router."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import DATA_DIR, TILES_DIR
from app.db import engine, get_session
from app.models import Dataset, Overlay
from app.tile_processor import TileProcessor, TileProcessingError

router = APIRouter()

# Directories
OVERLAY_UPLOAD_DIR = DATA_DIR / "overlays"
OVERLAY_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Tile processor reuse
overlay_tile_processor = TileProcessor(tiles_base_dir=TILES_DIR)

# Simple in-memory processing status tracking
overlay_processing_status: Dict[str, Dict[str, Any]] = {}


class OverlayResponse:
    """Helper to serialize overlay responses."""

    @staticmethod
    def from_db(overlay: Overlay) -> dict:
        metadata = overlay.metadata_
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except json.JSONDecodeError:
                metadata = {"raw": metadata}
        return {
            "id": overlay.id,
            "datasetId": overlay.dataset_id,
            "name": overlay.name,
            "tileUrl": overlay.tile_url,
            "opacity": overlay.opacity,
            "visible": overlay.visible,
            "position": {
                "x": overlay.position_x,
                "y": overlay.position_y,
                "width": overlay.width,
                "rotation": overlay.rotation,
            },
            "metadata": metadata,
            "sourceDatasetId": metadata.get("sourceDatasetId"),
            "createdAt": overlay.created_at.isoformat(),
            "updatedAt": overlay.updated_at.isoformat(),
        }


class OverlayPosition(BaseModel):
    x: float
    y: float
    width: float
    rotation: float = 0.0


class OverlayUpdateRequest(BaseModel):
    name: Optional[str] = None
    opacity: Optional[float] = None
    visible: Optional[bool] = None
    position: Optional[OverlayPosition] = None
    metadata: Optional[Dict[str, Any]] = None


class OverlayFromDatasetRequest(BaseModel):
    datasetId: str
    sourceDatasetId: str
    name: Optional[str] = None
    opacity: float = 1.0
    visible: bool = True
    position: OverlayPosition = OverlayPosition(x=0.0, y=0.0, width=1.0, rotation=0.0)
    metadata: Optional[Dict[str, Any]] = None


def _normalize_metadata(value: Optional[Any]) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}


def _extract_dataset_overlay_metadata(dataset: Dataset) -> Dict[str, Any]:
    metadata = _normalize_metadata(dataset.metadata_)
    try:
        levels = json.loads(dataset.levels)
        if isinstance(levels, list):
            metadata.setdefault("levels", levels)
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    try:
        pixel_size = json.loads(dataset.pixel_size)
        if (
            isinstance(pixel_size, (list, tuple))
            and len(pixel_size) == 2
            and all(isinstance(v, (int, float)) for v in pixel_size)
        ):
            metadata.setdefault("width", pixel_size[0])
            metadata.setdefault("height", pixel_size[1])
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    metadata.setdefault("sourceDatasetName", dataset.name)
    metadata.setdefault("sourceTileUrl", dataset.tile_url)
    return metadata


def process_overlay_background(
    overlay_id: str,
    dataset_id: str,
    file_path: Path,
    name: str,
    opacity: float,
    visible: bool,
    position: OverlayPosition,
    metadata: Optional[Dict[str, Any]] = None,
    cleanup_upload: bool = True,
):
    """Generate tiles for the overlay image and persist metadata."""

    overlay_processing_status[overlay_id] = {
        "status": "processing",
        "progress": 0,
        "message": "Starting overlay tile generation...",
    }

    tile_identifier = f"overlay-{overlay_id}"

    def progress_callback(current: int, total: int, message: str) -> None:
        progress = int((current / total) * 100) if total else 0
        overlay_processing_status[overlay_id] = {
            "status": "processing",
            "progress": progress,
            "message": message,
        }

    try:
        result = overlay_tile_processor.generate_tiles(
            image_path=file_path,
            dataset_id=tile_identifier,
            progress_callback=progress_callback,
        )

        with Session(engine) as session:
            dataset = session.get(Dataset, dataset_id)
            if not dataset:
                overlay_processing_status[overlay_id] = {
                    "status": "error",
                    "progress": 0,
                    "message": "Dataset not found while saving overlay",
                }
                return

            overlay = Overlay(
                id=overlay_id,
                dataset_id=dataset_id,
                name=name,
                tile_url=f"/tiles/{tile_identifier}",
                opacity=opacity,
                visible=visible,
                position_x=position.x,
                position_y=position.y,
                width=position.width,
                rotation=position.rotation,
                metadata_=metadata
                if metadata is None
                else json.loads(json.dumps(metadata)),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            # Augment metadata with intrinsic image dimensions
            extra_metadata = {
                "width": result["width"],
                "height": result["height"],
                "levels": result["levels"],
                "totalTiles": result["total_tiles"],
            }
            if overlay.metadata_:
                overlay.metadata_.update(extra_metadata)
            else:
                overlay.metadata_ = extra_metadata

            session.add(overlay)
            session.commit()

        overlay_processing_status[overlay_id] = {
            "status": "complete",
            "progress": 100,
            "message": "Overlay processing complete",
            "result": {
                "tileId": tile_identifier,
                "width": result["width"],
                "height": result["height"],
            },
        }
    except TileProcessingError as exc:
        overlay_processing_status[overlay_id] = {
            "status": "error",
            "progress": 0,
            "message": str(exc),
        }
    except Exception as exc:  # pragma: no cover - defensive logging path
        overlay_processing_status[overlay_id] = {
            "status": "error",
            "progress": 0,
            "message": f"Unexpected error: {exc}",
        }
    finally:
        if cleanup_upload and file_path.exists():
            try:
                file_path.unlink()
            except OSError:
                pass


@router.get("", response_model=list)
async def list_overlays(
    datasetId: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """List overlays, optionally filtered by dataset."""
    statement = select(Overlay)
    if datasetId:
        statement = statement.where(Overlay.dataset_id == datasetId)
    overlays = session.exec(statement.order_by(Overlay.created_at.desc())).all()
    return [OverlayResponse.from_db(overlay) for overlay in overlays]


@router.get("/{overlay_id}", response_model=dict)
async def get_overlay(overlay_id: str, session: Session = Depends(get_session)):
    overlay = session.get(Overlay, overlay_id)
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")
    return OverlayResponse.from_db(overlay)


@router.post("", response_model=dict, status_code=202)
async def create_overlay(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Overlay image"),
    dataset_id: str = Form(..., description="Dataset identifier"),
    name: str = Form(..., description="Overlay name"),
    opacity: float = Form(1.0, ge=0.0, le=1.0),
    visible: bool = Form(True),
    position_x: float = Form(0.0),
    position_y: float = Form(0.0),
    width: float = Form(1.0),
    rotation: float = Form(0.0),
    metadata: Optional[str] = Form(None, description="Optional JSON metadata"),
):
    """Upload a new overlay image and start background tiling."""

    overlay_id = str(uuid4())
    dataset_id = dataset_id.strip()

    # Ensure dataset exists before accepting upload
    with Session(engine) as session:
        dataset = session.get(Dataset, dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Overlay file must be an image")

    upload_path = OVERLAY_UPLOAD_DIR / f"{overlay_id}{Path(file.filename or '').suffix or '.bin'}"
    with upload_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        parsed_metadata: Optional[Dict[str, Any]] = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")

    position = OverlayPosition(x=position_x, y=position_y, width=width, rotation=rotation)

    background_tasks.add_task(
        process_overlay_background,
        overlay_id=overlay_id,
        dataset_id=dataset_id,
        file_path=upload_path,
        name=name,
        opacity=opacity,
        visible=visible,
        position=position,
        metadata=parsed_metadata,
    )

    overlay_processing_status[overlay_id] = {
        "status": "queued",
        "progress": 0,
        "message": "Overlay upload received",
    }

    return {
        "overlayId": overlay_id,
        "status": "queued",
        "message": "Overlay upload accepted",
        "statusUrl": f"/overlays/status/{overlay_id}",
    }


@router.post("/from-dataset", response_model=dict, status_code=201)
async def create_overlay_from_dataset(
    payload: OverlayFromDatasetRequest,
    session: Session = Depends(get_session),
):
    dataset_id = payload.datasetId.strip()
    source_dataset_id = payload.sourceDatasetId.strip()

    if not dataset_id or not source_dataset_id:
        raise HTTPException(status_code=400, detail="datasetId and sourceDatasetId are required")

    if payload.position.width <= 0:
        raise HTTPException(status_code=400, detail="Position width must be greater than 0")

    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Target dataset not found")

    source_dataset = session.get(Dataset, source_dataset_id)
    if not source_dataset:
        raise HTTPException(status_code=404, detail="Source dataset not found")

    overlay_id = str(uuid4())

    metadata = _normalize_metadata(payload.metadata)
    metadata.update(_extract_dataset_overlay_metadata(source_dataset))
    metadata["sourceDatasetId"] = source_dataset_id

    overlay = Overlay(
        id=overlay_id,
        dataset_id=dataset_id,
        name=payload.name.strip() if payload.name else source_dataset.name,
        tile_url=source_dataset.tile_url,
        opacity=payload.opacity,
        visible=payload.visible,
        position_x=payload.position.x,
        position_y=payload.position.y,
        width=payload.position.width,
        rotation=payload.position.rotation,
        metadata_=metadata,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    session.add(overlay)
    session.commit()
    session.refresh(overlay)

    overlay_processing_status[overlay_id] = {
        "status": "complete",
        "progress": 100,
        "message": "Overlay linked to existing dataset",
    }

    return OverlayResponse.from_db(overlay)


@router.get("/status/{overlay_id}", response_model=dict)
async def get_overlay_status(overlay_id: str):
    status = overlay_processing_status.get(overlay_id)
    if not status:
        raise HTTPException(status_code=404, detail="Overlay status not found")
    return {"overlayId": overlay_id, **status}


@router.patch("/{overlay_id}", response_model=dict)
async def update_overlay(
    overlay_id: str,
    data: OverlayUpdateRequest,
    session: Session = Depends(get_session),
):
    overlay = session.get(Overlay, overlay_id)
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    if data.name is not None:
        overlay.name = data.name
    if data.opacity is not None:
        if not 0 <= data.opacity <= 1:
            raise HTTPException(status_code=400, detail="Opacity must be between 0 and 1")
        overlay.opacity = data.opacity
    if data.visible is not None:
        overlay.visible = data.visible
    if data.position is not None:
        overlay.position_x = data.position.x
        overlay.position_y = data.position.y
        overlay.width = data.position.width
        overlay.rotation = data.position.rotation
    if data.metadata is not None:
        overlay.metadata_ = data.metadata

    overlay.updated_at = datetime.now()

    session.add(overlay)
    session.commit()
    session.refresh(overlay)

    return OverlayResponse.from_db(overlay)


@router.delete("/{overlay_id}", status_code=204)
async def delete_overlay(overlay_id: str, session: Session = Depends(get_session)):
    overlay = session.get(Overlay, overlay_id)
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    tile_identifier = overlay.tile_url.split("/tiles/")[-1]
    metadata = _normalize_metadata(overlay.metadata_)
    if metadata.get("sourceDatasetId") is None and tile_identifier.startswith("overlay-"):
        tile_dir = TILES_DIR / tile_identifier
        if tile_dir.exists():
            shutil.rmtree(tile_dir, ignore_errors=True)

    session.delete(overlay)
    session.commit()

    overlay_processing_status.pop(overlay_id, None)

    return None
