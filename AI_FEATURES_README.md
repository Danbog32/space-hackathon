# 🤖 AI Features Integration

## Two New AI Features Added! 🎉

This repository now includes two powerful AI capabilities for astronomical image analysis:

### 1. 🔬 Object Classification
**What:** Automatically identifies astronomical objects in annotated regions  
**How:** Draw a rectangle → Get instant AI classification  
**Output:** "galaxy" (87% confidence), plus alternatives  

### 2. 🎯 Object Detection
**What:** Finds ALL instances of a specific object type  
**How:** Search "galaxy" → See all galaxies highlighted  
**Output:** Multiple detections with bounding boxes and confidence scores  

---

## 🚀 Quick Start

### Start the Services
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

### Open Browser
Navigate to http://localhost:3000

### Try Classification
1. Select a dataset
2. Click "Rectangle + AI Classify"
3. Draw a rectangle
4. See instant classification popup!

### Try Detection
1. Find the "🎯 Object Detection" panel
2. Click "galaxy" quick-select
3. Click "Detect Objects"
4. See all galaxies highlighted!

---

## 📖 Documentation

- **Quick Start Guide:** `ai/AI_FEATURES_QUICKSTART.md`
- **Full Integration Guide:** `ai/PLATFORM_INTEGRATION.md` (900+ lines!)
- **Implementation Summary:** `AI_INTEGRATION_SUMMARY.md`

---

## 🏗️ What Changed

### New Endpoints
- `POST /classify` - Classify a region
- `GET /detect` - Detect all instances of an object

### New Components
- **Annotator** - Enhanced with auto-classification
- **ObjectDetector** - New detection UI

### New Files
- `apps/api/app/routers/classify.py`
- `apps/api/app/routers/detect.py`
- `apps/web/src/components/ObjectDetector.tsx`

---

## 🎨 Features in Action

### Classification
```
User draws rectangle
    ↓
AI analyzes region
    ↓
Popup shows: "galaxy" (87% confidence)
    ↓
Auto-closes after 5 seconds
```

### Detection
```
User searches "galaxy"
    ↓
AI scans entire image
    ↓
Finds 15 galaxies
    ↓
All appear as pins on viewer
    ↓
Click any pin to navigate
```

---

## 📊 Status

**Current:** Mock mode (demonstrates UI/UX and API flow)  
**Next:** Upgrade to real CLIP model (see integration guide)  
**Future:** Train custom models for astronomy  

---

## 🔗 Key Links

- [Quick Start Guide](ai/AI_FEATURES_QUICKSTART.md)
- [Integration Guide](ai/PLATFORM_INTEGRATION.md)
- [Implementation Summary](AI_INTEGRATION_SUMMARY.md)

---

## 🎯 Supported Object Types

- galaxy
- star
- nebula
- star cluster
- planet
- moon crater
- supernova remnant
- and more...

---

## 🛠️ API Examples

### Classify
```bash
curl -X POST "http://localhost:8000/classify?datasetId=andromeda&bbox=512,256,128,128"
```

### Detect
```bash
curl "http://localhost:8000/detect?q=galaxy&datasetId=andromeda&confidence_threshold=0.6"
```

---

## 💡 Pro Tips

- Lower confidence threshold → more detections
- Higher confidence threshold → more accurate
- Try specific queries: "spiral galaxy", "planetary nebula"
- Click detection results to fly to location

---

## 🐛 Troubleshooting

See the comprehensive troubleshooting sections in:
- `ai/PLATFORM_INTEGRATION.md`
- `ai/AI_FEATURES_QUICKSTART.md`

---

## ✨ What's Next?

1. Test the features in your browser
2. Review the detailed documentation
3. Upgrade to real CLIP for production
4. Add more object types as needed
5. Deploy and share with your team!

---

**Happy exploring! 🔭✨**

For detailed documentation, see `ai/PLATFORM_INTEGRATION.md`

