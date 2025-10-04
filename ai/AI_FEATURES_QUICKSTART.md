# 🚀 Quick Start: AI Object Classification & Detection

## Overview

Two NEW AI features have been integrated into the space-hackathon platform:

1. **🔬 Object Classification** - Automatically identify what's in an annotated region
2. **🎯 Object Detection** - Find ALL instances of a specific object type

---

## Prerequisites

- AI service running on port 8001
- API backend running on port 8000
- Frontend running on port 3000

---

## Feature 1: Object Classification

### What it does
When you draw a rectangle annotation, the AI automatically tells you what astronomical object is in that region.

### How to use

1. **Start the platform**
   ```bash
   # Terminal 1: AI Service
   cd ai
   python simple_app.py
   
   # Terminal 2: API Backend
   cd apps/api
   python -m uvicorn app.main:app --reload --port 8000
   
   # Terminal 3: Frontend
   cd apps/web
   npm run dev
   ```

2. **Open your browser**
   - Navigate to http://localhost:3000
   - Select a dataset (e.g., "Andromeda Galaxy")

3. **Create an annotation with AI classification**
   - Click the "Rectangle + AI Classify" button
   - Click once on the image to start the rectangle
   - Click again to complete the rectangle
   - **BOOM!** A popup appears showing:
     - Primary classification (e.g., "galaxy")
     - Confidence score (e.g., 87%)
     - Alternative possibilities

4. **The popup auto-closes after 5 seconds**

### API Example
```bash
# Classify a region
curl -X POST "http://localhost:8000/classify?datasetId=andromeda&bbox=512,256,128,128"

# Response:
{
  "primary_classification": "galaxy",
  "confidence": 0.87,
  "all_classifications": [
    {"type": "galaxy", "confidence": 0.87},
    {"type": "nebula", "confidence": 0.09},
    {"type": "star cluster", "confidence": 0.04}
  ]
}
```

---

## Feature 2: Object Detection

### What it does
Finds and pinpoints ALL instances of a specific astronomical object type across the entire image.

### How to use

1. **Navigate to a dataset** in the platform

2. **Use the Object Detector panel**
   - Type an object name (e.g., "galaxy")
   - Or click a quick-select button:
     - galaxy
     - star
     - nebula
     - star cluster
     - planet
     - moon crater

3. **Adjust confidence threshold**
   - Slide the threshold control (default 60%)
   - Lower = more results, less accurate
   - Higher = fewer results, more accurate

4. **Click "Detect Objects"**

5. **See results!**
   - All detections appear as pins on the image
   - Results panel shows count (e.g., "Found 15 galaxies")
   - Each result shows confidence score and location
   - Click any result to fly to that location

### API Example
```bash
# Detect all galaxies with 60%+ confidence
curl "http://localhost:8000/detect?q=galaxy&datasetId=andromeda&confidence_threshold=0.6&max_results=50"

# Response:
{
  "object_type": "galaxy",
  "detections": [
    {
      "id": 42,
      "bbox": [512, 256, 128, 128],
      "confidence": 0.92
    },
    {
      "id": 87,
      "bbox": [1024, 512, 96, 96],
      "confidence": 0.85
    }
    // ... more detections
  ],
  "total_found": 15
}
```

---

## Common Object Types to Try

### Astronomical Objects
- `galaxy` - Detect galaxies
- `spiral galaxy` - Detect spiral galaxies specifically
- `elliptical galaxy` - Detect elliptical galaxies
- `star` - Detect individual stars
- `star cluster` - Detect star clusters
- `nebula` - Detect nebulae
- `planetary nebula` - Detect planetary nebulae
- `supernova remnant` - Detect supernova remnants

### Solar System Objects
- `planet` - Detect planets
- `moon crater` - Detect craters on moons
- `asteroid` - Detect asteroids
- `comet` - Detect comets

---

## Troubleshooting

### Classification not working?
1. Check AI service is running:
   ```bash
   curl http://localhost:8001/health
   ```

2. Check browser console (F12) for errors

3. Verify you clicked "Rectangle + AI Classify" button

### Detection returns no results?
1. Try lowering confidence threshold to 0.4 or 0.5

2. Try different object types

3. Check AI service logs:
   ```bash
   # You should see:
   🎯 Detect Objects: 'galaxy' | Dataset: 'andromeda' | Threshold: 0.6
   ```

### Pins not showing on viewer?
1. Check that detections have valid bounding boxes

2. Refresh the page

3. Check browser console for errors

---

## Current Status

**Currently in MOCK mode:**
- Classification uses random object types with realistic confidence scores
- Detection returns random patches from the dataset
- Both features demonstrate the UI/UX and API flow

**To upgrade to REAL AI:**
- See `PLATFORM_INTEGRATION.md` section "Upgrading to Real AI"
- Involves loading real CLIP model and implementing zero-shot classification
- Detection will use actual semantic search with FAISS

---

## Next Steps

1. **Test the features** with the mock implementation
2. **Verify the UI/UX** works as expected
3. **Upgrade to real CLIP** for production use
4. **Add more object types** as needed
5. **Optimize performance** with caching and batching

---

## Need Help?

- Check `PLATFORM_INTEGRATION.md` for comprehensive documentation
- See the troubleshooting sections above
- Check the AI service logs for detailed error messages
- Open an issue on GitHub

**Happy detecting! 🔭✨**

