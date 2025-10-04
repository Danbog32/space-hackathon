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
        
        # Create Andromeda sample dataset
        andromeda = Dataset(
            id="andromeda",
            name="Andromeda Galaxy (Sample)",
            description="A sample deep-zoom image of the Andromeda Galaxy M31",
            tile_type="dzi",
            tile_url="/tiles/andromeda",
            levels=json.dumps([0, 1, 2]),
            pixel_size=json.dumps([4096, 4096]),
            metadata_={
                "telescope": "Hubble Space Telescope",
                "filter": "Composite RGB",
                "date": "2015-01-05",
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
