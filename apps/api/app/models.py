"""SQLModel database models."""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON


class Dataset(SQLModel, table=True):
    """Dataset model representing a tiled image collection."""

    id: str = Field(primary_key=True)
    name: str
    description: Optional[str] = None
    tile_type: str = Field(default="dzi")  # dzi, tms, iiif, cog
    tile_url: str
    levels: str  # JSON array stored as string
    pixel_size: str  # JSON tuple stored as string
    source_format: Optional[str] = Field(default=None)  # Original format (IMG, TIF, JPG, etc.)
    source_file: Optional[str] = Field(default=None)  # Path to source file
    cog_file: Optional[str] = Field(default=None)  # Path to COG file
    is_dynamic: bool = Field(default=False)  # Dynamic processing flag
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSON),
    )  # JSON metadata stored under `metadata` column
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Feature(SQLModel, table=True):
    """Feature model representing interesting regions in datasets."""

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: str = Field(foreign_key="dataset.id")
    name: str
    type: str  # point, bbox, polygon
    geometry: str = Field(sa_column=Column(JSON))  # JSON geometry
    properties: Optional[str] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.now)


class Annotation(SQLModel, table=True):
    """Annotation model for user-created markers and regions."""

    id: Optional[int] = Field(default=None, primary_key=True)
    dataset_id: str = Field(foreign_key="dataset.id")
    user_id: Optional[str] = None
    type: str  # point, rect, polygon
    geometry: str = Field(sa_column=Column(JSON))  # JSON geometry
    label: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = "#ff0000"
    metadata_: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
