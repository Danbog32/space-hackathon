#!/usr/bin/env python3
"""
SAM (Segment Anything Model) integration for assisted annotation masks.
This is a stretch goal implementation.
"""

import logging
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Optional, Tuple
import torch

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

logger = logging.getLogger(__name__)

class SAMIntegration:
    """Integration with Segment Anything Model for assisted annotation."""
    
    def __init__(self, model_type: str = "vit_b", device: Optional[str] = None):
        """
        Initialize SAM integration.
        
        Args:
            model_type: SAM model type ('vit_b', 'vit_l', 'vit_h')
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto-detection)
        """
        self.model_type = model_type
        self.device = self._detect_device(device)
        self.sam_model = None
        self.sam_predictor = None
        
        logger.info(f"Initializing SAM integration with {model_type} on {self.device}")
    
    def _detect_device(self, device: Optional[str]) -> str:
        """Auto-detect best available device."""
        if device:
            return device
            
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    def load_model(self) -> bool:
        """Load SAM model and predictor."""
        try:
            # Try to import SAM
            try:
                from segment_anything import sam_model_registry, SamPredictor
            except ImportError:
                logger.error("segment-anything not installed. Install with: pip install segment-anything")
                return False
            
            # Load model
            sam_checkpoint = self._get_checkpoint_path()
            if not sam_checkpoint.exists():
                logger.error(f"SAM checkpoint not found: {sam_checkpoint}")
                logger.info("Download SAM checkpoints from: https://github.com/facebookresearch/segment-anything#model-checkpoints")
                return False
            
            self.sam_model = sam_model_registry[self.model_type](checkpoint=str(sam_checkpoint))
            self.sam_model.to(device=self.device)
            self.sam_predictor = SamPredictor(self.sam_model)
            
            logger.info(f"SAM model loaded successfully: {self.model_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load SAM model: {e}")
            return False
    
    def _get_checkpoint_path(self) -> Path:
        """Get path to SAM checkpoint file."""
        checkpoints_dir = Path(__file__).parent / "checkpoints"
        checkpoints_dir.mkdir(exist_ok=True)
        
        checkpoint_map = {
            "vit_b": "sam_vit_b_01ec64.pth",
            "vit_l": "sam_vit_l_0b3195.pth", 
            "vit_h": "sam_vit_h_4b8939.pth"
        }
        
        return checkpoints_dir / checkpoint_map.get(self.model_type, "sam_vit_b_01ec64.pth")
    
    def segment_from_points(self, image: Image.Image, points: List[Tuple[int, int]], 
                          labels: List[int]) -> Optional[np.ndarray]:
        """
        Generate segmentation mask from point prompts.
        
        Args:
            image: PIL Image to segment
            points: List of (x, y) point coordinates
            labels: List of labels (1 for foreground, 0 for background)
            
        Returns:
            Segmentation mask as numpy array, or None if failed
        """
        if not self.sam_predictor:
            logger.error("SAM predictor not loaded")
            return None
        
        try:
            # Convert PIL to numpy
            image_array = np.array(image)
            
            # Set image for predictor
            self.sam_predictor.set_image(image_array)
            
            # Convert points to numpy arrays
            input_points = np.array(points)
            input_labels = np.array(labels)
            
            # Generate mask
            masks, scores, logits = self.sam_predictor.predict(
                point_coords=input_points,
                point_labels=input_labels,
                multimask_output=True
            )
            
            # Return best mask (highest score)
            best_mask_idx = np.argmax(scores)
            best_mask = masks[best_mask_idx]
            
            logger.info(f"Generated segmentation mask with score: {scores[best_mask_idx]:.3f}")
            return best_mask.astype(np.uint8) * 255
            
        except Exception as e:
            logger.error(f"Error generating segmentation: {e}")
            return None
    
    def segment_from_bbox(self, image: Image.Image, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Generate segmentation mask from bounding box.
        
        Args:
            image: PIL Image to segment
            bbox: Bounding box as (x1, y1, x2, y2)
            
        Returns:
            Segmentation mask as numpy array, or None if failed
        """
        if not self.sam_predictor:
            logger.error("SAM predictor not loaded")
            return None
        
        try:
            # Convert PIL to numpy
            image_array = np.array(image)
            
            # Set image for predictor
            self.sam_predictor.set_image(image_array)
            
            # Generate mask from bbox
            masks, scores, logits = self.sam_predictor.predict(
                box=np.array(bbox),
                multimask_output=True
            )
            
            # Return best mask (highest score)
            best_mask_idx = np.argmax(scores)
            best_mask = masks[best_mask_idx]
            
            logger.info(f"Generated segmentation mask from bbox with score: {scores[best_mask_idx]:.3f}")
            return best_mask.astype(np.uint8) * 255
            
        except Exception as e:
            logger.error(f"Error generating segmentation from bbox: {e}")
            return None
    
    def segment_from_combined(self, image: Image.Image, 
                            points: List[Tuple[int, int]], 
                            labels: List[int],
                            bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Generate segmentation mask from combined point and bbox prompts.
        
        Args:
            image: PIL Image to segment
            points: List of (x, y) point coordinates
            labels: List of labels (1 for foreground, 0 for background)
            bbox: Optional bounding box as (x1, y1, x2, y2)
            
        Returns:
            Segmentation mask as numpy array, or None if failed
        """
        if not self.sam_predictor:
            logger.error("SAM predictor not loaded")
            return None
        
        try:
            # Convert PIL to numpy
            image_array = np.array(image)
            
            # Set image for predictor
            self.sam_predictor.set_image(image_array)
            
            # Prepare inputs
            input_points = np.array(points) if points else None
            input_labels = np.array(labels) if labels else None
            input_box = np.array(bbox) if bbox else None
            
            # Generate mask
            masks, scores, logits = self.sam_predictor.predict(
                point_coords=input_points,
                point_labels=input_labels,
                box=input_box,
                multimask_output=True
            )
            
            # Return best mask (highest score)
            best_mask_idx = np.argmax(scores)
            best_mask = masks[best_mask_idx]
            
            logger.info(f"Generated segmentation mask with combined prompts, score: {scores[best_mask_idx]:.3f}")
            return best_mask.astype(np.uint8) * 255
            
        except Exception as e:
            logger.error(f"Error generating segmentation with combined prompts: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded SAM model."""
        return {
            "model_type": self.model_type,
            "device": self.device,
            "loaded": self.sam_predictor is not None,
            "checkpoint_path": str(self._get_checkpoint_path())
        }

# Global SAM instance
_sam_instance = None

def get_sam_instance() -> Optional[SAMIntegration]:
    """Get global SAM instance."""
    global _sam_instance
    if _sam_instance is None:
        _sam_instance = SAMIntegration()
        if not _sam_instance.load_model():
            _sam_instance = None
    return _sam_instance

def segment_patch(patch: Image.Image, points: List[Tuple[int, int]], 
                 labels: List[int], bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
    """
    Convenience function to segment a patch.
    
    Args:
        patch: PIL Image patch to segment
        points: List of (x, y) point coordinates
        labels: List of labels (1 for foreground, 0 for background)
        bbox: Optional bounding box as (x1, y1, x2, y2)
        
    Returns:
        Segmentation mask as numpy array, or None if failed
    """
    sam = get_sam_instance()
    if not sam:
        logger.warning("SAM not available")
        return None
    
    if bbox:
        return sam.segment_from_combined(patch, points, labels, bbox)
    elif points:
        return sam.segment_from_points(patch, points, labels)
    else:
        logger.warning("No points or bbox provided for segmentation")
        return None
