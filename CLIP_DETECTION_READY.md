# CLIP AI Object Detection - Ready to Test! 🚀

## Services Status ✅

All services are running and ready:
- **Web Frontend**: http://localhost:3000
- **API Backend**: http://localhost:8000
- **AI Service**: http://localhost:8001 (with CLIP loaded)

## How CLIP Object Detection Works

### 1. Image Processing Flow

```
User uploads image
    ↓
Image is tiled for Deep Zoom (DZI format)
    ↓
Source image is saved as "source.jpg" in tiles directory
    ↓
User requests object detection
    ↓
AI service looks for source.jpg
    ↓
If not found: Reconstructs image from tiles automatically
    ↓
CLIP analyzes image with sliding window (256x256 patches)
    ↓
Returns bounding boxes for detected objects
    ↓
Frontend displays red semi-transparent boxes on viewer
```

### 2. What Changed

#### ✅ AI Service (`ai/simple_app.py`)
- **CLIP Model**: Loads at startup (ViT-B-32)
- **Image Reconstruction**: Automatically rebuilds image from tiles if source.jpg is missing
- **PIL Protection Disabled**: Can handle large astronomical images (no size limits)
- **Smart Level Selection**: Uses lower resolution if full image is too large (>100MP)

#### ✅ Tile Processor (`apps/api/app/tile_processor.py`)
- **Source Preservation**: Saves original image as `source.jpg` during upload
- This ensures CLIP always has access to the full image

#### ✅ Frontend Features
- **Red Semi-Transparent Boxes**: Visible from the start
- **Opacity Control**: Slider to adjust box transparency
- **Strict Validation**: Boxes only appear within actual image bounds (no black areas)
- **Hide/Show AI Panels**: Button to toggle AI controls visibility
- **Click to Zoom**: Click any detection to fly to that location

## Testing CLIP Detection

### Step 1: Open the Platform
Navigate to: http://localhost:3000

### Step 2: Upload an Image
1. Click "Upload Dataset"
2. Select an astronomical image (JWST, Hubble, etc.)
3. Wait for tiling to complete
4. Open the viewer

### Step 3: Try Object Detection
1. In the "AI Object Detector" panel on the left
2. Enter an object type (e.g., "galaxy", "star", "nebula", "cluster")
3. Adjust confidence threshold (0.6 is default)
4. Click "Detect Objects"

### Step 4: Observe the Results

**In Browser Console** (F12), you should see:
```
🎯 Detect Objects: 'galaxy' | Dataset: 'your_dataset_id' | Threshold: 0.6
✅ Found existing source image: source.jpg
📐 Found source image: source.jpg (42208×9870)
🤖 CLIP Detection: loading image from ...
📐 Image size: 42208×9870
✅ CLIP found 25 detections for 'galaxy'
```

**If source.jpg doesn't exist**, you'll see:
```
📦 No source image found, attempting to reconstruct from tiles...
🔨 Reconstructing 42208×9870 image from level 11 tiles...
✅ Reconstructed image from 2145 tiles
✅ Saved reconstructed image to source.jpg
```

**On the Viewer**:
- Red semi-transparent bounding boxes appear on detected objects
- Each box has a numbered label
- Detection list appears in the left panel
- Click any detection to zoom to that location

### Step 5: Verify CLIP is Active

Check the detection metadata in console or API response:
```json
{
  "metadata": {
    "detection_method": "CLIP_AI",  // ← Should say "CLIP_AI", not "random"
    "model": "ViT-B-32",
    "patch_size": 256
  }
}
```

## What to Expect

### ✅ Good Results (CLIP Working)
- Detections cluster around actual objects in the image
- Confidence scores reflect actual similarity to query
- Different queries produce different detection patterns
- Detection method shows "CLIP_AI"

### ⚠️ Random Fallback (CLIP Not Working)
- Detections appear randomly distributed
- All queries produce similar random patterns
- Detection method shows "random_no_clip_model" or "random_no_image_found"
- Console shows warning: "⚠️ Using random detection"

## For Existing Datasets

If you uploaded images **before** this update:
1. The AI service will automatically reconstruct the image from tiles
2. First detection may take 10-30 seconds (reconstruction time)
3. Subsequent detections will be fast (image is cached as `source.jpg`)
4. You can manually check if reconstruction worked by looking in `infra/tiles/{datasetId}/` for `source.jpg`

## Troubleshooting

### Issue: "Detection Failed" Error
**Solution**: Check that all services are running (see ports above)

### Issue: Still seeing random detection
**Check**:
1. Console logs - does it say "CLIP_AI" or "random"?
2. Is CLIP loaded? Check AI service startup logs
3. Is image found? Look for "Found source image" or "reconstructing from tiles"

### Issue: Very slow detection
**Normal**: Large images (>50MP) take longer to analyze
**Expected**: 5-30 seconds for first detection on large images
**Speed up**: The service automatically uses lower resolution for very large images

### Issue: Boxes appear in black areas
**Should be fixed**: Strict validation now filters out-of-bounds boxes
**If still occurring**: Check console for "Filtered X boxes that were outside image bounds"

## Technical Details

### CLIP Sliding Window Parameters
- **Patch Size**: 256×256 pixels
- **Stride**: 128 pixels (50% overlap)
- **Batch Size**: 32 patches at a time (memory efficient)
- **Query Format**: "a photo of a {object_type}"

### Image Size Handling
- Images **< 100MP**: Full resolution analysis
- Images **> 100MP**: Automatically uses lower pyramid level
- Maximum: No limit (PIL protection disabled)

### Confidence Scores
- **0.6-0.7**: Possible match
- **0.7-0.8**: Likely match
- **0.8-0.9**: Strong match
- **> 0.9**: Very confident match

CLIP's confidence scores are relative similarity scores, not absolute probabilities.

## Need Help?

Check the console logs in both:
1. **Browser Console** (F12) - Frontend logging
2. **AI Service Terminal** - Backend CLIP processing logs

Look for:
- ✅ Success indicators (green checkmarks)
- ⚠️ Warnings (yellow warnings)
- 🤖 CLIP-specific messages

---

**Ready to test!** Open http://localhost:3000 and try detecting objects in your astronomical images! 🔭✨


