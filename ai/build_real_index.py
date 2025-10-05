#!/usr/bin/env python3
"""
Build FAISS index from real space imagery data.
Processes DZI tiles and creates multi-scale patch embeddings.
"""

import logging
import sys
from pathlib import Path
import numpy as np
from PIL import Image
import json
from typing import List, Dict, Any, Tuple
import argparse
from tqdm import tqdm

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from models.clip_model import ClipEncoder
from utils.patch_extractor import PatchExtractor
from utils.faiss_helper import DatasetIndexManager, create_dataset_hash

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpaceImageryIndexer:
    """Index space imagery data with multi-scale patches."""
    
    def __init__(self, tiles_dir: Path, output_dir: Path, 
                 patch_sizes: List[int] = [64, 128, 256],
                 max_patches_per_scale: int = 1000):
        self.tiles_dir = Path(tiles_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.patch_extractor = PatchExtractor(
            patch_sizes=patch_sizes,
            stride_ratios=[0.5, 0.75, 1.0],
            quality_threshold=0.05,
            max_patches_per_scale=max_patches_per_scale
        )
        
        self.index_manager = DatasetIndexManager(self.output_dir)
        
        # Initialize CLIP model
        logger.info("Initializing CLIP model...")
        self.clip = ClipEncoder(device=None)  # Auto-detect device
        logger.info(f"CLIP model info: {self.clip.get_model_info()}")
    
    def process_dzi_dataset(self, dataset_id: str, dzi_path: Path) -> bool:
        """Process a DZI dataset and create embeddings."""
        try:
            # Load DZI info
            with open(dzi_path, 'r') as f:
                dzi_info = json.load(f)
            
            logger.info(f"Processing DZI dataset: {dataset_id}")
            logger.info(f"Image size: {dzi_info['Image']['Size']}")
            logger.info(f"Tile size: {dzi_info['Image']['TileSize']}")
            logger.info(f"Overlap: {dzi_info['Image']['Overlap']}")
            
            # Create dataset index
            embedding_dim = self.clip.get_embedding_dim()
            index = self.index_manager.create_dataset_index(
                dataset_id, embedding_dim, index_type="flat"
            )
            
            # Process each zoom level
            levels = list(dzi_info['Image']['Size'].keys())
            total_patches = 0
            
            for level in sorted(levels, key=int):
                level_dir = self.tiles_dir / dataset_id / level
                if not level_dir.exists():
                    logger.warning(f"Level {level} directory not found: {level_dir}")
                    continue
                
                logger.info(f"Processing level {level}...")
                level_patches = self._process_level(level_dir, level, dataset_id)
                total_patches += level_patches
                
                if total_patches > 0:
                    logger.info(f"Level {level}: {level_patches} patches")
            
            # Save dataset
            self.index_manager.save_dataset(dataset_id)
            logger.info(f"Completed dataset {dataset_id}: {total_patches} total patches")
            return True
            
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            return False
    
    def _process_level(self, level_dir: Path, level: int, dataset_id: str) -> int:
        """Process all tiles in a zoom level."""
        tile_files = list(level_dir.glob("*.jpg")) + list(level_dir.glob("*.png"))
        if not tile_files:
            return 0
        
        level_patches = 0
        batch_size = 32
        patch_batch = []
        metadata_batch = []
        
        for tile_file in tqdm(tile_files, desc=f"Level {level}"):
            try:
                # Load tile
                tile_img = Image.open(tile_file)
                
                # Extract patches
                for patch, metadata in self.patch_extractor.extract_patches(tile_img):
                    # Add tile-specific metadata
                    metadata.update({
                        'tile_file': str(tile_file.name),
                        'level': level,
                        'dataset_id': dataset_id
                    })
                    
                    patch_batch.append(patch)
                    metadata_batch.append(metadata)
                    
                    # Process batch when full
                    if len(patch_batch) >= batch_size:
                        self._process_patch_batch(patch_batch, metadata_batch, dataset_id)
                        level_patches += len(patch_batch)
                        patch_batch = []
                        metadata_batch = []
                
            except Exception as e:
                logger.warning(f"Error processing tile {tile_file}: {e}")
                continue
        
        # Process remaining patches
        if patch_batch:
            self._process_patch_batch(patch_batch, metadata_batch, dataset_id)
            level_patches += len(patch_batch)
        
        return level_patches
    
    def _process_patch_batch(self, patches: List[Image.Image], 
                           metadata: List[Dict[str, Any]], dataset_id: str) -> None:
        """Process a batch of patches and add to index."""
        try:
            # Encode patches
            embeddings = []
            for patch in patches:
                emb = self.clip.encode_image(patch)
                embeddings.append(emb.numpy())
            
            # Convert to numpy array
            embeddings = np.stack(embeddings, axis=0)
            
            # Add to index
            self.index_manager.add_vectors(dataset_id, embeddings, metadata)
            
        except Exception as e:
            logger.error(f"Error processing patch batch: {e}")
    
    def process_single_image(self, dataset_id: str, image_path: Path) -> bool:
        """Process a single large image (for demo purposes)."""
        try:
            logger.info(f"Processing single image: {image_path}")
            
            # Load image
            img = Image.open(image_path)
            logger.info(f"Image size: {img.size}")
            
            # Create dataset index
            embedding_dim = self.clip.get_embedding_dim()
            index = self.index_manager.create_dataset_index(
                dataset_id, embedding_dim, index_type="flat"
            )
            
            # Extract patches
            patch_batch = []
            metadata_batch = []
            batch_size = 32
            
            for patch, metadata in self.patch_extractor.extract_patches(img):
                metadata.update({
                    'source_image': str(image_path.name),
                    'dataset_id': dataset_id
                })
                
                patch_batch.append(patch)
                metadata_batch.append(metadata)
                
                # Process batch when full
                if len(patch_batch) >= batch_size:
                    self._process_patch_batch(patch_batch, metadata_batch, dataset_id)
                    patch_batch = []
                    metadata_batch = []
            
            # Process remaining patches
            if patch_batch:
                self._process_patch_batch(patch_batch, metadata_batch, dataset_id)
            
            # Save dataset
            self.index_manager.save_dataset(dataset_id)
            logger.info(f"Completed single image processing: {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing single image {image_path}: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Build FAISS index from space imagery")
    parser.add_argument("--tiles-dir", type=Path, default=Path("../infra/tiles"),
                       help="Directory containing DZI tiles")
    parser.add_argument("--output-dir", type=Path, default=Path("data"),
                       help="Output directory for indices")
    parser.add_argument("--dataset-id", type=str, default="andromeda",
                       help="Dataset ID to process")
    parser.add_argument("--patch-sizes", nargs="+", type=int, default=[64, 128, 256],
                       help="Patch sizes to extract")
    parser.add_argument("--max-patches", type=int, default=1000,
                       help="Maximum patches per scale")
    parser.add_argument("--single-image", type=Path,
                       help="Process single image instead of DZI")
    
    args = parser.parse_args()
    
    # Create indexer
    indexer = SpaceImageryIndexer(
        tiles_dir=args.tiles_dir,
        output_dir=args.output_dir,
        patch_sizes=args.patch_sizes,
        max_patches_per_scale=args.max_patches
    )
    
    success = False
    
    if args.single_image:
        # Process single image
        success = indexer.process_single_image(args.dataset_id, args.single_image)
    else:
        # Process DZI dataset
        dzi_path = args.tiles_dir / args.dataset_id / "info.dzi"
        if dzi_path.exists():
            success = indexer.process_dzi_dataset(args.dataset_id, dzi_path)
        else:
            logger.error(f"DZI file not found: {dzi_path}")
            return 1
    
    if success:
        logger.info("Index building completed successfully!")
        return 0
    else:
        logger.error("Index building failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
