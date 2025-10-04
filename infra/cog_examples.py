#!/usr/bin/env python3
"""
COG Conversion and Management Examples

This script demonstrates how to use the universal COG converter
and validation tools for various image formats.
"""

import os
import sys
from pathlib import Path

# Add the infra directory to the path
sys.path.append(str(Path(__file__).parent))

from universal_cog_converter import UniversalCOGConverter
from cog_validator import COGValidator

def example_single_file_conversion():
    """Example: Convert a single image file to COG."""
    
    print("=== Single File Conversion Example ===")
    
    converter = UniversalCOGConverter(output_dir="infra/cogs")
    
    # Example files (replace with your actual files)
    example_files = [
        "mars_orbital_scan.img",
        "planetary_surface.tif", 
        "satellite_image.jpg",
        "astronomical_data.png"
    ]
    
    for file_path in example_files:
        if Path(file_path).exists():
            print(f"\nConverting {file_path}...")
            
            try:
                result = converter.convert_image(
                    file_path,
                    compression="lzw"  # Lossless compression for scientific data
                )
                
                if result["success"]:
                    print(f"✓ Success: {result['output_path']}")
                    
                    # Validate the COG
                    validator = COGValidator()
                    validation = validator.validate_cog(result["output_path"])
                    
                    if validation["valid"]:
                        print("✓ COG validation passed")
                    else:
                        print("✗ COG validation failed")
                        print(f"  Error: {validation.get('error', 'Unknown')}")
                else:
                    print(f"✗ Conversion failed: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                print(f"✗ Error converting {file_path}: {e}")
        else:
            print(f"⚠ File not found: {file_path}")

def example_batch_conversion():
    """Example: Batch convert multiple files."""
    
    print("\n=== Batch Conversion Example ===")
    
    converter = UniversalCOGConverter(output_dir="infra/cogs")
    
    # Convert all supported files in a directory
    input_directory = "infra/source_images"  # Replace with your directory
    
    if Path(input_directory).exists():
        print(f"Batch converting files in {input_directory}...")
        
        results = converter.batch_convert(
            input_directory,
            pattern="*",  # All files
            compression="lzw"
        )
        
        # Generate report
        report = converter.generate_conversion_report(results)
        
        # Save report
        report_path = Path("infra/cogs/conversion_report.md")
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"✓ Batch conversion complete. Report saved to: {report_path}")
        
        # Validate all converted COGs
        validator = COGValidator()
        validation_results = validator.batch_validate("infra/cogs")
        
        print(f"\nValidation Summary:")
        summary = validation_results["summary"]
        print(f"  Total COG files: {summary['total_files']}")
        print(f"  Valid COG files: {summary['valid_files']}")
        print(f"  Success rate: {summary['validation_rate']:.1%}")
        
    else:
        print(f"⚠ Input directory not found: {input_directory}")

def example_cog_validation():
    """Example: Validate COG files."""
    
    print("\n=== COG Validation Example ===")
    
    validator = COGValidator()
    
    # Validate a single COG file
    cog_file = "infra/cogs/mars_orbital_scan.cog.tif"
    
    if Path(cog_file).exists():
        print(f"Validating {cog_file}...")
        
        result = validator.validate_cog(cog_file)
        
        if result["valid"]:
            print("✓ Valid COG file")
        else:
            print("✗ Invalid COG file")
            print(f"  Error: {result.get('error', 'Unknown')}")
        
        # Generate detailed report
        report = validator.generate_validation_report(result)
        print("\nDetailed Report:")
        print(report)
        
    else:
        print(f"⚠ COG file not found: {cog_file}")
    
    # Batch validate all COGs
    cog_directory = "infra/cogs"
    if Path(cog_directory).exists():
        print(f"\nBatch validating COGs in {cog_directory}...")
        
        batch_results = validator.batch_validate(cog_directory)
        
        if "error" not in batch_results:
            summary = batch_results["summary"]
            print(f"Batch Validation Results:")
            print(f"  Total files: {summary['total_files']}")
            print(f"  Valid files: {summary['valid_files']}")
            print(f"  Invalid files: {summary['invalid_files']}")
            print(f"  Success rate: {summary['validation_rate']:.1%}")

def example_database_integration():
    """Example: How to integrate COG datasets with the database."""
    
    print("\n=== Database Integration Example ===")
    
    # This would typically be done in your API
    example_dataset = {
        "id": "mars_orbital_cog",
        "name": "Mars Orbital Scan (COG)",
        "description": "High-resolution Mars orbital imagery in COG format",
        "tile_type": "cog",
        "tile_url": "/tiles/mars_orbital_cog",
        "levels": "[0, 1, 2, 3, 4]",
        "pixel_size": "[8192, 4096]",
        "source_format": "IMG",
        "source_file": "mars_orbital_scan.img",
        "cog_file": "mars_orbital_scan.cog.tif",
        "is_dynamic": False,
        "metadata": {
            "mission": "Mars Reconnaissance Orbiter",
            "instrument": "HiRISE",
            "date": "2024-01-15",
            "resolution": "25cm/pixel",
            "conversion_date": "2024-01-20",
            "conversion_tool": "universal_cog_converter"
        }
    }
    
    print("Example dataset configuration:")
    for key, value in example_dataset.items():
        print(f"  {key}: {value}")

def example_api_usage():
    """Example: How to use the COG API endpoints."""
    
    print("\n=== API Usage Example ===")
    
    base_url = "http://localhost:8000"
    dataset_id = "mars_orbital_cog"
    
    api_endpoints = {
        "DZI Info": f"{base_url}/tiles/{dataset_id}/info.dzi",
        "COG Info": f"{base_url}/tiles/{dataset_id}/cog/info", 
        "COG Validation": f"{base_url}/tiles/{dataset_id}/cog/validate",
        "COG Tile": f"{base_url}/tiles/{dataset_id}/cog/0/0_0.jpg",
        "Thumbnail": f"{base_url}/tiles/{dataset_id}/thumbnail.jpg",
        "Dataset Info": f"{base_url}/datasets/{dataset_id}"
    }
    
    print("Available API endpoints:")
    for name, url in api_endpoints.items():
        print(f"  {name}: {url}")
    
    print("\nExample curl commands:")
    for name, url in api_endpoints.items():
        print(f"  # {name}")
        print(f"  curl {url}")
        print()

def main():
    """Run all examples."""
    
    print("🌌 COG Conversion and Management Examples")
    print("=" * 50)
    
    # Check if required libraries are available
    try:
        import rasterio
        print("✓ rasterio available")
    except ImportError:
        print("✗ rasterio not available - install with: pip install rasterio")
        return
    
    try:
        from rio_cogeo.cogeo import cog_translate
        print("✓ rio-cogeo available")
    except ImportError:
        print("⚠ rio-cogeo not available - install with: pip install rio-cogeo")
        print("  (Will use rasterio fallback)")
    
    # Run examples
    example_single_file_conversion()
    example_batch_conversion()
    example_cog_validation()
    example_database_integration()
    example_api_usage()
    
    print("\n" + "=" * 50)
    print("✅ Examples complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install rasterio rio-cogeo")
    print("2. Convert your images: python3 infra/universal_cog_converter.py your_image.img")
    print("3. Validate COGs: python3 infra/cog_validator.py infra/cogs/")
    print("4. Start your API: pnpm dev")
    print("5. Test endpoints: curl http://localhost:8000/tiles/your_dataset/cog/info")

if __name__ == "__main__":
    main()
