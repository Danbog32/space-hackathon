"""Tiles router - serves DZI tiles and metadata."""

import math
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple, Optional
import io
import numpy as np

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response

from app.config import TILE_BASE

# COG support imports
try:
    import rasterio
    from rasterio.windows import Window
    from PIL import Image
    COG_AVAILABLE = True
except ImportError:
    COG_AVAILABLE = False

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


def normalize_to_uint8(data: np.ndarray) -> np.ndarray:
    """Normalize data to 0-255 range for display."""
    if data.dtype == np.uint8:
        return data
    
    # Handle different data types
    if data.dtype in [np.float32, np.float64]:
        # Float data - normalize to 0-1 then scale to 0-255
        data_min = np.nanmin(data)
        data_max = np.nanmax(data)
        
        if data_max > data_min:
            normalized = ((data - data_min) / (data_max - data_min) * 255).astype(np.uint8)
        else:
            normalized = np.zeros_like(data, dtype=np.uint8)
    else:
        # Integer data - scale appropriately
        data_min = np.min(data)
        data_max = np.max(data)
        
        if data_max > 255:
            # Scale down
            normalized = ((data - data_min) / (data_max - data_min) * 255).astype(np.uint8)
        else:
            normalized = data.astype(np.uint8)
    
    return normalized


def get_cog_path(dataset_id: str) -> Optional[Path]:
    """Get COG file path for dataset."""
    cog_path = Path(TILE_BASE) / f"{dataset_id}.cog.tif"
    return cog_path if cog_path.exists() else None


def generate_dzi_from_cog(cog_path: Path) -> Response:
    """Generate DZI descriptor from COG metadata."""
    if not COG_AVAILABLE:
        raise HTTPException(status_code=500, detail="COG support not available")
    
    try:
        with rasterio.open(cog_path) as src:
            width, height = src.width, src.height
            
            dzi_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<Image xmlns="http://schemas.microsoft.com/deepzoom/2008"
       Format="jpg"
       Overlap="0"
       TileSize="256">
  <Size Width="{width}" Height="{height}"/>
</Image>'''
            
            return Response(
                content=dzi_content,
                media_type="application/xml",
                headers={"Cache-Control": "public, max-age=31536000"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading COG: {str(e)}")


@router.get("/{dataset_id}")
async def get_dataset_base(dataset_id: str):
    """Serve DZI info for base dataset path - OpenSeadragon compatibility."""
    return await get_dzi_info(dataset_id)


@router.get("/{dataset_id}/info.dzi")
async def get_dzi_info(dataset_id: str):
    """Serve DZI XML descriptor - supports both DZI and COG datasets."""
    
    # Check for COG first
    cog_path = get_cog_path(dataset_id)
    if cog_path:
        return generate_dzi_from_cog(cog_path)
    
    # Fall back to existing DZI
    tile_path = Path(TILE_BASE) / dataset_id / "info.dzi"
    
    if not tile_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found")
    
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


@router.get("/{dataset_id}/cog/{level}/{col}_{row}.{ext}")
async def get_cog_tile(dataset_id: str, level: int, col: int, row: int, ext: str):
    """Serve tiles from Cloud Optimized GeoTIFF."""
    
    if not COG_AVAILABLE:
        raise HTTPException(status_code=500, detail="COG support not available")
    
    cog_path = get_cog_path(dataset_id)
    if not cog_path:
        # Fall back to DZI tiles
        return await get_tile(dataset_id, level, col, row, ext, Request)
    
    try:
        with rasterio.open(cog_path) as src:
            # Calculate tile bounds based on level
            tile_size = 256
            scale_factor = 2 ** level
            
            col_off = col * tile_size * scale_factor
            row_off = row * tile_size * scale_factor
            width = tile_size * scale_factor
            height = tile_size * scale_factor
            
            # Define window
            window = Window(col_off, row_off, width, height)
            
            # Read region efficiently (this is the magic of COG!)
            if src.count == 1:
                # Grayscale
                data = src.read(1, window=window)
                # Convert to RGB for display
                rgb_data = np.stack([data, data, data], axis=2)
            elif src.count >= 3:
                # RGB or multispectral
                rgb_data = np.transpose(src.read([1, 2, 3], window=window), (1, 2, 0))
            else:
                raise ValueError(f"Unsupported band count: {src.count}")
            
            # Normalize data
            rgb_data = normalize_to_uint8(rgb_data)
            
            # Convert to image
            img = Image.fromarray(rgb_data)
            img = img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            
            # Return as response
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85)
            output.seek(0)
            
            return Response(
                content=output.getvalue(),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=31536000"}
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"COG processing error: {str(e)}")


@router.get("/{dataset_id}/{level}/{col}_{row}.{ext}")
@router.head("/{dataset_id}/{level}/{col}_{row}.{ext}")
async def get_tile(dataset_id: str, level: int, col: int, row: int, ext: str, request: Request):
    """
    Serve individual tile image.
    
    Optimizations:
    - Serves WebP to supporting browsers (25-35% smaller)
    - Long-term caching (tiles are immutable)
    - Efficient content negotiation
    - Falls back to COG if available
    """
    
    # Check for COG first
    cog_path = get_cog_path(dataset_id)
    if cog_path and COG_AVAILABLE:
        try:
            return await get_cog_tile(dataset_id, level, col, row, ext)
        except Exception:
            # Fall back to DZI tiles if COG fails
            pass
    
    # Serve DZI tiles
    tile_path, media_type = _resolve_tile(dataset_id, level, col, row, ext)
    
    # Check if browser supports WebP and we have a WebP version
    accept_header = request.headers.get("accept", "")
    if "image/webp" in accept_header and ext in ["jpg", "jpeg"]:
        webp_path = tile_path.with_suffix(".webp")
        if webp_path.exists():
            tile_path = webp_path
            media_type = "image/webp"
    
    headers = {
        "Cache-Control": "public, max-age=31536000, immutable",
        "Vary": "Accept",  # Cache varies by Accept header
    }

    # For HEAD requests, return just headers without body
    if request.method == "HEAD":
        return Response(
            status_code=200,
            headers={
                **headers,
                "Content-Type": media_type,
                "Content-Length": str(tile_path.stat().st_size),
            }
        )

    return FileResponse(
        tile_path,
        media_type=media_type,
        headers=headers,
    )


@router.get("/{dataset_id}/files/{level}/{col}_{row}.{ext}")
@router.head("/{dataset_id}/files/{level}/{col}_{row}.{ext}")
async def get_dzi_files_tile(dataset_id: str, level: int, col: int, row: int, ext: str, request: Request):
    """Serve tiles following the Deep Zoom naming convention (files)."""
    return await get_tile(dataset_id, level, col, row, ext, request)


@router.get("/{dataset_id}/info_files/{level}/{col}_{row}.{ext}")
async def get_dzi_tile(dataset_id: str, level: int, col: int, row: int, ext: str, request: Request):
    """
    Serve tiles following the Deep Zoom naming convention (<name>_files).
    
    Includes WebP content negotiation for modern browsers.
    """
    tile_path, media_type = _resolve_tile(dataset_id, level, col, row, ext)
    
    # Check if browser supports WebP and we have a WebP version
    accept_header = request.headers.get("accept", "")
    if "image/webp" in accept_header and ext in ["jpg", "jpeg"]:
        webp_path = tile_path.with_suffix(".webp")
        if webp_path.exists():
            tile_path = webp_path
            media_type = "image/webp"
    
    headers = {
        "Cache-Control": "public, max-age=31536000, immutable",
        "Vary": "Accept",
    }

    return FileResponse(
        tile_path,
        media_type=media_type,
        headers=headers,
        )


@router.get("/{dataset_id}/cog/validate")
async def validate_cog_dataset(dataset_id: str):
    """Validate COG file for dataset."""
    
    if not COG_AVAILABLE:
        raise HTTPException(status_code=500, detail="COG support not available")
    
    cog_path = get_cog_path(dataset_id)
    if not cog_path:
        raise HTTPException(status_code=404, detail="COG file not found")
    
    try:
        # Import COG validator
        import sys
        sys.path.append(str(Path(__file__).parent.parent.parent.parent / "infra"))
        from cog_validator import COGValidator
        
        validator = COGValidator()
        result = validator.validate_cog(str(cog_path))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.get("/{dataset_id}/thumbnail.jpg")
async def get_thumbnail(dataset_id: str):
    """Serve dataset thumbnail - supports both DZI and COG."""
    
    # Try COG first
    cog_path = get_cog_path(dataset_id)
    if cog_path and COG_AVAILABLE:
        try:
            # Generate thumbnail from COG
            return await get_cog_tile(dataset_id, 0, 0, 0, "jpg")
        except Exception:
            # Fall back to DZI thumbnail
            pass
    
    # Try to serve level 0 tile as thumbnail
    tile_path = Path(TILE_BASE) / dataset_id / "0" / "0_0.jpg"
    
    if not tile_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(
        tile_path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=3600"},
    )
