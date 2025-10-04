#!/usr/bin/env python3
"""
Universal Cloud Optimized GeoTIFF (COG) Converter

Converts various image formats (.IMG, .TIF, .JPG, .PNG, etc.) to COG format
with automatic format detection, metadata preservation, and optimization.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import argparse
import json
import logging

# Core libraries
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_bounds
import numpy as np
from PIL import Image
import numpy as np

# COG-specific libraries
try:
    from rio_cogeo.cogeo import cog_translate
    from rio_cogeo.profiles import cog_profiles
    COG_AVAILABLE = True
except ImportError:
    COG_AVAILABLE = False
    print("Warning: rio-cogeo not available. Install with: pip install rio-cogeo")

# Planetary image support
try:
    import planetaryimage
    PLANETARY_AVAILABLE = True
except ImportError:
    PLANETARY_AVAILABLE = False
    print("Warning: planetaryimage not available. Install with: pip install planetaryimage")

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UniversalCOGConverter:
    """Universal converter for various image formats to COG."""
    
    # Supported input formats
    SUPPORTED_FORMATS = {
        '.img': 'PDS/Planetary Data System',
        '.tif': 'GeoTIFF',
        '.tiff': 'GeoTIFF', 
        '.jpg': 'JPEG',
        '.jpeg': 'JPEG',
        '.png': 'PNG',
        '.bmp': 'Bitmap',
        '.gif': 'GIF',
        '.webp': 'WebP'
    }
    
    def __init__(self, output_dir: str = "infra/cogs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def detect_format(self, file_path: str) -> Tuple[str, str]:
        """Detect file format and return extension and description."""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext in self.SUPPORTED_FORMATS:
            return ext, self.SUPPORTED_FORMATS[ext]
        else:
            raise ValueError(f"Unsupported format: {ext}")
    
    def get_image_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive image information."""
        try:
            with rasterio.open(file_path) as src:
                info = {
                    'file_path': str(file_path),
                    'format': src.driver,
                    'dimensions': (src.width, src.height),
                    'bands': src.count,
                    'data_type': str(src.dtypes[0]),
                    'crs': str(src.crs) if src.crs else None,
                    'bounds': src.bounds,
                    'transform': src.transform,
                    'nodata': src.nodata,
                    'color_interp': [src.colorinterp[i].name for i in range(src.count)],
                    'overviews': src.overviews(1) if src.count > 0 else [],
                    'profile': dict(src.profile)
                }
                
                # Add metadata
                if src.tags():
                    info['metadata'] = dict(src.tags())
                
                return info
                
        except Exception as e:
            logger.error(f"Error reading image info: {e}")
            return {'error': str(e)}
    
    def normalize_image_data(self, data: np.ndarray, src_dtype: str) -> np.ndarray:
        """Normalize image data to uint8 for display."""
        if src_dtype == 'uint8':
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
    
    def create_cog_profile(self, src_profile: Dict[str, Any], compression: str = 'lzw') -> Dict[str, Any]:
        """Create optimized COG profile from source profile."""
        profile = src_profile.copy()
        
        # COG-specific settings
        profile.update({
            'driver': 'GTiff',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'compress': compression,
            'interleave': 'pixel',
            'bigtiff': 'yes' if src_profile.get('width', 0) * src_profile.get('height', 0) > 2**31 else 'no'
        })
        
        return profile
    
    def convert_with_rio_cogeo(self, input_path: str, output_path: str, 
                              compression: str = 'deflate') -> bool:
        """Convert using rio-cogeo (preferred method)."""
        if not COG_AVAILABLE:
            return False
            
        try:
            profile = cog_profiles.get(compression)
            
            cog_translate(
                input_path,
                output_path,
                profile,
                in_memory=False,
                allow_intermediate_compression=True,
                overview_resampling="average",
                overview_levels=[2, 4, 8, 16, 32],
                add_overview_levels=True
            )
            
            logger.info(f"✓ Converted with rio-cogeo: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"rio-cogeo conversion failed: {e}")
            return False
    
    def convert_with_rasterio(self, input_path: str, output_path: str,
                             compression: str = 'lzw') -> bool:
        """Convert using rasterio (fallback method)."""
        try:
            with rasterio.open(input_path) as src:
                # Create COG profile
                profile = self.create_cog_profile(src.profile, compression)
                
                # Write COG
                with rasterio.open(output_path, 'w', **profile) as dst:
                    # Copy all bands
                    for i in range(1, src.count + 1):
                        logger.info(f"  - Copying band {i}...")
                        dst.write(src.read(i), i)
                    
                    # Build overviews
                    logger.info(f"  - Building overviews...")
                    dst.build_overviews([2, 4, 8, 16], rasterio.enums.Resampling.average)
                
                logger.info(f"✓ Converted with rasterio: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"rasterio conversion failed: {e}")
            return False
    
    def convert_image(self, input_path: str, output_path: Optional[str] = None,
                     compression: str = 'lzw', preserve_metadata: bool = True) -> Dict[str, Any]:
        """Convert image to COG format."""
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Detect format
        ext, format_desc = self.detect_format(str(input_path))
        logger.info(f"Converting {format_desc} file: {input_path}")
        
        # Generate output path if not provided
        if output_path is None:
            output_path = self.output_dir / f"{input_path.stem}.cog.tif"
        else:
            output_path = Path(output_path)
        
        # Get image info
        info = self.get_image_info(str(input_path))
        if 'error' in info:
            raise ValueError(f"Failed to read image: {info['error']}")
        
        logger.info(f"Image info: {info['dimensions'][0]}x{info['dimensions'][1]}, "
                   f"{info['bands']} bands, {info['data_type']}")
        
        # Try rio-cogeo first, fall back to rasterio
        success = False
        
        if COG_AVAILABLE:
            success = self.convert_with_rio_cogeo(str(input_path), str(output_path), compression)
        
        if not success:
            logger.info("Falling back to rasterio conversion...")
            success = self.convert_with_rasterio(str(input_path), str(output_path), compression)
        
        if not success:
            raise RuntimeError("All conversion methods failed")
        
        # Verify COG
        verification = self.verify_cog(str(output_path))
        
        # Return conversion results
        result = {
            'input_path': str(input_path),
            'output_path': str(output_path),
            'format': format_desc,
            'success': success,
            'verification': verification,
            'original_info': info
        }
        
        return result
    
    def verify_cog(self, cog_path: str) -> Dict[str, Any]:
        """Verify COG was created correctly."""
        try:
            with rasterio.open(cog_path) as src:
                verification = {
                    'valid': True,
                    'dimensions': (src.width, src.height),
                    'bands': src.count,
                    'data_type': str(src.dtypes[0]),
                    'crs': str(src.crs) if src.crs else None,
                    'tiled': src.profile.get('tiled', False),
                    'compressed': src.profile.get('compress') is not None,
                    'overviews': src.overviews(1) if src.count > 0 else [],
                    'block_size': (src.profile.get('blockxsize', 0), 
                                 src.profile.get('blockysize', 0)),
                    'file_size_mb': Path(cog_path).stat().st_size / (1024 * 1024)
                }
                
                logger.info(f"✓ COG verified: {verification['dimensions'][0]}x{verification['dimensions'][1]}, "
                           f"{verification['file_size_mb']:.1f} MB")
                
                return verification
                
        except Exception as e:
            logger.error(f"COG verification failed: {e}")
            return {'valid': False, 'error': str(e)}
    
    def batch_convert(self, input_dir: str, pattern: str = "*", 
                     compression: str = 'lzw') -> List[Dict[str, Any]]:
        """Batch convert multiple files."""
        
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all supported files
        files = []
        for ext in self.SUPPORTED_FORMATS.keys():
            files.extend(input_path.glob(f"{pattern}{ext}"))
            files.extend(input_path.glob(f"{pattern}{ext.upper()}"))
        
        logger.info(f"Found {len(files)} files to convert")
        
        results = []
        for file_path in files:
            try:
                logger.info(f"Converting {file_path.name}...")
                result = self.convert_image(str(file_path), compression=compression)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to convert {file_path}: {e}")
                results.append({
                    'input_path': str(file_path),
                    'success': False,
                    'error': str(e)
                })
        
        return results
    
    def generate_conversion_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate a conversion report."""
        
        successful = [r for r in results if r.get('success', False)]
        failed = [r for r in results if not r.get('success', False)]
        
        report = f"""
# COG Conversion Report

## Summary
- Total files: {len(results)}
- Successful: {len(successful)}
- Failed: {len(failed)}

## Successful Conversions
"""
        
        for result in successful:
            verification = result.get('verification', {})
            report += f"- {Path(result['input_path']).name} → {Path(result['output_path']).name}\n"
            report += f"  - Size: {verification.get('dimensions', 'Unknown')}\n"
            report += f"  - File size: {verification.get('file_size_mb', 0):.1f} MB\n"
            report += f"  - Overviews: {len(verification.get('overviews', []))}\n"
        
        if failed:
            report += "\n## Failed Conversions\n"
            for result in failed:
                report += f"- {Path(result['input_path']).name}: {result.get('error', 'Unknown error')}\n"
        
        return report


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(description='Universal COG Converter')
    parser.add_argument('input', help='Input file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('-c', '--compression', default='lzw', 
                       choices=['lzw', 'deflate', 'jpeg', 'webp'],
                       help='Compression method')
    parser.add_argument('-b', '--batch', action='store_true',
                       help='Batch convert directory')
    parser.add_argument('-p', '--pattern', default='*',
                       help='File pattern for batch conversion')
    parser.add_argument('--report', action='store_true',
                       help='Generate conversion report')
    
    args = parser.parse_args()
    
    converter = UniversalCOGConverter()
    
    try:
        if args.batch or Path(args.input).is_dir():
            # Batch conversion
            results = converter.batch_convert(args.input, args.pattern, args.compression)
            
            if args.report:
                report = converter.generate_conversion_report(results)
                report_path = converter.output_dir / "conversion_report.md"
                with open(report_path, 'w') as f:
                    f.write(report)
                logger.info(f"Report saved to: {report_path}")
            
        else:
            # Single file conversion
            result = converter.convert_image(args.input, args.output, args.compression)
            
            if result['success']:
                logger.info(f"✓ Conversion successful: {result['output_path']}")
            else:
                logger.error("Conversion failed")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
