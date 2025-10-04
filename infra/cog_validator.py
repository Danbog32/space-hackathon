#!/usr/bin/env python3
"""
COG Validation and Verification Utilities

Provides tools to validate Cloud Optimized GeoTIFF files and ensure
they meet COG specifications for optimal web serving.
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

try:
    import rasterio
    from rasterio.windows import Window
    RASTERIO_AVAILABLE = True
except ImportError:
    RASTERIO_AVAILABLE = False

logger = logging.getLogger(__name__)


class COGValidator:
    """Validates Cloud Optimized GeoTIFF files."""
    
    def __init__(self):
        self.validation_results = {}
    
    def validate_cog(self, cog_path: str) -> Dict[str, Any]:
        """Comprehensive COG validation."""
        
        if not RASTERIO_AVAILABLE:
            return {
                "valid": False,
                "error": "rasterio not available",
                "checks": {}
            }
        
        cog_path = Path(cog_path)
        if not cog_path.exists():
            return {
                "valid": False,
                "error": "File not found",
                "checks": {}
            }
        
        checks = {}
        
        try:
            with rasterio.open(cog_path) as src:
                # Basic file checks
                checks["file_exists"] = True
                checks["file_readable"] = True
                checks["file_size_mb"] = cog_path.stat().st_size / (1024 * 1024)
                
                # COG-specific checks
                checks["is_tiled"] = src.profile.get("tiled", False)
                checks["has_compression"] = src.profile.get("compress") is not None
                checks["compression_type"] = src.profile.get("compress")
                
                # Block size checks
                blockxsize = src.profile.get("blockxsize", 0)
                blockysize = src.profile.get("blockysize", 0)
                checks["block_size"] = [blockxsize, blockysize]
                checks["optimal_block_size"] = blockxsize == 512 and blockysize == 512
                
                # Overview checks
                overviews = src.overviews(1) if src.count > 0 else []
                checks["has_overviews"] = len(overviews) > 0
                checks["overview_count"] = len(overviews)
                checks["overview_levels"] = overviews
                
                # Data integrity checks
                checks["dimensions"] = [src.width, src.height]
                checks["band_count"] = src.count
                checks["data_type"] = str(src.dtypes[0])
                checks["has_crs"] = src.crs is not None
                checks["crs"] = str(src.crs) if src.crs else None
                
                # Performance checks
                checks["bigtiff"] = src.profile.get("bigtiff", "no") == "yes"
                checks["interleave"] = src.profile.get("interleave", "band")
                
                # Test tile reading performance
                performance_test = self._test_tile_reading(src)
                checks["tile_reading_test"] = performance_test
                
                # Overall validation
                checks["is_valid_cog"] = self._is_valid_cog(checks)
                
                return {
                    "valid": checks["is_valid_cog"],
                    "checks": checks,
                    "recommendations": self._get_recommendations(checks)
                }
                
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "checks": checks
            }
    
    def _test_tile_reading(self, src) -> Dict[str, Any]:
        """Test tile reading performance."""
        try:
            import time
            
            # Test reading a small region
            start_time = time.time()
            
            # Read a 256x256 region from the top-left
            window = Window(0, 0, 256, 256)
            data = src.read(1, window=window)
            
            read_time = time.time() - start_time
            
            return {
                "success": True,
                "read_time_ms": read_time * 1000,
                "data_shape": data.shape,
                "performance": "good" if read_time < 0.1 else "slow"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_valid_cog(self, checks: Dict[str, Any]) -> bool:
        """Determine if file is a valid COG."""
        required_checks = [
            "is_tiled",
            "has_compression", 
            "has_overviews"
        ]
        
        return all(checks.get(check, False) for check in required_checks)
    
    def _get_recommendations(self, checks: Dict[str, Any]) -> List[str]:
        """Get optimization recommendations."""
        recommendations = []
        
        if not checks.get("is_tiled", False):
            recommendations.append("File should be tiled for better performance")
        
        if not checks.get("has_compression", False):
            recommendations.append("Add compression to reduce file size")
        
        if not checks.get("has_overviews", False):
            recommendations.append("Add overviews for better zoom performance")
        
        if not checks.get("optimal_block_size", False):
            recommendations.append("Use 512x512 block size for optimal performance")
        
        if checks.get("tile_reading_test", {}).get("performance") == "slow":
            recommendations.append("Tile reading is slow - consider re-optimizing")
        
        if not checks.get("bigtiff", False) and checks.get("file_size_mb", 0) > 4000:
            recommendations.append("Consider using BigTIFF for large files")
        
        return recommendations
    
    def batch_validate(self, directory: str, pattern: str = "*.cog.tif") -> Dict[str, Any]:
        """Validate multiple COG files."""
        
        directory = Path(directory)
        if not directory.exists():
            return {"error": "Directory not found"}
        
        cog_files = list(directory.glob(pattern))
        
        results = {}
        for cog_file in cog_files:
            logger.info(f"Validating {cog_file.name}...")
            results[cog_file.name] = self.validate_cog(str(cog_file))
        
        # Summary
        total_files = len(cog_files)
        valid_files = sum(1 for r in results.values() if r.get("valid", False))
        
        summary = {
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": total_files - valid_files,
            "validation_rate": valid_files / total_files if total_files > 0 else 0
        }
        
        return {
            "summary": summary,
            "results": results
        }
    
    def generate_validation_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable validation report."""
        
        if "error" in validation_result:
            return f"Validation Error: {validation_result['error']}"
        
        checks = validation_result.get("checks", {})
        recommendations = validation_result.get("recommendations", [])
        
        report = f"""
# COG Validation Report

## File Information
- **File Size**: {checks.get('file_size_mb', 0):.1f} MB
- **Dimensions**: {checks.get('dimensions', 'Unknown')}
- **Bands**: {checks.get('band_count', 'Unknown')}
- **Data Type**: {checks.get('data_type', 'Unknown')}

## COG Compliance
- **Tiled**: {'✓' if checks.get('is_tiled') else '✗'}
- **Compressed**: {'✓' if checks.get('has_compression') else '✗'}
- **Overviews**: {'✓' if checks.get('has_overviews') else '✗'} ({checks.get('overview_count', 0)} levels)
- **Block Size**: {'✓' if checks.get('optimal_block_size') else '✗'} ({checks.get('block_size', 'Unknown')})

## Performance
- **Tile Reading**: {checks.get('tile_reading_test', {}).get('performance', 'Unknown')}
- **Read Time**: {checks.get('tile_reading_test', {}).get('read_time_ms', 0):.1f} ms

## Overall Status
**Status**: {'✓ VALID COG' if validation_result.get('valid') else '✗ INVALID COG'}

## Recommendations
"""
        
        if recommendations:
            for rec in recommendations:
                report += f"- {rec}\n"
        else:
            report += "- No recommendations - file is optimally configured\n"
        
        return report


def validate_cog_file(cog_path: str) -> Dict[str, Any]:
    """Convenience function to validate a single COG file."""
    validator = COGValidator()
    return validator.validate_cog(cog_path)


def batch_validate_cogs(directory: str) -> Dict[str, Any]:
    """Convenience function to validate all COG files in a directory."""
    validator = COGValidator()
    return validator.batch_validate(directory)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="COG Validation Tool")
    parser.add_argument("path", help="COG file or directory to validate")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--batch", action="store_true", help="Batch validate directory")
    
    args = parser.parse_args()
    
    validator = COGValidator()
    
    if args.batch or Path(args.path).is_dir():
        # Batch validation
        results = validator.batch_validate(args.path)
        
        if "error" in results:
            print(f"Error: {results['error']}")
        else:
            summary = results["summary"]
            print(f"Validation Summary:")
            print(f"  Total files: {summary['total_files']}")
            print(f"  Valid files: {summary['valid_files']}")
            print(f"  Invalid files: {summary['invalid_files']}")
            print(f"  Success rate: {summary['validation_rate']:.1%}")
            
            if args.report:
                for filename, result in results["results"].items():
                    if not result.get("valid", False):
                        print(f"\nInvalid file: {filename}")
                        print(f"  Error: {result.get('error', 'Unknown')}")
    else:
        # Single file validation
        result = validator.validate_cog(args.path)
        
        if result.get("valid"):
            print("✓ Valid COG file")
        else:
            print("✗ Invalid COG file")
            print(f"  Error: {result.get('error', 'Unknown')}")
        
        if args.report:
            report = validator.generate_validation_report(result)
            print(report)
