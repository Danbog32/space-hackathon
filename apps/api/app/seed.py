"""Database seeding script."""

import json
from sqlmodel import Session, select

from app.db import engine
from app.models import Dataset, Feature


def seed_database():
    """Seed database with sample data."""
    with Session(engine) as session:
        # Check if andromeda dataset already exists
        statement = select(Dataset).where(Dataset.id == "andromeda")
        existing = session.exec(statement).first()
        
        if existing:
            print("Database already seeded, skipping...")
            return
        
        print("Seeding database with sample data...")
        
        # Detect if we're using real tiles or mock tiles
        # Real NASA image is 42208 x 9870
        # Mock/sample is 1024 x 1024
        from pathlib import Path
        import xml.etree.ElementTree as ET
        
        # Try to read actual DZI metadata
        dzi_path = Path(__file__).parent.parent.parent.parent / "infra" / "tiles" / "andromeda" / "info.dzi"
        
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
        if is_real_dataset:
            name = "Andromeda Galaxy (NASA Hubble 2025)"
            description = "High-resolution Hubble Space Telescope mosaic of the Andromeda Galaxy (M31). 42208x9870 pixels of stunning detail showing the spiral structure, star-forming regions, and galactic core."
            date = "2025-01-01"
        else:
            name = "Andromeda Galaxy (Sample)"
            description = "A sample deep-zoom image of the Andromeda Galaxy M31"
            date = "2015-01-05"
        
        andromeda = Dataset(
            id="andromeda",
            name=name,
            description=description,
            tile_type="dzi",
            tile_url="/tiles/andromeda",
            levels=json.dumps([0, 1, 2]),  # Will be dynamically detected by tile server
            pixel_size=json.dumps([width, height]),
            metadata_={
                "telescope": "Hubble Space Telescope",
                "filter": "Composite RGB",
                "date": date,
                "is_real_data": is_real_dataset,
            },
        )
        session.add(andromeda)
        
        # Add some sample features
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
        
        for feature in features:
            session.add(feature)
        
        session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    from app.db import create_db_and_tables
    
    create_db_and_tables()
    seed_database()
