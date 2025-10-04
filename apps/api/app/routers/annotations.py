"""Annotations router."""

import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from pydantic import BaseModel

from app.db import get_session
from app.models import Annotation
from app.auth import get_current_user

router = APIRouter()


class CreateAnnotationRequest(BaseModel):
    datasetId: str
    type: str  # point, rect, polygon
    geometry: dict
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = "#ff0000"
    metadata: Optional[dict] = None


class UpdateAnnotationRequest(BaseModel):
    geometry: Optional[dict] = None
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    metadata: Optional[dict] = None


class AnnotationResponse:
    """Annotation response model."""

    @staticmethod
    def from_db(annotation: Annotation) -> dict:
        return {
            "id": str(annotation.id),
            "datasetId": annotation.dataset_id,
            "userId": annotation.user_id,
            "type": annotation.type,
            "geometry": json.loads(annotation.geometry),
            "label": annotation.label,
            "description": annotation.description,
            "color": annotation.color,
            "metadata": (
                json.loads(annotation.metadata_)
                if isinstance(annotation.metadata_, str)
                else annotation.metadata_
            )
            if annotation.metadata_
            else None,
            "createdAt": annotation.created_at.isoformat(),
            "updatedAt": annotation.updated_at.isoformat(),
        }


@router.get("", response_model=List[dict])
async def list_annotations(
    datasetId: Optional[str] = Query(None),
    bbox: Optional[str] = Query(None),  # Format: "x,y,width,height"
    session: Session = Depends(get_session),
):
    """List annotations, optionally filtered by dataset and bounding box."""
    statement = select(Annotation)
    if datasetId:
        statement = statement.where(Annotation.dataset_id == datasetId)
    
    # TODO: Filter by bbox if provided (requires spatial index for efficiency)
    # For hackathon, we'll return all matching annotations
    
    annotations = session.exec(statement).all()
    return [AnnotationResponse.from_db(a) for a in annotations]


@router.post("", response_model=dict, status_code=201)
async def create_annotation(
    request: CreateAnnotationRequest,
    session: Session = Depends(get_session),
    user: Optional[dict] = Depends(get_current_user),
):
    """Create a new annotation."""
    # For demo, allow anonymous annotations
    annotation = Annotation(
        dataset_id=request.datasetId,
        user_id=user["username"] if user else "anonymous",
        type=request.type,
        geometry=json.dumps(request.geometry),
        label=request.label,
        description=request.description,
        color=request.color,
        metadata_=request.metadata,
    )
    session.add(annotation)
    session.commit()
    session.refresh(annotation)
    return AnnotationResponse.from_db(annotation)


@router.get("/{annotation_id}", response_model=dict)
async def get_annotation(annotation_id: int, session: Session = Depends(get_session)):
    """Get a specific annotation by ID."""
    annotation = session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return AnnotationResponse.from_db(annotation)


@router.put("/{annotation_id}", response_model=dict)
async def update_annotation(
    annotation_id: int,
    request: UpdateAnnotationRequest,
    session: Session = Depends(get_session),
    user: Optional[dict] = Depends(get_current_user),
):
    """Update an existing annotation."""
    annotation = session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    # Update fields if provided
    if request.geometry is not None:
        annotation.geometry = json.dumps(request.geometry)
    if request.label is not None:
        annotation.label = request.label
    if request.description is not None:
        annotation.description = request.description
    if request.color is not None:
        annotation.color = request.color
    if request.metadata is not None:
        annotation.metadata_ = request.metadata

    annotation.updated_at = datetime.now()
    session.add(annotation)
    session.commit()
    session.refresh(annotation)
    return AnnotationResponse.from_db(annotation)


@router.delete("/{annotation_id}", status_code=204)
async def delete_annotation(
    annotation_id: int,
    session: Session = Depends(get_session),
    user: Optional[dict] = Depends(get_current_user),
):
    """Delete an annotation."""
    annotation = session.get(Annotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    session.delete(annotation)
    session.commit()
    return None
