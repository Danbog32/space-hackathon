from PIL import Image
import numpy as np
from pathlib import Path
import logging
from typing import Iterator, Tuple, List, Optional, Dict, Any
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Some features will be disabled.")

try:
    from skimage.feature import corner_harris, corner_peaks
    from skimage.filters import gaussian
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False
    print("Warning: scikit-image not available. Some features will be disabled.")
import json

logger = logging.getLogger(__name__)

class PatchExtractor:
    """Advanced patch extraction with multi-scale sampling and quality filtering."""
    
    def __init__(self, patch_sizes: List[int] = [64, 128, 256], 
                 stride_ratios: List[float] = [0.5, 0.75, 1.0],
                 quality_threshold: float = 0.1,
                 max_patches_per_scale: Optional[int] = None):
        """
        Initialize patch extractor with multi-scale strategy.
        
        Args:
            patch_sizes: List of patch sizes to extract
            stride_ratios: List of stride ratios (relative to patch size)
            quality_threshold: Minimum variance threshold for patch quality
            max_patches_per_scale: Maximum patches per scale (None for unlimited)
        """
        self.patch_sizes = sorted(patch_sizes)
        self.stride_ratios = stride_ratios
        self.quality_threshold = quality_threshold
        self.max_patches_per_scale = max_patches_per_scale
        
    def load_or_make_demo_image(self, path: Path, size=(4096, 4096)) -> Image.Image:
        """Load existing image or create demo image with space-like patterns."""
        if not path.exists():
            logger.info(f"Creating demo image at {path}")
            w, h = size
            
            # Create more realistic space-like patterns
            x = np.linspace(0, 2*np.pi, w)
            y = np.linspace(0, 2*np.pi, h)
            xv, yv = np.meshgrid(x, y)
            
            # Galaxy spiral pattern
            spiral = np.sin(xv + yv * 0.5) * np.exp(-(xv**2 + yv**2) / 4)
            
            # Star field
            stars = np.random.default_rng(42).random((h, w)) > 0.95
            star_field = stars.astype(float) * 255
            
            # Dust clouds
            dust = np.sin(xv * 2) * np.cos(yv * 2) * 50
            
            # Combine patterns
            base = (spiral * 100 + dust + star_field).astype(np.uint8)
            base = np.clip(base, 0, 255)
            
            img = Image.fromarray(base, mode='L').convert("RGB")
            img.save(path)
            logger.info(f"Demo image saved: {path}")
        
        return Image.open(path).convert("RGB")
    
    def extract_patches(self, img: Image.Image) -> Iterator[Tuple[Image.Image, Dict[str, Any]]]:
        """
        Extract multi-scale patches with quality filtering.
        
        Args:
            img: PIL Image to extract patches from
            
        Yields:
            Tuple of (patch_image, metadata_dict)
        """
        img_array = np.array(img)
        total_patches = 0
        
        for patch_size in self.patch_sizes:
            logger.info(f"Extracting {patch_size}x{patch_size} patches...")
            patches_count = 0
            
            for stride_ratio in self.stride_ratios:
                stride = int(patch_size * stride_ratio)
                patches = self._extract_patches_at_scale(
                    img, img_array, patch_size, stride
                )
                
                for patch, metadata in patches:
                    if self.max_patches_per_scale and patches_count >= self.max_patches_per_scale:
                        break
                    
                    if self._is_quality_patch(patch):
                        metadata.update({
                            'patch_size': patch_size,
                            'stride': stride,
                            'stride_ratio': stride_ratio,
                            'scale': patch_size / min(self.patch_sizes)
                        })
                        yield patch, metadata
                        patches_count += 1
                        total_patches += 1
                
                if self.max_patches_per_scale and patches_count >= self.max_patches_per_scale:
                    break
            
            logger.info(f"Extracted {patches_count} patches at scale {patch_size}x{patch_size}")
        
        logger.info(f"Total patches extracted: {total_patches}")
    
    def _extract_patches_at_scale(self, img: Image.Image, img_array: np.ndarray, 
                                 patch_size: int, stride: int) -> Iterator[Tuple[Image.Image, Dict[str, Any]]]:
        """Extract patches at a specific scale."""
        w, h = img.size
        
        for y in range(0, h - patch_size + 1, stride):
            for x in range(0, w - patch_size + 1, stride):
                # Extract patch
                patch = img.crop((x, y, x + patch_size, y + patch_size))
                
                # Calculate metadata
                metadata = {
                    'bbox': [x, y, patch_size, patch_size],
                    'center': [x + patch_size // 2, y + patch_size // 2],
                    'area': patch_size * patch_size,
                    'aspect_ratio': 1.0,  # Square patches
                    'position': {
                        'x': x,
                        'y': y,
                        'level': self._calculate_zoom_level(patch_size, w, h)
                    }
                }
                
                yield patch, metadata
    
    def _is_quality_patch(self, patch: Image.Image) -> bool:
        """Check if patch meets quality criteria."""
        try:
            # Convert to grayscale for analysis
            gray = patch.convert('L')
            img_array = np.array(gray)
            
            # Check variance (avoid uniform patches)
            variance = np.var(img_array)
            if variance < self.quality_threshold * 255**2:
                return False
            
            # Check for sufficient edge content (only if OpenCV is available)
            if CV2_AVAILABLE:
                edges = cv2.Canny(img_array, 50, 150)
                edge_ratio = np.sum(edges > 0) / edges.size
                if edge_ratio < 0.01:  # Less than 1% edge pixels
                    return False
            
            return True
        except Exception as e:
            logger.warning(f"Error checking patch quality: {e}")
            return True  # Default to keeping patch if check fails
    
    def _calculate_zoom_level(self, patch_size: int, img_width: int, img_height: int) -> int:
        """Calculate approximate zoom level for patch."""
        max_dim = max(img_width, img_height)
        return int(np.log2(max_dim / patch_size))
    
    def extract_interest_points(self, img: Image.Image, patch_size: int = 128) -> List[Dict[str, Any]]:
        """
        Extract patches centered on interest points (corners, edges).
        
        Args:
            img: PIL Image to analyze
            patch_size: Size of patches to extract around interest points
            
        Returns:
            List of patch metadata dictionaries
        """
        if not SKIMAGE_AVAILABLE:
            logger.warning("scikit-image not available, skipping interest point extraction")
            return []
            
        try:
            # Convert to grayscale
            gray = np.array(img.convert('L'))
            
            # Detect corners using Harris corner detection
            corners = corner_peaks(corner_harris(gray), min_distance=patch_size//2)
            
            patches = []
            w, h = img.size
            half_size = patch_size // 2
            
            for y, x in corners:
                # Ensure patch fits within image bounds
                x1 = max(0, x - half_size)
                y1 = max(0, y - half_size)
                x2 = min(w, x + half_size)
                y2 = min(h, y + half_size)
                
                # Adjust if patch would be too small
                if x2 - x1 < patch_size or y2 - y1 < patch_size:
                    continue
                
                patch = img.crop((x1, y1, x2, y2))
                if patch.size == (patch_size, patch_size):
                    metadata = {
                        'bbox': [x1, y1, patch_size, patch_size],
                        'center': [x, y],
                        'type': 'interest_point',
                        'patch_size': patch_size,
                        'harris_response': corner_harris(gray)[y, x]
                    }
                    patches.append((patch, metadata))
            
            logger.info(f"Extracted {len(patches)} interest point patches")
            return patches
            
        except Exception as e:
            logger.error(f"Error extracting interest points: {e}")
            return []
    
    def extract_hierarchical_patches(self, img: Image.Image, 
                                   levels: List[int] = [0, 1, 2]) -> Iterator[Tuple[Image.Image, Dict[str, Any]]]:
        """
        Extract patches at different zoom levels (hierarchical sampling).
        
        Args:
            img: PIL Image to process
            levels: List of zoom levels to sample
            
        Yields:
            Tuple of (patch_image, metadata_dict)
        """
        w, h = img.size
        max_level = int(np.log2(min(w, h) / min(self.patch_sizes)))
        
        for level in levels:
            if level > max_level:
                continue
                
            # Calculate scale factor for this level
            scale_factor = 2 ** level
            scaled_size = (w // scale_factor, h // scale_factor)
            
            # Resize image for this level
            scaled_img = img.resize(scaled_size, Image.Resampling.LANCZOS)
            
            # Extract patches at this scale
            for patch_size in self.patch_sizes:
                stride = patch_size // 2  # Overlapping patches
                
                for y in range(0, scaled_size[1] - patch_size + 1, stride):
                    for x in range(0, scaled_size[0] - patch_size + 1, stride):
                        patch = scaled_img.crop((x, y, x + patch_size, y + patch_size))
                        
                        # Scale coordinates back to original image
                        orig_x = x * scale_factor
                        orig_y = y * scale_factor
                        orig_patch_size = patch_size * scale_factor
                        
                        metadata = {
                            'bbox': [orig_x, orig_y, orig_patch_size, orig_patch_size],
                            'level': level,
                            'scale_factor': scale_factor,
                            'patch_size': patch_size,
                            'type': 'hierarchical'
                        }
                        
                        if self._is_quality_patch(patch):
                            yield patch, metadata

# Backward compatibility functions
def load_or_make_demo_image(path: Path, size=(4096, 4096)) -> Image.Image:
    """Backward compatibility function."""
    extractor = PatchExtractor()
    return extractor.load_or_make_demo_image(path, size)

def extract_patches(img: Image.Image, patch=128, stride=128) -> Iterator[Tuple[Image.Image, List[int]]]:
    """Backward compatibility function."""
    extractor = PatchExtractor(patch_sizes=[patch], stride_ratios=[stride/patch])
    for patch_img, metadata in extractor.extract_patches(img):
        yield patch_img, metadata['bbox']