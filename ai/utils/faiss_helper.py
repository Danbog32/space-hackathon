import json
from pathlib import Path
import numpy as np
import faiss
import logging
from typing import Dict, List, Optional, Any, Tuple
import pickle
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class DatasetIndexManager:
    """Manages FAISS indices for multiple datasets with metadata."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True, parents=True)
        self.indices: Dict[str, faiss.Index] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
    
    def create_dataset_index(self, dataset_id: str, embedding_dim: int, 
                           index_type: str = "flat") -> faiss.Index:
        """Create a new FAISS index for a dataset."""
        if index_type == "flat":
            index = faiss.IndexFlatIP(embedding_dim)
        elif index_type == "ivf":
            # IVF index for larger datasets
            quantizer = faiss.IndexFlatIP(embedding_dim)
            index = faiss.IndexIVFFlat(quantizer, embedding_dim, 100)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        self.indices[dataset_id] = index
        self.metadata[dataset_id] = {
            "dataset_id": dataset_id,
            "embedding_dim": embedding_dim,
            "index_type": index_type,
            "created_at": datetime.now().isoformat(),
            "num_vectors": 0,
            "is_trained": False
        }
        
        logger.info(f"Created {index_type} index for dataset {dataset_id}")
        return index
    
    def add_vectors(self, dataset_id: str, vectors: np.ndarray, 
                   patch_metadata: List[Dict[str, Any]]) -> None:
        """Add vectors and metadata to a dataset index."""
        if dataset_id not in self.indices:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        index = self.indices[dataset_id]
        vectors = vectors.astype(np.float32)
        
        # Train index if needed (for IVF)
        if hasattr(index, 'is_trained') and not index.is_trained:
            logger.info(f"Training index for dataset {dataset_id}")
            index.train(vectors)
            self.metadata[dataset_id]["is_trained"] = True
        
        # Add vectors
        index.add(vectors)
        
        # Update metadata
        self.metadata[dataset_id]["num_vectors"] += len(vectors)
        self.metadata[dataset_id]["last_updated"] = datetime.now().isoformat()
        
        # Save patch metadata
        metadata_path = self.base_dir / f"{dataset_id}_patches.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                existing_metadata = json.load(f)
        else:
            existing_metadata = []
        
        existing_metadata.extend(patch_metadata)
        
        with open(metadata_path, 'w') as f:
            json.dump(existing_metadata, f, indent=2)
        
        logger.info(f"Added {len(vectors)} vectors to dataset {dataset_id}")
    
    def search(self, dataset_id: str, query_vector: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for similar vectors in a dataset."""
        if dataset_id not in self.indices:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        index = self.indices[dataset_id]
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        
        scores, indices = index.search(query_vector, k)
        return scores[0], indices[0]
    
    def get_patch_metadata(self, dataset_id: str, patch_indices: List[int]) -> List[Dict[str, Any]]:
        """Get metadata for specific patch indices."""
        metadata_path = self.base_dir / f"{dataset_id}_patches.json"
        if not metadata_path.exists():
            return []
        
        with open(metadata_path, 'r') as f:
            all_metadata = json.load(f)
        
        return [all_metadata[i] for i in patch_indices if i < len(all_metadata)]
    
    def save_dataset(self, dataset_id: str) -> None:
        """Save dataset index and metadata to disk."""
        if dataset_id not in self.indices:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        # Save index
        index_path = self.base_dir / f"{dataset_id}.faiss"
        faiss.write_index(self.indices[dataset_id], str(index_path))
        
        # Save metadata
        metadata_path = self.base_dir / f"{dataset_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata[dataset_id], f, indent=2)
        
        logger.info(f"Saved dataset {dataset_id} to {index_path}")
    
    def load_dataset(self, dataset_id: str) -> bool:
        """Load dataset index and metadata from disk."""
        index_path = self.base_dir / f"{dataset_id}.faiss"
        metadata_path = self.base_dir / f"{dataset_id}_metadata.json"
        
        if not index_path.exists() or not metadata_path.exists():
            return False
        
        try:
            # Load index
            self.indices[dataset_id] = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata[dataset_id] = json.load(f)
            
            logger.info(f"Loaded dataset {dataset_id}")
            return True
        except Exception as e:
            logger.error(f"Error loading dataset {dataset_id}: {e}")
            return False
    
    def list_datasets(self) -> List[str]:
        """List all available datasets."""
        return list(self.metadata.keys())
    
    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a dataset."""
        return self.metadata.get(dataset_id)

def build_faiss_index(vectors: np.ndarray, index_type: str = "flat") -> faiss.Index:
    """Build a FAISS index from vectors."""
    dim = vectors.shape[1]
    
    if index_type == "flat":
        index = faiss.IndexFlatIP(dim)
    elif index_type == "ivf":
        quantizer = faiss.IndexFlatIP(dim)
        index = faiss.IndexIVFFlat(quantizer, dim, min(100, len(vectors) // 10))
        if len(vectors) > 0:
            index.train(vectors.astype(np.float32))
    else:
        raise ValueError(f"Unknown index type: {index_type}")
    
    index.add(vectors.astype(np.float32))
    return index

def save_index(index: faiss.Index, path: Path) -> None:
    """Save FAISS index to disk."""
    faiss.write_index(index, str(path))

def load_index(path: Path) -> faiss.Index:
    """Load FAISS index from disk."""
    return faiss.read_index(str(path))

def save_metadata(metadata: dict, path: Path) -> None:
    """Save metadata to JSON file."""
    path.write_text(json.dumps(metadata, indent=2))

def load_metadata(path: Path) -> dict:
    """Load metadata from JSON file."""
    return json.loads(path.read_text())

def create_dataset_hash(dataset_id: str, image_paths: List[str], 
                       patch_config: Dict[str, Any]) -> str:
    """Create a hash for dataset versioning."""
    content = f"{dataset_id}:{sorted(image_paths)}:{patch_config}"
    return hashlib.md5(content.encode()).hexdigest()[:8]

def optimize_index_for_search(index: faiss.Index, vectors: np.ndarray) -> faiss.Index:
    """Optimize index for better search performance."""
    if hasattr(index, 'is_trained') and not index.is_trained:
        logger.info("Training index for optimization")
        index.train(vectors.astype(np.float32))
    
    # For IVF indices, adjust nprobe for better recall
    if hasattr(index, 'nprobe'):
        index.nprobe = min(10, index.ntotal // 10)
    
    return index
