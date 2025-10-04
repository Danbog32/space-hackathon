"""Features router."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db import get_session
from app.models import Feature

router = APIRouter()


class FeatureResponse:
    """Feature response model."""

    @staticmethod
    def from_db(feature: Feature) -> dict:
        return {
            "id": str(feature.id),
            "datasetId": feature.dataset_id,
            "name": feature.name,
            "type": feature.type,
            "geometry": json.loads(feature.geometry),
            "properties": json.loads(feature.properties) if feature.properties else None,
            "createdAt": feature.created_at.isoformat(),
        }


@router.get("", response_model=List[dict])
async def list_features(
    datasetId: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    """List features, optionally filtered by dataset."""
    statement = select(Feature)
    if datasetId:
        statement = statement.where(Feature.dataset_id == datasetId)
    features = session.exec(statement).all()
    return [FeatureResponse.from_db(f) for f in features]


@router.get("/{feature_id}", response_model=dict)
async def get_feature(feature_id: int, session: Session = Depends(get_session)):
    """Get a specific feature by ID."""
    feature = session.get(Feature, feature_id)
    if not feature:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Feature not found")
    return FeatureResponse.from_db(feature)

