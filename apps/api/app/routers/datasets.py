"""Datasets router."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db import get_session
from app.models import Dataset

router = APIRouter()


class DatasetResponse:
    """Dataset response model."""

    @staticmethod
    def from_db(dataset: Dataset) -> dict:
        return {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "tileType": dataset.tile_type,
            "tileUrl": dataset.tile_url,
            "levels": json.loads(dataset.levels),
            "pixelSize": json.loads(dataset.pixel_size),
            "metadata": (
                json.loads(dataset.metadata_)
                if isinstance(dataset.metadata_, str)
                else dataset.metadata_
            )
            if dataset.metadata_
            else None,
            "createdAt": dataset.created_at.isoformat(),
            "updatedAt": dataset.updated_at.isoformat(),
        }


@router.get("", response_model=List[dict])
async def list_datasets(session: Session = Depends(get_session)):
    """List all available datasets."""
    statement = select(Dataset)
    datasets = session.exec(statement).all()
    return [DatasetResponse.from_db(ds) for ds in datasets]


@router.get("/{dataset_id}", response_model=dict)
async def get_dataset(dataset_id: str, session: Session = Depends(get_session)):
    """Get a specific dataset by ID."""
    dataset = session.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse.from_db(dataset)
