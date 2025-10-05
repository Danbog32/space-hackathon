import torch
import open_clip
from PIL import Image
import logging
from typing import Optional, Union, List
import os

logger = logging.getLogger(__name__)

class ClipEncoder:
    def __init__(self, device: Optional[str] = None, model_name: str = "ViT-B-32", 
                 pretrained: str = "laion2b_s34b_b79k", cache_dir: Optional[str] = None):
        """
        Enhanced CLIP encoder with GPU detection, model caching, and error handling.
        
        Args:
            device: Device to use ('cpu', 'cuda', 'mps', or None for auto-detection)
            model_name: CLIP model variant ('ViT-B-32', 'ViT-L-14', 'ViT-H-14')
            pretrained: Pretrained weights identifier
            cache_dir: Directory to cache models (defaults to ~/.cache/clip)
        """
        self.device = self._detect_device(device)
        self.model_name = model_name
        self.pretrained = pretrained
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/clip")
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Initializing CLIP model: {model_name} on {self.device}")
        
        try:
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(
                model_name, 
                pretrained=pretrained, 
                device=self.device,
                cache_dir=self.cache_dir
            )
            self.tokenizer = open_clip.get_tokenizer(model_name)
            self.model.eval()
            logger.info(f"Successfully loaded CLIP model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise RuntimeError(f"Could not load CLIP model {model_name}: {e}")
    
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
    
    @torch.inference_mode()
    def encode_image(self, pil_image: Image.Image) -> torch.Tensor:
        """
        Encode a PIL image to CLIP embedding.
        
        Args:
            pil_image: PIL Image to encode
            
        Returns:
            Normalized embedding tensor
        """
        try:
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            img = self.preprocess(pil_image).unsqueeze(0).to(self.device)
            feats = self.model.encode_image(img)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            return feats.squeeze(0).cpu()
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            raise
    
    @torch.inference_mode()
    def encode_text(self, text: str) -> torch.Tensor:
        """
        Encode text to CLIP embedding.
        
        Args:
            text: Text string to encode
            
        Returns:
            Normalized embedding tensor
        """
        try:
            tokens = self.tokenizer([text])
            tokens = tokens.to(self.device)
            feats = self.model.encode_text(tokens)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            return feats.squeeze(0).cpu()
        except Exception as e:
            logger.error(f"Error encoding text '{text}': {e}")
            raise
    
    @torch.inference_mode()
    def encode_images_batch(self, pil_images: List[Image.Image]) -> torch.Tensor:
        """
        Encode multiple images in batch for efficiency.
        
        Args:
            pil_images: List of PIL Images to encode
            
        Returns:
            Batch of normalized embeddings
        """
        try:
            # Preprocess all images
            processed_images = []
            for img in pil_images:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                processed_images.append(self.preprocess(img))
            
            # Stack and move to device
            batch = torch.stack(processed_images).to(self.device)
            
            # Encode batch
            feats = self.model.encode_image(batch)
            feats = feats / feats.norm(dim=-1, keepdim=True)
            return feats.cpu()
        except Exception as e:
            logger.error(f"Error encoding image batch: {e}")
            raise
    
    def get_embedding_dim(self) -> int:
        """Get the dimension of the embedding space."""
        return self.model.visual.output_dim
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "pretrained": self.pretrained,
            "device": self.device,
            "embedding_dim": self.get_embedding_dim(),
            "cache_dir": self.cache_dir
        }
