"""Stub CLIP implementation for systems without GPU/CLIP."""

import hashlib
import numpy as np
from typing import List


class StubCLIP:
    """
    Stub CLIP implementation that generates deterministic random vectors.
    Allows the demo to work without actual CLIP models.
    """

    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        print("Using stub CLIP implementation (no real AI search)")

    def encode_text(self, text: str) -> np.ndarray:
        """Generate deterministic embedding from text."""
        # Use hash of text to generate deterministic random vector
        hash_bytes = hashlib.sha256(text.encode()).digest()
        seed = int.from_bytes(hash_bytes[:4], "big")
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self.embedding_dim)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)

    def encode_image(self, image_path: str, x: int, y: int) -> np.ndarray:
        """Generate deterministic embedding from image coordinates."""
        # Use hash of coordinates to generate deterministic random vector
        coord_string = f"{image_path}_{x}_{y}"
        hash_bytes = hashlib.sha256(coord_string.encode()).digest()
        seed = int.from_bytes(hash_bytes[:4], "big")
        rng = np.random.RandomState(seed)
        embedding = rng.randn(self.embedding_dim)
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.astype(np.float32)

    def encode_batch(self, items: List[tuple]) -> np.ndarray:
        """Encode multiple items."""
        embeddings = []
        for item in items:
            if isinstance(item, str):
                embeddings.append(self.encode_text(item))
            else:
                embeddings.append(self.encode_image(*item))
        return np.array(embeddings)


def create_clip_model():
    """Create CLIP model or stub."""
    from app.config import CLIP_AVAILABLE

    if CLIP_AVAILABLE:
        try:
            import open_clip
            import torch

            model, _, preprocess = open_clip.create_model_and_transforms(
                "ViT-B-32", pretrained="openai"
            )
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device)
            model.eval()

            class RealCLIP:
                def __init__(self, model, preprocess, device):
                    self.model = model
                    self.preprocess = preprocess
                    self.device = device

                def encode_text(self, text: str) -> np.ndarray:
                    with torch.no_grad():
                        text_token = open_clip.tokenize([text]).to(self.device)
                        text_features = self.model.encode_text(text_token)
                        text_features /= text_features.norm(dim=-1, keepdim=True)
                        return text_features.cpu().numpy()[0]

                def encode_image(self, image_path: str, x: int, y: int) -> np.ndarray:
                    from PIL import Image

                    # Load and crop image patch
                    img = Image.open(image_path)
                    patch = img.crop((x, y, x + 256, y + 256))
                    patch_tensor = self.preprocess(patch).unsqueeze(0).to(self.device)

                    with torch.no_grad():
                        image_features = self.model.encode_image(patch_tensor)
                        image_features /= image_features.norm(dim=-1, keepdim=True)
                        return image_features.cpu().numpy()[0]

            return RealCLIP(model, preprocess, device)
        except Exception as e:
            print(f"Failed to load CLIP model: {e}")
            return StubCLIP()
    else:
        return StubCLIP()

