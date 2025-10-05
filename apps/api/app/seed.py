"""Database seeding script."""

import json
import subprocess
import sys
from pathlib import Path
from sqlmodel import Session, select

from app.db import engine
from app.models import Dataset, Feature


def seed_database():
    """Seed database with sample data."""
    # Ensure tiles exist for default datasets before seeding
    repo_root = Path(__file__).parent.parent.parent.parent
    infra_dir = repo_root / "infra"
    andromeda_tiles = infra_dir / "tiles" / "andromeda" / "info.dzi"
    earth_tiles = infra_dir / "tiles" / "earth" / "info.dzi"
    sun_tiles = infra_dir / "tiles" / "sun" / "info.dzi"
    hockey_tiles = infra_dir / "tiles" / "hockey" / "info.dzi"

    try:
        if not andromeda_tiles.exists():
            print("Andromeda tiles missing; generating via process_real_image.py ...")
            subprocess.run([sys.executable, str(infra_dir / "process_real_image.py")], check=True)
        if not earth_tiles.exists():
            print("Earth tiles missing; generating via process_earth_image.py ...")
            subprocess.run([sys.executable, str(infra_dir / "process_earth_image.py")], check=True)
        if not sun_tiles.exists():
            print("Sun tiles missing; generating via process_sun_image.py ...")
            subprocess.run([sys.executable, str(infra_dir / "process_sun_image.py")], check=True)
        if not hockey_tiles.exists():
            print("Hockey Stick tiles missing; generating via process_hockey_image.py ...")
            subprocess.run([sys.executable, str(infra_dir / "process_hockey_image.py")], check=True)
    except Exception as e:
        print(f"Warning: automatic tile generation failed: {e}")

    with Session(engine) as session:
        # Check if andromeda dataset already exists
        statement = select(Dataset).where(Dataset.id == "andromeda")
        existing = session.exec(statement).first()
        seed_andromeda = False
        if existing:
            print("Andromeda already present, skipping its seeding...")
        else:
            print("Seeding database with sample data...")
            seed_andromeda = True
        
        # Detect if we're using real tiles or mock tiles
        # Real NASA image is 42208 x 9870
        # Mock/sample is 1024 x 1024
        import xml.etree.ElementTree as ET
        
        # Try to read actual DZI metadata
        dzi_path = repo_root / "infra" / "tiles" / "andromeda" / "info.dzi"
        
        width, height = 1024, 1024  # Default to mock
        is_real_dataset = False
        
        if dzi_path.exists():
            try:
                tree = ET.parse(dzi_path)
                size_node = tree.find("{http://schemas.microsoft.com/deepzoom/2008}Size")
                if size_node is not None:
                    width = int(size_node.attrib.get("Width", "1024"))
                    height = int(size_node.attrib.get("Height", "1024"))
                    is_real_dataset = width > 10000  # Real NASA image is 42208px wide
            except Exception:
                pass
        
        # Create Andromeda dataset with appropriate metadata
        # Check available zoom levels to determine if it's a preview or full resolution
        import os
        available_levels = []
        andromeda_tiles_path = repo_root / "infra" / "tiles" / "andromeda"
        if andromeda_tiles_path.exists():
            available_levels = [int(d.name) for d in andromeda_tiles_path.iterdir() if d.is_dir() and d.name.isdigit()]
        
        # Full resolution would need ~16 levels for 42208px, if we have less it's a preview
        is_preview = len(available_levels) < 10
        
        if is_real_dataset and not is_preview:
            name = "Andromeda Galaxy (NASA Hubble)"
            description = "High-resolution Hubble Space Telescope mosaic of the Andromeda Galaxy (M31). 42208x9870 pixels of stunning detail showing the spiral structure, star-forming regions, and galactic core."
            date = "2025-01-01"
        elif is_real_dataset and is_preview:
            name = "Andromeda Galaxy (Preview)"
            description = "Preview of Andromeda Galaxy (M31) from NASA Hubble Space Telescope. High-resolution spiral galaxy showing the galactic core, spiral arms, and star-forming regions."
            date = "2025-01-01"
        else:
            name = "Andromeda Galaxy (Sample)"
            description = "A sample deep-zoom image of the Andromeda Galaxy M31"
            date = "2015-01-05"
        
        # Sort levels to ensure proper order
        if available_levels:
            available_levels.sort()
        
        if seed_andromeda:
            andromeda = Dataset(
                id="andromeda",
                name=name,
                description=description,
                tile_type="dzi",
                tile_url="/tiles/andromeda",
                levels=json.dumps(available_levels if available_levels else [0, 1, 2]),
                pixel_size=json.dumps([width, height]),
                metadata_={
                    "telescope": "Hubble Space Telescope",
                    "filter": "Composite RGB",
                    "date": date,
                    "is_real_data": is_real_dataset,
                    "is_preview": is_preview if is_real_dataset else False,
                    "available_levels": len(available_levels) if available_levels else 3,
                    "full_resolution": [width, height] if is_real_dataset else None,
                },
            )
            session.add(andromeda)
        
        # Add some sample features with coordinates appropriate for image size
        if seed_andromeda and is_real_dataset:
            # Coordinates for high-resolution image (42208 x 9870)
            features = [
                Feature(
                    dataset_id="andromeda",
                    name="Galaxy Core",
                    type="bbox",
                    geometry=json.dumps({"x": 21000, "y": 4900, "width": 3000, "height": 2000}),
                    properties=json.dumps({"description": "Bright galactic core region of M31"}),
                ),
                Feature(
                    dataset_id="andromeda",
                    name="Spiral Arm",
                    type="bbox",
                    geometry=json.dumps({"x": 10000, "y": 3000, "width": 4000, "height": 2500}),
                    properties=json.dumps({"description": "Prominent spiral arm structure"}),
                ),
                Feature(
                    dataset_id="andromeda",
                    name="Star Cluster",
                    type="point",
                    geometry=json.dumps({"x": 30000, "y": 6000}),
                    properties=json.dumps({"description": "Dense star cluster visible in outer regions"}),
                ),
            ]
        elif seed_andromeda:
            # Coordinates for sample image (~1024 x 1024)
            features = [
                Feature(
                    dataset_id="andromeda",
                    name="Galaxy Core",
                    type="bbox",
                    geometry=json.dumps({"x": 1800, "y": 1800, "width": 500, "height": 500}),
                    properties=json.dumps({"description": "Bright galactic core region"}),
                ),
                Feature(
                    dataset_id="andromeda",
                    name="Spiral Arm",
                    type="bbox",
                    geometry=json.dumps({"x": 800, "y": 1200, "width": 400, "height": 300}),
                    properties=json.dumps({"description": "Prominent spiral arm structure"}),
                ),
                Feature(
                    dataset_id="andromeda",
                    name="Star Cluster",
                    type="point",
                    geometry=json.dumps({"x": 2400, "y": 2200}),
                    properties=json.dumps({"description": "Dense star cluster"}),
                ),
            ]
        if seed_andromeda:
            for feature in features:
                session.add(feature)
            session.commit()
            print("Database seeded successfully!")

        # Seed Earth dataset if tiles exist
        earth_existing = session.exec(select(Dataset).where(Dataset.id == "earth")).first()
        earth_tiles_path = repo_root / "infra" / "tiles" / "earth"
        earth_dzi_path = earth_tiles_path / "info.dzi"
        if earth_existing is None and earth_tiles_path.exists():
            # Try reading DZI; if missing, fall back to safe defaults
            earth_width, earth_height = 1024, 1024
            if earth_dzi_path.exists():
                try:
                    tree = ET.parse(earth_dzi_path)
                    size_node = tree.find("{http://schemas.microsoft.com/deepzoom/2008}Size")
                    if size_node is not None:
                        earth_width = int(size_node.attrib.get("Width", "1024"))
                        earth_height = int(size_node.attrib.get("Height", "1024"))
                except Exception:
                    pass

            earth_levels = [
                int(d.name)
                for d in earth_tiles_path.iterdir()
                if d.is_dir() and d.name.isdigit()
            ] if earth_tiles_path.exists() else []
            earth_levels.sort()

            earth = Dataset(
                id="earth",
                name="Earth (Suomi NPP)",
                description="High-resolution Earth image processed into Deep Zoom tiles.",
                tile_type="dzi",
                tile_url="/tiles/earth",
                levels=json.dumps(earth_levels if earth_levels else [0, 1, 2]),
                pixel_size=json.dumps([earth_width, earth_height]),
                metadata_={
                    "source": "NASA",
                    "platform": "Suomi NPP",
                    "is_real_data": True,
                    "available_levels": len(earth_levels) if earth_levels else 3,
                    "full_resolution": [earth_width, earth_height],
                },
            )
            session.add(earth)
            session.commit()
            print("Earth dataset seeded successfully!")

        # Seed Sun dataset if tiles exist
        sun_existing = session.exec(select(Dataset).where(Dataset.id == "sun")).first()
        sun_tiles_path = repo_root / "infra" / "tiles" / "sun"
        sun_dzi_path = sun_tiles_path / "info.dzi"
        if sun_existing is None and sun_tiles_path.exists():
            sun_width, sun_height = 1024, 1024
            if sun_dzi_path.exists():
                try:
                    tree = ET.parse(sun_dzi_path)
                    size_node = tree.find("{http://schemas.microsoft.com/deepzoom/2008}Size")
                    if size_node is not None:
                        sun_width = int(size_node.attrib.get("Width", "1024"))
                        sun_height = int(size_node.attrib.get("Height", "1024"))
                except Exception:
                    pass

            sun_levels = [
                int(d.name)
                for d in sun_tiles_path.iterdir()
                if d.is_dir() and d.name.isdigit()
            ] if sun_tiles_path.exists() else []
            sun_levels.sort()

            sun = Dataset(
                id="sun",
                name="Sun (NASA Archive)",
                description="High-resolution Sun image processed into Deep Zoom tiles.",
                tile_type="dzi",
                tile_url="/tiles/sun",
                levels=json.dumps(sun_levels if sun_levels else [0, 1, 2]),
                pixel_size=json.dumps([sun_width, sun_height]),
                metadata_={
                    "source": "NASA",
                    "platform": "SDO/GSFC Archive",
                    "is_real_data": True,
                    "available_levels": len(sun_levels) if sun_levels else 3,
                    "full_resolution": [sun_width, sun_height],
                },
            )
            session.add(sun)
            session.commit()
            print("Sun dataset seeded successfully!")

        # Seed Hockey Stick dataset if tiles exist
        hockey_existing = session.exec(select(Dataset).where(Dataset.id == "hockey")).first()
        hockey_tiles_path = repo_root / "infra" / "tiles" / "hockey"
        hockey_dzi_path = hockey_tiles_path / "info.dzi"
        if hockey_existing is None and hockey_tiles_path.exists():
            hockey_width, hockey_height = 1024, 1024
            if hockey_dzi_path.exists():
                try:
                    tree = ET.parse(hockey_dzi_path)
                    size_node = tree.find("{http://schemas.microsoft.com/deepzoom/2008}Size")
                    if size_node is not None:
                        hockey_width = int(size_node.attrib.get("Width", "1024"))
                        hockey_height = int(size_node.attrib.get("Height", "1024"))
                except Exception:
                    pass

            hockey_levels = [
                int(d.name)
                for d in hockey_tiles_path.iterdir()
                if d.is_dir() and d.name.isdigit()
            ] if hockey_tiles_path.exists() else []
            hockey_levels.sort()

            hockey = Dataset(
                id="hockey",
                name="Hockey Stick Galaxy (NASA Archive)",
                description="High-resolution Hockey Stick Galaxy image processed into Deep Zoom tiles.",
                tile_type="dzi",
                tile_url="/tiles/hockey",
                levels=json.dumps(hockey_levels if hockey_levels else [0, 1, 2]),
                pixel_size=json.dumps([hockey_width, hockey_height]),
                metadata_={
                    "source": "NASA",
                    "platform": "GSFC Archive",
                    "is_real_data": True,
                    "available_levels": len(hockey_levels) if hockey_levels else 3,
                    "full_resolution": [hockey_width, hockey_height],
                },
            )
            session.add(hockey)
            session.commit()
            print("Hockey Stick dataset seeded successfully!")


if __name__ == "__main__":
    from app.db import create_db_and_tables
    
    create_db_and_tables()
    seed_database()
