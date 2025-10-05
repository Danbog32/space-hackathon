#!/usr/bin/env python3
"""
Build FAISS index - now supports both demo and real data.
"""

import logging
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import argparse

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from models.clip_model import ClipEncoder
from utils.patch_extractor import PatchExtractor
from utils.faiss_helper import DatasetIndexManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def build_demo_index():
    """Build demo index with synthetic data (backward compatibility)."""
    DATA_DIR = Path(__file__).parent / "data"
    IMG_PATH = DATA_DIR / "demo_big.jpg"
    
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    
    logger.info("Loading or creating demo image...")
    extractor = PatchExtractor(patch_sizes=[128], stride_ratios=[1.0])
    img = extractor.load_or_make_demo_image(IMG_PATH, size=(4096, 4096))
    
    logger.info("Initializing CLIP...")
    encoder = ClipEncoder(device="cpu")
    
    logger.info("Extracting patches and encoding...")
    bboxes = []
    embs = []
    
    for patch, metadata in extractor.extract_patches(img):
        emb = encoder.encode_image(patch)
        embs.append(emb.numpy())
        bboxes.append(metadata['bbox'])
    
    embs = np.stack(embs, axis=0).astype(np.float32)
    logger.info(f"Building FAISS index with {embs.shape[0]} patches...")
    
    # Use new index manager
    index_manager = DatasetIndexManager(DATA_DIR)
    dataset_id = "demo"
    
    # Create index
    embedding_dim = encoder.get_embedding_dim()
    index = index_manager.create_dataset_index(dataset_id, embedding_dim)
    
    # Add vectors
    patch_metadata = [{"bbox": bbox} for bbox in bboxes]
    index_manager.add_vectors(dataset_id, embs, patch_metadata)
    
    # Save
    index_manager.save_dataset(dataset_id)
    
    logger.info("Demo index completed!")

def main():
    parser = argparse.ArgumentParser(description="Build FAISS index")
    parser.add_argument("--demo", action="store_true", 
                       help="Build demo index with synthetic data")
    parser.add_argument("--real", action="store_true",
                       help="Build real index from space imagery")
    parser.add_argument("--tiles-dir", type=Path, default=Path("../infra/tiles"),
                       help="Directory containing DZI tiles")
    parser.add_argument("--dataset-id", type=str, default="andromeda",
                       help="Dataset ID to process")
    
    args = parser.parse_args()
    
    if args.real:
        # Use the new real indexer
        from build_real_index import SpaceImageryIndexer
        
        indexer = SpaceImageryIndexer(
            tiles_dir=args.tiles_dir,
            output_dir=Path("data"),
            patch_sizes=[64, 128, 256],
            max_patches_per_scale=1000
        )
        
        dzi_path = args.tiles_dir / args.dataset_id / "info.dzi"
        if dzi_path.exists():
            success = indexer.process_dzi_dataset(args.dataset_id, dzi_path)
            if success:
                logger.info("Real index building completed!")
            else:
                logger.error("Real index building failed!")
                return 1
        else:
            logger.error(f"DZI file not found: {dzi_path}")
            return 1
    else:
        # Build demo index
        build_demo_index()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
