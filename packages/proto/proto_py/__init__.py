"""
Shared Python schemas mirroring TypeScript proto definitions.
Used by FastAPI services for request/response validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float


class Polygon(BaseModel):
    points: List[Point]


class Dataset(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    tileType: Literal["dzi", "tms", "iiif"] = "dzi"
    tileUrl: str
    levels: List[int]
    pixelSize: Tuple[int, int]
    metadata: Optional[Dict[str, Any]] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "andromeda",
                "name": "Andromeda Galaxy",
                "tileType": "dzi",
                "tileUrl": "/tiles/andromeda",
                "levels": [0, 1, 2, 3],
                "pixelSize": [4096, 4096],
            }
        }


class Feature(BaseModel):
    id: str
    datasetId: str
    name: str
    type: Literal["point", "bbox", "polygon"]
    geometry: Union[Point, BBox, Polygon]
    properties: Optional[Dict[str, Any]] = None
    createdAt: Optional[datetime] = None


class Annotation(BaseModel):
    id: str
    datasetId: str
    userId: Optional[str] = None
    type: Literal["point", "rect", "polygon"]
    geometry: Union[Point, BBox, Polygon]
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class CreateAnnotation(BaseModel):
    datasetId: str
    type: Literal["point", "rect", "polygon"]
    geometry: Union[Point, BBox, Polygon]
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = "#ff0000"
    metadata: Optional[Dict[str, Any]] = None


class UpdateAnnotation(BaseModel):
    geometry: Optional[Union[Point, BBox, Polygon]] = None
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchResult(BaseModel):
    bbox: BBox
    score: float
    preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    datasetId: str
    results: List[SearchResult]
    total: int


class Login(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    accessToken: str = Field(..., alias="access_token")
    tokenType: str = "bearer"

    class Config:
        populate_by_name = True


class Health(BaseModel):
    status: Literal["ok", "degraded", "down"]
    version: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

