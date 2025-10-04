"""
Tile processing utilities for generating Deep Zoom Image pyramids.

This module provides functionality to process uploaded images and generate
optimized tile pyramids for the OpenSeadragon viewer.
"""

import json
import math
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple, Optional
from xml.dom import minidom

from PIL import Image

# Disable PIL's decompression bomb protection for very large images
Image.MAX_IMAGE_PIXELS = None


class TileProcessorConfig:
    """Configuration for tile processing."""
    
    TILE_SIZE: int = 256
    TILE_OVERLAP: int = 1
    TILE_FORMAT: str = "jpg"
    TILE_QUALITY: int = 90
    MAX_FILE_SIZE_MB: int = 1500  # Maximum upload size
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}


class TileProcessingError(Exception):
    """Custom exception for tile processing errors."""
    pass


class TileProcessor:
    """Handles image tile generation for Deep Zoom Images."""
    
    def __init__(
        self,
        tiles_base_dir: Path,
        tile_size: int = TileProcessorConfig.TILE_SIZE,
        tile_overlap: int = TileProcessorConfig.TILE_OVERLAP,
        tile_quality: int = TileProcessorConfig.TILE_QUALITY,
    ):
        """
        Initialize the tile processor.
        
        Args:
            tiles_base_dir: Base directory for storing tiles
            tile_size: Size of each tile in pixels (default: 256)
            tile_overlap: Overlap between tiles in pixels (default: 1)
            tile_quality: JPEG quality 0-100 (default: 85)
        """
        self.tiles_base_dir = Path(tiles_base_dir)
        self.tile_size = tile_size
        self.tile_overlap = tile_overlap
        self.tile_quality = tile_quality
        self.tile_format = TileProcessorConfig.TILE_FORMAT
    
    @staticmethod
    def validate_image(image_path: Path) -> Tuple[int, int]:
        """
        Validate image and get its dimensions.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (width, height)
            
        Raises:
            TileProcessingError: If image is invalid
        """
        if not image_path.exists():
            raise TileProcessingError(f"Image file not found: {image_path}")
        
        # Check file extension
        if image_path.suffix.lower() not in TileProcessorConfig.ALLOWED_EXTENSIONS:
            raise TileProcessingError(
                f"Unsupported file type: {image_path.suffix}. "
                f"Allowed: {', '.join(TileProcessorConfig.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_size_mb = image_path.stat().st_size / (1024 * 1024)
        if file_size_mb > TileProcessorConfig.MAX_FILE_SIZE_MB:
            raise TileProcessingError(
                f"File too large: {file_size_mb:.1f}MB. "
                f"Maximum allowed: {TileProcessorConfig.MAX_FILE_SIZE_MB}MB"
            )
        
        # Try to open and get dimensions
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Basic sanity checks
                if width < 256 or height < 256:
                    raise TileProcessingError(
                        f"Image too small: {width}x{height}. Minimum: 256x256"
                    )
                
                return width, height
        except Exception as e:
            raise TileProcessingError(f"Failed to read image: {str(e)}")
    
    @staticmethod
    def calculate_pyramid_levels(width: int, height: int, tile_size: int) -> int:
        """Calculate the number of zoom levels needed for the pyramid."""
        max_dimension = max(width, height)
        levels = math.ceil(math.log2(max_dimension / tile_size)) + 1
        return levels
    
    def create_dzi_xml(self, width: int, height: int) -> str:
        """
        Create DZI XML descriptor.
        
        Args:
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            Formatted XML string
        """
        image = ET.Element('Image', {
            'xmlns': 'http://schemas.microsoft.com/deepzoom/2008',
            'Format': self.tile_format,
            'Overlap': str(self.tile_overlap),
            'TileSize': str(self.tile_size)
        })
        
        ET.SubElement(image, 'Size', {
            'Width': str(width),
            'Height': str(height)
        })
        
        # Pretty print
        xml_str = ET.tostring(image, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent='  ')
    
    def generate_tiles(
        self,
        image_path: Path,
        dataset_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict:
        """
        Generate optimized tile pyramid from source image.
        
        Args:
            image_path: Path to source image
            dataset_id: Unique identifier for this dataset
            progress_callback: Optional callback function for progress updates
                              Signature: callback(current, total, message)
        
        Returns:
            Dictionary with processing results including:
            - dataset_id: The dataset identifier
            - width: Image width
            - height: Image height
            - levels: Number of zoom levels
            - total_tiles: Total number of tiles generated
            - output_dir: Path to tile directory
            
        Raises:
            TileProcessingError: If processing fails
        """
        try:
            # Validate image
            width, height = self.validate_image(image_path)
            
            # Calculate pyramid levels
            num_levels = self.calculate_pyramid_levels(width, height, self.tile_size)
            
            # Setup output directory
            output_dir = self.tiles_base_dir / dataset_id
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate DZI metadata
            dzi_xml = self.create_dzi_xml(width, height)
            dzi_path = output_dir / "info.dzi"
            with open(dzi_path, 'w') as f:
                f.write(dzi_xml)
            
            # Progress tracking
            total_tiles = sum(
                math.ceil((width // (2 ** (num_levels - 1 - level))) / self.tile_size) *
                math.ceil((height // (2 ** (num_levels - 1 - level))) / self.tile_size)
                for level in range(num_levels)
            )
            
            if progress_callback:
                progress_callback(0, total_tiles, "Starting tile generation...")
            
            # Generate tiles
            with Image.open(image_path) as img:
                current_img = img.copy()
                tiles_generated = 0
                
                for level in range(num_levels - 1, -1, -1):
                    level_dir = output_dir / str(level)
                    level_dir.mkdir(exist_ok=True)
                    
                    # Calculate dimensions for this level
                    scale = 2 ** (num_levels - 1 - level)
                    level_width = max(1, width // scale)
                    level_height = max(1, height // scale)
                    
                    # Resize image for this level if needed
                    if level < num_levels - 1:
                        current_img = current_img.resize(
                            (level_width, level_height),
                            Image.Resampling.LANCZOS
                        )
                    
                    # Calculate number of tiles for this level
                    cols = math.ceil(level_width / self.tile_size)
                    rows = math.ceil(level_height / self.tile_size)
                    
                    # Generate tiles for this level
                    for col in range(cols):
                        for row in range(rows):
                            # Calculate tile boundaries with overlap
                            x = col * self.tile_size
                            y = row * self.tile_size
                            x1 = max(0, x - self.tile_overlap)
                            y1 = max(0, y - self.tile_overlap)
                            x2 = min(level_width, x + self.tile_size + self.tile_overlap)
                            y2 = min(level_height, y + self.tile_size + self.tile_overlap)
                            
                            # Extract and save tile
                            tile = current_img.crop((x1, y1, x2, y2))
                            tile_path = level_dir / f"{col}_{row}.{self.tile_format}"
                            tile.save(
                                tile_path,
                                format='JPEG',
                                quality=self.tile_quality,
                                optimize=True,
                                progressive=True
                            )
                            
                            tiles_generated += 1
                            
                            # Update progress
                            if progress_callback and tiles_generated % 10 == 0:
                                progress_callback(
                                    tiles_generated,
                                    total_tiles,
                                    f"Level {level}: {tiles_generated}/{total_tiles} tiles"
                                )
            
            if progress_callback:
                progress_callback(total_tiles, total_tiles, "Complete!")
            
            return {
                "dataset_id": dataset_id,
                "width": width,
                "height": height,
                "levels": num_levels,
                "total_tiles": tiles_generated,
                "output_dir": str(output_dir),
                "tile_url": f"/tiles/{dataset_id}",
            }
            
        except TileProcessingError:
            raise
        except Exception as e:
            raise TileProcessingError(f"Tile generation failed: {str(e)}")
    
    def get_processing_status(self, dataset_id: str) -> Optional[Dict]:
        """
        Get processing status for a dataset.
        
        Args:
            dataset_id: Dataset identifier
            
        Returns:
            Dictionary with status information or None if not found
        """
        output_dir = self.tiles_base_dir / dataset_id
        
        if not output_dir.exists():
            return None
        
        dzi_path = output_dir / "info.dzi"
        if not dzi_path.exists():
            return {"status": "processing", "progress": 0}
        
        # Count generated tiles
        tile_count = sum(1 for _ in output_dir.rglob(f"*.{self.tile_format}"))
        
        return {
            "status": "complete",
            "tile_count": tile_count,
            "output_dir": str(output_dir),
        }

