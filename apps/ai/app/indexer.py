"""Image indexing with CLIP and FAISS."""

import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import faiss

from app.config import INDEX_DIR, TILES_DIR, DEFAULT_PATCH_SIZE, DEFAULT_STRIDE
from app.clip_stub import create_clip_model


class ImageIndexer:
    """Build and manage FAISS indices for image datasets."""

    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.index_path = INDEX_DIR / f"{dataset_id}.faiss"
        self.metadata_path = INDEX_DIR / f"{dataset_id}_metadata.json"
        self.clip_model = create_clip_model()
        self.index = None
        self.metadata = []

    def build_index(
        self,
        patch_size: int = DEFAULT_PATCH_SIZE,
        stride: int = DEFAULT_STRIDE,
        level: int = 2,
    ):
        """
        Build FAISS index from tiled images.
        For hackathon demo, we'll create a sparse index with a few sample points.
        """
        print(f"Building index for {self.dataset_id}...")

        dataset_path = TILES_DIR / self.dataset_id
        if not dataset_path.exists():
            raise ValueError(f"Dataset path not found: {dataset_path}")

        # Collect embeddings and metadata
        embeddings = []
        metadata = []

        # For demo, create embeddings for a grid of points
        # In production, you'd scan all tiles and extract patches
        image_width, image_height = 4096, 4096  # From sample dataset
        
        for x in range(0, image_width - patch_size, stride):
            for y in range(0, image_height - patch_size, stride):
                # Generate embedding for this patch location
                # In production, load actual image and extract patch
                embedding = self.clip_model.encode_image(
                    str(dataset_path / "2" / "0_0.jpg"), x, y
                )
                embeddings.append(embedding)
                metadata.append(
                    {
                        "x": x,
                        "y": y,
                        "width": patch_size,
                        "height": patch_size,
                        "level": level,
                    }
                )

        embeddings_array = np.array(embeddings).astype("float32")

        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatL2(dimension)  # Simple L2 index for demo
        self.index.add(embeddings_array)
        self.metadata = metadata

        # Save index and metadata
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f)

        print(f"Index built with {len(metadata)} patches")

    def load_index(self):
        """Load existing index."""
        if not self.index_path.exists():
            raise ValueError(f"Index not found: {self.index_path}")

        self.index = faiss.read_index(str(self.index_path))
        with open(self.metadata_path, "r") as f:
            self.metadata = json.load(f)

    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Search for patches matching the query."""
        if self.index is None:
            try:
                self.load_index()
            except ValueError:
                # Index doesn't exist, return empty results
                print(f"Index not found for {self.dataset_id}, returning empty results")
                return []

        # Encode query
        query_embedding = self.clip_model.encode_text(query)
        query_embedding = np.array([query_embedding]).astype("float32")

        # Search
        distances, indices = self.index.search(query_embedding, top_k)

        # Format results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                meta = self.metadata[idx]
                results.append(
                    {
                        "bbox": {
                            "x": meta["x"],
                            "y": meta["y"],
                            "width": meta["width"],
                            "height": meta["height"],
                        },
                        "score": float(1.0 / (1.0 + dist)),  # Convert distance to similarity
                        "metadata": {"level": meta.get("level", 2)},
                    }
                )

        return results


def build_index_for_dataset(dataset_id: str):
    """Build index for a specific dataset."""
    indexer = ImageIndexer(dataset_id)
    indexer.build_index()
    return indexer

