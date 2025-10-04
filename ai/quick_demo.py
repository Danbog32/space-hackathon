#!/usr/bin/env python3
"""
Quick demo setup for Misha - builds index from simple image and starts service.
Run this to get started quickly!
"""

import sys
import subprocess
from pathlib import Path
from PIL import Image
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_demo_image():
    """Create a simple demo image with interesting features."""
    print("\n" + "="*60)
    print("STEP 1: Creating demo space image...")
    print("="*60)
    logger.info("Creating demo image...")
    
    # Create 2048x2048 image with space-like features
    size = 2048
    print(f"• Creating {size}x{size} pixel image...")
    img = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Add background gradient
    for i in range(size):
        for j in range(size):
            img[i, j] = [20, 20, 30]  # Dark blue background
    
    # Add some "stars" (bright spots)
    print("• Adding 200 stars...")
    np.random.seed(42)
    for _ in range(200):
        x = np.random.randint(0, size)
        y = np.random.randint(0, size)
        brightness = np.random.randint(200, 255)
        # Draw small circle for star
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if 0 <= x+dx < size and 0 <= y+dy < size:
                    if dx*dx + dy*dy <= 4:
                        img[y+dy, x+dx] = [brightness, brightness, brightness]
    
    # Add some "nebula" regions (colorful clouds)
    print("• Adding 5 colorful nebula regions...")
    for _ in range(5):
        cx = np.random.randint(200, size-200)
        cy = np.random.randint(200, size-200)
        radius = 150
        
        # Create circular gradient blob
        y_coords, x_coords = np.ogrid[:size, :size]
        distances = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
        blob = np.clip(255 * (1 - distances / radius), 0, 255).astype(np.uint8)
        
        # Add color
        color = np.random.choice([[255, 100, 100], [100, 100, 255], [100, 255, 100]])
        for c in range(3):
            img[:, :, c] = np.clip(img[:, :, c] + (blob * color[c] // 255), 0, 255)
    
    # Add some bright "galaxy core" regions
    print("• Adding 3 bright galaxy cores...")
    for _ in range(3):
        cx = np.random.randint(300, size-300)
        cy = np.random.randint(300, size-300)
        
        # Create bright center
        for r in range(0, 150, 10):
            brightness = int(255 * (1 - r/150))
            for angle in range(0, 360, 10):
                x = int(cx + r * np.cos(np.radians(angle)))
                y = int(cy + r * np.sin(np.radians(angle)))
                if 0 <= x < size and 0 <= y < size:
                    img[y, x] = [brightness, brightness, brightness]
    
    # Save image
    output_path = Path("data/demo_space.jpg")
    output_path.parent.mkdir(exist_ok=True)
    
    print("• Saving image...")
    pil_img = Image.fromarray(img)
    pil_img.save(output_path, quality=95)
    
    print(f"✅ Demo image created: {output_path}")
    print(f"   Size: {size}x{size} pixels")
    logger.info(f"✅ Demo image created: {output_path} ({size}x{size})")
    return output_path

def check_dependencies():
    """Check if all dependencies are installed."""
    print("\n" + "="*60)
    print("CHECKING DEPENDENCIES...")
    print("="*60)
    logger.info("Checking dependencies...")
    
    try:
        print("• Importing torch...")
        import torch
        print("• Importing open_clip...")
        import open_clip
        print("• Importing faiss...")
        import faiss
        print("• Importing numpy...")
        import numpy
        print("• Importing PIL...")
        from PIL import Image
        print("✅ All dependencies installed!")
        logger.info("✅ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("Run: pip install -r requirements.txt")
        return False

def build_index(image_path: Path):
    """Build FAISS index from demo image."""
    print("\n" + "="*60)
    print("STEP 2: Building FAISS Index")
    print("="*60)
    print("⏱️  This may take 2-5 minutes depending on your hardware...")
    print("    (Downloading CLIP model on first run: ~350MB)")
    print()
    logger.info("Building FAISS index...")
    logger.info("This may take 2-5 minutes depending on your hardware...")
    
    try:
        print("• Importing AI modules...")
        from models.clip_model import ClipEncoder
        from utils.patch_extractor import PatchExtractor
        from utils.faiss_helper import DatasetIndexManager
        import numpy as np
        
        # Initialize
        print("• Loading CLIP model (this may download ~350MB on first run)...")
        clip = ClipEncoder(device=None)  # Auto-detect
        device = clip.get_model_info()['device']
        print(f"✅ CLIP model loaded on: {device}")
        logger.info(f"CLIP loaded on: {device}")
        
        print("• Initializing patch extractor...")
        extractor = PatchExtractor(
            patch_sizes=[128, 256],  # Two scales for variety
            stride_ratios=[0.75],     # Some overlap
            quality_threshold=0.02,   # Lower threshold for demo
            max_patches_per_scale=300 # Limit for speed
        )
        
        print("• Initializing index manager...")
        manager = DatasetIndexManager(Path("data"))
        
        # Load image
        print(f"• Loading image: {image_path}")
        logger.info(f"Loading image: {image_path}")
        img = Image.open(image_path).convert("RGB")
        print(f"  Image size: {img.size}")
        logger.info(f"Image size: {img.size}")
        
        # Create index
        print("• Creating FAISS index...")
        embedding_dim = clip.get_embedding_dim()
        manager.create_dataset_index("demo", embedding_dim, index_type="flat")
        print(f"  Embedding dimension: {embedding_dim}")
        
        # Extract and encode patches
        print("• Extracting patches (this takes time)...")
        logger.info("Extracting patches...")
        patches = []
        metadata = []
        patch_count = 0
        
        for patch, meta in extractor.extract_patches(img):
            meta.update({
                'source_image': 'demo_space.jpg',
                'dataset_id': 'demo'
            })
            patches.append(patch)
            metadata.append(meta)
            patch_count += 1
            
            # Show progress every 50 patches
            if patch_count % 50 == 0:
                print(f"  Extracted {patch_count} patches so far...")
            
            # Process in batches
            if len(patches) >= 32:
                print(f"• Encoding batch of {len(patches)} patches with CLIP...")
                logger.info(f"Encoding batch of {len(patches)} patches...")
                embeddings = clip.encode_images_batch(patches)
                manager.add_vectors("demo", embeddings.numpy(), metadata)
                patches = []
                metadata = []
        
        # Process remaining
        if patches:
            print(f"• Encoding final batch of {len(patches)} patches...")
            logger.info(f"Encoding final batch of {len(patches)} patches...")
            embeddings = clip.encode_images_batch(patches)
            manager.add_vectors("demo", embeddings.numpy(), metadata)
        
        # Save
        print("• Saving index to disk...")
        manager.save_dataset("demo")
        
        info = manager.get_dataset_info("demo")
        print()
        print("✅ Index built successfully!")
        print(f"   Total patches: {info['num_vectors']}")
        print(f"   Embedding dim: {info['embedding_dim']}")
        print(f"   Index file: data/demo.faiss")
        logger.info(f"✅ Index built successfully!")
        logger.info(f"   Total patches: {info['num_vectors']}")
        logger.info(f"   Embedding dim: {info['embedding_dim']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Index building failed!")
        print(f"Error: {e}")
        logger.error(f"❌ Index building failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main setup and start."""
    print("\n" + "=" * 60)
    print("  🚀 Quick Demo Setup for AI Service")
    print("=" * 60)
    print()
    print("This script will:")
    print("  1. Check dependencies")
    print("  2. Create demo space image")
    print("  3. Build FAISS index with CLIP")
    print("  4. Start AI service")
    print()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies missing!")
        print("Run: cd ai && pip install -r requirements.txt")
        logger.error("Please install dependencies first: pip install -r requirements.txt")
        input("\nPress Enter to exit...")
        return 1
    
    # Create or use existing demo image
    demo_image = Path("data/demo_space.jpg")
    
    if not demo_image.exists():
        demo_image = create_demo_image()
    else:
        print("\n✅ Demo image already exists")
        print(f"   Using: {demo_image}")
        logger.info(f"Using existing demo image: {demo_image}")
    
    # Check if index already exists
    index_file = Path("data/demo.faiss")
    
    if index_file.exists():
        print("\n✅ Index already exists, skipping build")
        print("   (Delete data/demo.faiss to rebuild)")
        logger.info("✅ Index already exists, skipping build")
        logger.info("   (Delete data/demo.faiss to rebuild)")
    else:
        # Build index
        if not build_index(demo_image):
            print("\n❌ Failed to build index")
            logger.error("Failed to build index")
            input("\nPress Enter to exit...")
            return 1
    
    print()
    print("=" * 60)
    print("  ✅ Setup Complete!")
    print("=" * 60)
    print()
    print("STEP 3: Starting AI service...")
    print()
    print("📍 Service URL: http://localhost:8001")
    print()
    print("🧪 Test commands (in another terminal):")
    print('   curl "http://localhost:8001/health"')
    print('   curl "http://localhost:8001/search?q=bright%20star&dataset_id=demo&k=5"')
    print()
    print("   Or run: python test_quick.py")
    print()
    print("⚠️  Press Ctrl+C to stop the service")
    print("=" * 60)
    print()
    
    # Start the service
    try:
        print("🚀 Starting service...\n")
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n\n✅ Service stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Service failed to start: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

