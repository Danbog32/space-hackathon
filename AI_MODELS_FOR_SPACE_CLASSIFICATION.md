# 🤖 AI Models for Space Image Classification

## Current Implementation Status

### ❌ **No Real Model is Currently Used**

**Your annotation tool currently uses:**
- **Method:** `random.choice()` from Python's random module
- **File:** `apps/ai/app/main.py` lines 106-145
- **How it works:** Randomly picks one of 8 predefined categories

```python
# Current Implementation (MOCK)
object_types = [
    "galaxy", "nebula", "star", "star cluster", 
    "supernova", "planet", "black hole", "quasar"
]
primary = random.choice(object_types)  # ← Just random selection!
confidence = random.uniform(0.75, 0.95)  # ← Fake confidence
```

### ✅ **Yes, Limited to Preselected List**

Currently, it can **ONLY** classify into these 8 categories:
1. galaxy
2. nebula
3. star
4. star cluster
5. supernova
6. planet
7. black hole
8. quasar

**Limitations:**
- No actual image analysis
- Cannot detect new/unknown objects
- Confidence scores are meaningless (random)
- No real AI/ML involved

---

## 🌟 Recommended Free Models for Space Classification

### **Option 1: CLIP (OpenAI) - Best for Flexibility** ⭐ RECOMMENDED

**What it is:**
- Vision-Language model that understands images and text together
- Can classify ANY astronomical object without pre-training on astronomy data
- Already partially integrated in your codebase!

**Why it's great for astronomy:**
- Zero-shot classification (works without astronomy-specific training)
- Natural language queries: "a spiral galaxy", "a red supergiant star"
- Can handle any object type, not just predefined list
- Works with any image resolution

**Implementation:**
```python
# Already in your requirements.txt (commented out)
# open-clip-torch==2.23.0
# torch==2.1.2

# File: apps/ai/app/clip_stub.py already has the structure!
```

**Pretrained Weights:**
- `ViT-B-32` (Best balance) - 354MB
- `ViT-L-14` (Most accurate) - 890MB
- `ViT-B-16` (Faster) - 354MB

**GitHub:** https://github.com/mlfoundations/open_clip
**License:** MIT (Free for commercial use)

**Pros:**
- ✅ Works out of the box
- ✅ No astronomy training needed
- ✅ Flexible - add new categories anytime
- ✅ Your code already supports it!

**Cons:**
- ❌ Requires 2-4GB RAM
- ❌ Slower without GPU (~2-5 seconds per image)

---

### **Option 2: ResNet-50 + Fine-tuning on Galaxy Zoo**

**What it is:**
- CNN architecture pretrained on ImageNet
- Can be fine-tuned on astronomical datasets like Galaxy Zoo

**Datasets for training:**
- **Galaxy Zoo** - 900,000+ galaxy images with classifications
- **SDSS (Sloan Digital Sky Survey)** - Millions of celestial objects
- **Hubble Legacy Archive** - High-quality space images

**Implementation:**
```python
from torchvision.models import resnet50
import torch

model = resnet50(pretrained=True)
# Fine-tune on your astronomy data
```

**GitHub Examples:**
- https://github.com/zooniverse/decals (Galaxy Zoo ML)
- https://github.com/dr-rodriguez/AstroML (Astronomy ML examples)

**Pros:**
- ✅ Highly accurate for galaxies
- ✅ Fast inference
- ✅ Well-documented

**Cons:**
- ❌ Needs training on astronomy data
- ❌ Fixed categories (requires retraining to add new ones)
- ❌ Requires labeled dataset

---

### **Option 3: EfficientNet + Transfer Learning**

**What it is:**
- Modern CNN architecture that's efficient and accurate
- Good for resource-constrained environments

**Models:**
- EfficientNet-B0 (Smallest) - 5.3M parameters
- EfficientNet-B3 (Balanced) - 12M parameters
- EfficientNet-B7 (Most accurate) - 66M parameters

**Implementation:**
```python
from efficientnet_pytorch import EfficientNet

model = EfficientNet.from_pretrained('efficientnet-b3')
# Fine-tune on astronomy images
```

**Pros:**
- ✅ Faster than ResNet
- ✅ Better accuracy with fewer parameters
- ✅ Works on CPU

**Cons:**
- ❌ Still needs astronomy fine-tuning
- ❌ Fixed categories

---

### **Option 4: AstroNN (Astronomy-Specific)**

**What it is:**
- Deep learning package specifically for astronomy
- Built on top of Keras/TensorFlow
- Pre-trained models for stellar classification

**GitHub:** https://github.com/henrysky/astroNN
**Documentation:** https://astronn.readthedocs.io/

**Features:**
- Spectral classification
- Stellar parameter estimation
- Galaxy morphology classification

**Pros:**
- ✅ Purpose-built for astronomy
- ✅ Includes pretrained models
- ✅ Active development

**Cons:**
- ❌ More focused on spectral data than images
- ❌ Steeper learning curve

---

### **Option 5: Vision Transformer (ViT) - Most Modern**

**What it is:**
- Transformer architecture adapted for vision
- State-of-the-art performance on image classification

**Hugging Face Models:**
- `google/vit-base-patch16-224` - 86M parameters
- `google/vit-large-patch16-224` - 304M parameters

**Implementation:**
```python
from transformers import ViTForImageClassification, ViTImageProcessor

processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
model = ViTForImageClassification.from_pretrained('google/vit-base-patch16-224')
```

**Pros:**
- ✅ State-of-the-art accuracy
- ✅ Good with limited data (with transfer learning)
- ✅ Easy to use with Hugging Face

**Cons:**
- ❌ Requires more compute than CNNs
- ❌ Needs fine-tuning for astronomy

---

## 📊 Model Comparison for Your Use Case

| Model | Accuracy | Speed | Setup Difficulty | Best For |
|-------|----------|-------|------------------|----------|
| **CLIP (ViT-B-32)** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Quick start, flexibility** |
| ResNet-50 + Fine-tune | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | High accuracy with training |
| EfficientNet-B3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | Resource efficiency |
| AstroNN | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | Astronomy-specific tasks |
| ViT (Google) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | State-of-the-art results |

---

## 🚀 Quick Implementation Guide - CLIP (Recommended)

### Step 1: Install Dependencies

```bash
# In apps/ai directory
pip install open-clip-torch torch torchvision pillow
```

### Step 2: Update your AI service

```python
# apps/ai/app/main.py

import torch
import open_clip
from PIL import Image

# Load model once at startup
model, _, preprocess = open_clip.create_model_and_transforms(
    'ViT-B-32', 
    pretrained='openai'
)
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)
model.eval()

@app.post("/classify")
async def classify_region(
    datasetId: str = Query(...),
    bbox: str = Query(...)
):
    x, y, w, h = map(int, bbox.split(','))
    
    # Load and crop image region
    image_path = f"path/to/dataset/{datasetId}/image.jpg"
    image = Image.open(image_path).crop((x, y, x+w, y+h))
    image_tensor = preprocess(image).unsqueeze(0).to(device)
    
    # Define astronomical object types (expandable!)
    categories = [
        "a spiral galaxy",
        "an elliptical galaxy", 
        "a nebula",
        "a star cluster",
        "a bright star",
        "a supernova",
        "a planet",
        "a black hole",
        "a quasar",
        "deep space background"
    ]
    
    # Tokenize text
    text_tokens = open_clip.tokenize(categories).to(device)
    
    # Get predictions
    with torch.no_grad():
        image_features = model.encode_image(image_tensor)
        text_features = model.encode_text(text_tokens)
        
        # Normalize
        image_features /= image_features.norm(dim=-1, keepdim=True)
        text_features /= text_features.norm(dim=-1, keepdim=True)
        
        # Calculate similarity (cosine similarity)
        similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        probs = similarity[0].cpu().numpy()
    
    # Format results
    classifications = [
        {"type": cat.replace("a ", "").replace("an ", ""), 
         "confidence": float(prob),
         "rank": i+1}
        for i, (cat, prob) in enumerate(sorted(
            zip(categories, probs), 
            key=lambda x: x[1], 
            reverse=True
        ))
    ]
    
    return {
        "primary_classification": classifications[0]["type"],
        "confidence": classifications[0]["confidence"],
        "all_classifications": classifications[:5],
        "bbox": [x, y, w, h]
    }
```

### Step 3: Test It

```bash
# Restart your AI service
# The classification will now use real CLIP model!
```

---

## 🎯 Expanding Beyond 8 Categories

With CLIP, you can easily add more categories without retraining:

```python
categories = [
    # Galaxies
    "a spiral galaxy",
    "an elliptical galaxy",
    "an irregular galaxy",
    "a barred spiral galaxy",
    
    # Stars
    "a red giant star",
    "a blue supergiant star",
    "a white dwarf",
    "a binary star system",
    
    # Nebulae
    "a planetary nebula",
    "an emission nebula",
    "a reflection nebula",
    "a dark nebula",
    
    # Clusters
    "a globular cluster",
    "an open star cluster",
    
    # Exotic Objects
    "a supernova remnant",
    "a pulsar",
    "a black hole accretion disk",
    "a quasar",
    "a gamma-ray burst",
    
    # Other
    "a planet",
    "a moon",
    "an asteroid",
    "a comet",
    "cosmic dust",
    "gravitational lensing",
    "deep space background"
]
```

**No retraining needed!** Just add to the list.

---

## 💾 Pre-trained Astronomy Datasets

If you want to fine-tune models:

1. **Galaxy Zoo** - https://www.galaxyzoo.org/
   - 900,000+ galaxy images with morphology labels
   - Free for research

2. **SDSS DR17** - https://www.sdss.org/
   - Millions of celestial objects
   - Spectral and imaging data

3. **Hubble Legacy Archive** - https://hla.stsci.edu/
   - High-resolution space telescope images

4. **PanSTARRS** - https://panstarrs.stsci.edu/
   - 3 billion astronomical sources

5. **ESO Archive** - https://archive.eso.org/
   - European Southern Observatory images

---

## 🔧 System Requirements

### For CLIP (ViT-B-32):
- **CPU only:** 4GB RAM, ~2-5 seconds per classification
- **With GPU:** 4GB VRAM, ~50-200ms per classification
- **Disk:** 400MB for model weights

### For ResNet-50:
- **CPU only:** 2GB RAM, ~100-500ms per classification
- **With GPU:** 2GB VRAM, ~10-50ms per classification
- **Disk:** 100MB for model weights

---

## 📖 Resources

- **CLIP Paper:** https://arxiv.org/abs/2103.00020
- **Open CLIP:** https://github.com/mlfoundations/open_clip
- **Hugging Face Models:** https://huggingface.co/models?pipeline_tag=image-classification
- **AstroML:** https://www.astroml.org/
- **Galaxy Zoo Data:** https://data.galaxyzoo.org/

---

## ✅ Recommendation Summary

**For your hackathon project:**

1. **Start with CLIP ViT-B-32** (Easiest, already in your code structure)
   - Uncomment lines in `apps/ai/requirements.txt`
   - Update `apps/ai/app/main.py` with real CLIP code
   - Test immediately - works out of the box!

2. **If you need more accuracy later:**
   - Fine-tune ResNet-50 on Galaxy Zoo dataset
   - Takes a few hours to train
   - Much faster inference

3. **For production:**
   - Use CLIP for flexibility + ResNet for known categories
   - Best of both worlds

**Your current limitation is NOT the predefined list - it's the lack of any real AI model!** CLIP will fix both issues at once.
