# 🔍 CLIP Classification Troubleshooting

## Issue: Always Returns "Quasar" at 13% Confidence

### 🎯 **Most Likely Cause: Coordinate Mismatch**

The problem is likely that **annotation coordinates don't match tile coordinates**.

### The Problem Explained:

```
Your Deep Zoom Setup:
┌─────────────────────────────────────────┐
│  Full Image (virtual): 4096x4096        │
│                                         │
│  User draws box at: (1500, 1500)       │
│  ↓                                      │
│  But actual tiles are: 256x256 each    │
│  ↓                                      │
│  Trying to crop (1500, 1500) from      │
│  256x256 tile = FAILS or gets nothing  │
└─────────────────────────────────────────┘
```

**Result:** CLIP analyzes a blank/tiny region → low confidence → picks "quasar" randomly

---

## 🐛 Debugging Steps

### Step 1: Check the Debug Output

Look at the PowerShell window running AI service. When you create an annotation, you should see:

```
📷 Loading image from: C:\...\tiles\andromeda\0\0_0.jpg
📐 Image size: 256x256, Bbox: (1500, 1500, 200, 200)
                              ^^^^ PROBLEM! Bbox exceeds image size
✂️ Cropped region size: 0x0  ← Nothing to analyze!
🎯 Top 5 classifications:
   1. quasar: 13.2%         ← All similar low confidence
   2. empty space: 12.8%
   3. deep space background: 12.5%
   ...
```

### Step 2: Verify the Issue

Open a new PowerShell and test:
```powershell
# Test with coordinates that FIT in a 256x256 tile
Invoke-WebRequest -Uri "http://localhost:8001/classify?datasetId=andromeda&bbox=50,50,150,150" -Method POST

# vs coordinates that DON'T fit
Invoke-WebRequest -Uri "http://localhost:8001/classify?datasetId=andromeda&bbox=1500,1500,200,200" -Method POST
```

---

## ✅ Solutions

### **Solution 1: Use Actual Space Images** ⭐ RECOMMENDED

The generated sample tiles are just random noise. Use REAL astronomical images!

**Quick Fix:**
1. Download a real galaxy/nebula image from NASA
2. Place it in `infra/tiles/andromeda/`
3. Name it `image.jpg` or `source.jpg`

**Good sources:**
- Hubble: https://hubblesite.org/images
- NASA APOD: https://apod.nasa.gov/apod/
- ESA: https://www.esa.int/ESA_Multimedia/Images

**Example:**
```bash
# Download Andromeda galaxy image
curl https://example.com/andromeda.jpg -o infra/tiles/andromeda/source.jpg
```

---

### **Solution 2: Fix Coordinate Mapping**

Update the classify function to handle tile-based coordinates:

```python
# In apps/ai/app/main.py, replace the image loading section with:

# Calculate which tile contains this bbox
tile_size = 256
tile_col = x // tile_size
tile_row = y // tile_size
local_x = x % tile_size
local_y = y % tile_size

# Load the correct tile
tile_path = dataset_path / f"{tile_level}" / f"{tile_col}_{tile_row}.jpg"

if tile_path.exists():
    image = Image.open(tile_path).convert('RGB')
    # Crop using LOCAL coordinates
    cropped = image.crop((local_x, local_y, local_x + w, local_y + h))
else:
    # Fallback: use any available tile
    ...
```

---

### **Solution 3: Scale Coordinates**

If using generated tiles, scale down the annotation coordinates:

```python
# Add before loading image:
scale_factor = 256 / 4096  # tile_size / virtual_size
x = int(x * scale_factor)
y = int(y * scale_factor)
w = int(w * scale_factor)
h = int(h * scale_factor)
```

---

### **Solution 4: Create Better Sample Data**

Generate tiles from a real image:

```python
# infra/generate_real_tiles.py
from PIL import Image
import requests
from io import BytesIO

# Download real image
url = "https://hubblesite.org/contents/media/images/2019/01/4232-Image.jpg"
response = requests.get(url)
img = Image.open(BytesIO(response.content))

# Resize to 4096x4096
img = img.resize((4096, 4096), Image.Resampling.LANCZOS)

# Generate tiles
tile_size = 256
for level in range(3):
    for y in range(0, img.height, tile_size):
        for x in range(0, img.width, tile_size):
            tile = img.crop((x, y, x + tile_size, y + tile_size))
            tile.save(f"infra/tiles/andromeda/{level}/{x//tile_size}_{y//tile_size}.jpg")
```

---

## 🎯 Quick Test

### Test with Small Coordinates (should work):
```powershell
curl -X POST "http://localhost:8001/classify?datasetId=andromeda&bbox=50,50,100,100"
```

Expected: Higher confidence (~40-70%) with meaningful classification

### Test with Large Coordinates (will fail):
```powershell
curl -X POST "http://localhost:8001/classify?datasetId=andromeda&bbox=2000,2000,200,200"
```

Expected: Low confidence (~10-15%) because bbox exceeds tile size

---

## 🔬 Understanding the Confidence Scores

### What 13% means:
- CLIP is **uncertain**
- All categories have similar low scores
- Image doesn't clearly match any astronomical description
- Likely analyzing blank/noise/tiny region

### What you want to see:
```
🎯 Top 5 classifications:
   1. spiral galaxy: 67.3%      ← High confidence
   2. elliptical galaxy: 18.2%   ← Clear runner-up
   3. star cluster: 8.1%
   4. nebula: 3.2%
   5. deep space background: 2.1%
```

### Why CLIP struggles with generated tiles:
1. **Random noise** doesn't look like real astronomical objects
2. **No structure** → CLIP can't identify features
3. **Too small** → After cropping wrong coords, analyzing 0x0 or tiny region
4. **Not trained on noise** → CLIP was trained on real images

---

## 🚀 Immediate Action

**Check the AI service PowerShell window NOW:**

Look for these lines when you create an annotation:
```
📷 Loading image from: ...
📐 Image size: XXXxYYY, Bbox: (x,y,w,h)
✂️ Cropped region size: ...
```

**If cropped size is 0x0 or very small** → Coordinates don't match image!

---

## 💡 Best Practice for Testing

### Use a real image for meaningful results:

1. **Download:** 
   ```bash
   # Andromeda Galaxy (M31)
   curl "https://upload.wikimedia.org/wikipedia/commons/thumb/9/98/Andromeda_Galaxy_%28with_h-alpha%29.jpg/1280px-Andromeda_Galaxy_%28with_h-alpha%29.jpg" -o "C:\Users\miked\Desktop\NASA Space App Hackathon\space-hackathon\infra\tiles\andromeda\source.jpg"
   ```

2. **Test classification:**
   - Draw annotation on the galaxy core → should detect "spiral galaxy"
   - Draw on star field → should detect "star field" or "bright star"
   - Draw on dark region → should detect "deep space background"

3. **Confidence should be 40-80%** for real images

---

## 📋 Summary

| Symptom | Cause | Solution |
|---------|-------|----------|
| Always same result | Bad image data | Use real space images |
| Low confidence (~13%) | Analyzing noise/blank | Fix coordinates or use real images |
| 0x0 crop size | Coordinates mismatch | Scale coordinates or fix tile mapping |
| Works with small coords | Tile size limitation | Use Solution 1 or 2 |

**Bottom line:** The 13% confidence means CLIP is working but can't recognize what it's seeing. Fix the input image quality and coordinate mapping!
