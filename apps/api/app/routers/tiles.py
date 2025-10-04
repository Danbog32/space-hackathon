"""Tiles router - serves DZI tiles and metadata."""

import math
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import TILE_BASE

router = APIRouter()


DZI_NS = "{http://schemas.microsoft.com/deepzoom/2008}"


@lru_cache(maxsize=32)
def _dataset_level_metadata(dataset_id: str) -> Tuple[Path, Dict[int, Dict[str, int]], int, int, int]:
    """Return dataset path, level bounds, max available level, and expected DZI max level."""

    dataset_path = Path(TILE_BASE) / dataset_id

    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset tiles not found")

    level_bounds: Dict[int, Dict[str, int]] = {}
    available_levels = []

    for item in dataset_path.iterdir():
        if not item.is_dir():
            continue
        try:
            level_index = int(item.name)
        except ValueError:
            continue

        max_col = -1
        max_row = -1
        for tile in item.glob("*_*"):
            name = tile.stem
            if "_" not in name:
                continue
            try:
                col_str, row_str = name.split("_", 1)
                col = int(col_str)
                row = int(row_str)
            except ValueError:
                continue
            max_col = max(max_col, col)
            max_row = max(max_row, row)

        if max_col >= 0 and max_row >= 0:
            available_levels.append(level_index)
            level_bounds[level_index] = {"max_col": max_col, "max_row": max_row}

    if not available_levels:
        raise HTTPException(status_code=404, detail="No tiles available for dataset")

    max_available_level = max(available_levels)

    dzi_max_level = max_available_level
    dzi_file = dataset_path / "info.dzi"
    if dzi_file.exists():
        try:
            tree = ET.parse(dzi_file)
            size_node = tree.find(f"{DZI_NS}Size")
            if size_node is not None:
                width = int(size_node.attrib.get("Width", "0"))
                height = int(size_node.attrib.get("Height", "0"))
                if width > 0 or height > 0:
                    dzi_max_level = math.ceil(math.log2(max(width, height)))
        except Exception:
            # Ignore parsing errors and fall back to available level
            pass

    min_available_level = min(available_levels)

    return (
        dataset_path,
        level_bounds,
        min_available_level,
        max_available_level,
        max(dzi_max_level, max_available_level),
    )


@router.get("/{dataset_id}/info.dzi")
async def get_dzi_info(dataset_id: str):
    """Serve DZI XML descriptor."""
    tile_path = Path(TILE_BASE) / dataset_id / "info.dzi"
    
    if not tile_path.exists():
        raise HTTPException(status_code=404, detail="DZI info not found")
    
    return FileResponse(
        tile_path,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=31536000"},
    )


def _resolve_tile(dataset_id: str, level: int, col: int, row: int, ext: str):
    """Return tile path and media type, remapping levels if necessary."""

    (
        dataset_path,
        level_bounds,
        min_available_level,
        max_available_level,
        dzi_max_level,
    ) = _dataset_level_metadata(dataset_id)

    candidate_path = dataset_path / str(level) / f"{col}_{row}.{ext}"
    if not candidate_path.exists():
        level_offset = max(dzi_max_level - max_available_level, 0)
        remapped_level = level - level_offset

        if remapped_level < min_available_level:
            remapped_level = min_available_level
        remapped_level = min(remapped_level, max_available_level)

        bounds = level_bounds.get(remapped_level)
        if not bounds:
            raise HTTPException(status_code=404, detail="Tile not found")

        remapped_col = min(max(col, 0), bounds["max_col"])
        remapped_row = min(max(row, 0), bounds["max_row"])

        candidate_path = dataset_path / str(remapped_level) / f"{remapped_col}_{remapped_row}.{ext}"

    if not candidate_path.exists():
        raise HTTPException(status_code=404, detail="Tile not found")

    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }

    return candidate_path, media_types.get(ext, "image/jpeg")


@router.get("/{dataset_id}/{level}/{col}_{row}.{ext}")
async def get_tile(dataset_id: str, level: int, col: int, row: int, ext: str):
    """Serve individual tile image."""
    tile_path, media_type = _resolve_tile(dataset_id, level, col, row, ext)

    return FileResponse(
        tile_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=31536000"},
    )


@router.get("/{dataset_id}/info_files/{level}/{col}_{row}.{ext}")
async def get_dzi_tile(dataset_id: str, level: int, col: int, row: int, ext: str):
    """Serve tiles following the Deep Zoom naming convention (<name>_files)."""
    tile_path, media_type = _resolve_tile(dataset_id, level, col, row, ext)

    return FileResponse(
        tile_path,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=31536000"},
    )


@router.get("/{dataset_id}/thumbnail.jpg")
async def get_thumbnail(dataset_id: str):
    """Serve dataset thumbnail (optional)."""
    # Try to serve level 0 tile as thumbnail
    tile_path = Path(TILE_BASE) / dataset_id / "0" / "0_0.jpg"
    
    if not tile_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        tile_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )
