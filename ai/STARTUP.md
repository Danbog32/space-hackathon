🚀 Complete Startup Guide - AI Features Enabled

## ⚠️ IMPORTANT: AI Service Required

The new AI features (classification, detection) **REQUIRE** the AI service to be running. If it's not running, you'll see errors when:

- Drawing rectangle annotations (classification won't work)
- Using object detection (will show "AI service unavailable")

---

## 🎯 Quick Start (All 3 Services)

You **MUST** start all 3 services for the AI features to work:

### Terminal 1: AI Service (REQUIRED for AI features)

```bash
cd ai
python simple_app.py
```

**Wait for:** `✅ Loaded metadata: 1024 patches` and `Uvicorn running on http://0.0.0.0:8001`

### Terminal 2: API Backend (REQUIRED)

```bash
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

**Wait for:** `Application startup complete` and `Uvicorn running on http://127.0.0.1:8000`

### Terminal 3: Frontend (REQUIRED)

```bash
cd apps/web
npm run dev
```

**Wait for:** `Ready in X.Xs` and `Local: http://localhost:3000`

### Open Browser

```
http://localhost:3000
```

---

## ✅ Verify All Services Are Running

Before using the platform, check all services are healthy:

```bash
# Check AI Service (Port 8001)
curl http://localhost:8001/health

# Check API Backend (Port 8000)
curl http://localhost:8000/health

# Check Frontend (Port 3000)
# Should open in browser: http://localhost:3000
```

---

## 🎨 Using the AI Features

### Feature 1: Auto-Classification on Annotations

1. Open http://localhost:3000
2. Select dataset (e.g., "Andromeda Galaxy")
3. Click **"Annotate (3)"** button in top toolbar
4. Click **"Rectangle + AI Classify"** button
5. Draw rectangle (click twice to make corners)
6. ✨ **AI popup appears instantly!** Shows what's in the region

**If you see error:** Check Terminal 1 - AI service must be running!

---

### Feature 2: Object Detection by Name

1. Stay on viewer page
2. Look at **left panel** - see "🎯 Object Detection"
3. Type object name: `galaxy` or click quick-select button
4. Adjust confidence slider (60% default)
5. Click **"Detect Objects"**
6. ✨ **All instances appear as pins on the image!**

**If you see "AI service unavailable":** Check Terminal 1 - AI service must be running!

---

### Feature 3: Semantic Search

1. Look at **left panel** (top) - see "AI Search"
2. Type description: `bright region` or `dark area`
3. Click **"Search"**
4. ✨ **Results appear with confidence scores!**
5. Click any result to fly to that location

**If you see error:** Check Terminal 1 - AI service must be running!

---

## 🐛 Troubleshooting

### "Failed to classify region" or "AI service unavailable"

**Problem:** AI service is not running on port 8001

**Solution:**

```bash
# Start AI service
cd ai
python simple_app.py

# You should see:
# ✅ Loaded metadata: 1024 patches
# INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Verify it's running:**

```bash
curl http://localhost:8001/health
# Should return: {"status":"ok","patches":1024,"service":"simple_ai"}
```

---

### "Failed to fetch datasets"

**Problem:** API backend is not running on port 8000

**Solution:**

```bash
cd apps/api
python -m uvicorn app.main:app --reload --port 8000
```

**Verify it's running:**

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok","version":"0.1.0",...}
```

---

### Port Already in Use

**Problem:** `Address already in use` error

**Solution (Windows PowerShell):**

```powershell
# Find and kill process on port 8001 (AI service)
netstat -ano | findstr :8001
taskkill /PID <PID> /F

# Find and kill process on port 8000 (API)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Find and kill process on port 3000 (Frontend)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

---

### Annotations Save but No AI Classification

**Problem:** Annotation creates but no popup appears

**Checklist:**

1. ✅ AI service running? `curl http://localhost:8001/health`
2. ✅ Used "Rectangle + AI Classify" button? (not just "Rectangle")
3. ✅ Check browser console (F12) for errors
4. ✅ Check Terminal 1 for AI service logs

---

### Object Detection Returns No Results

**Problem:** Click "Detect Objects" but nothing happens

**Solutions:**

1. **Lower confidence threshold** - Try 30-50% instead of 60%
2. **Try different object types:**
   - `galaxy`
   - `star`
   - `nebula`
   - `bright region`
3. **Check AI service logs** in Terminal 1 - should see:
   ```
   🎯 Detect Objects: 'galaxy' | Dataset: 'demo' | Threshold: 0.6
   ```

---

## 📊 What Each Service Does

| Service         | Port | Purpose                           | Required For     |
| --------------- | ---- | --------------------------------- | ---------------- |
| **AI Service**  | 8001 | Classification, Detection, Search | AI features only |
| **API Backend** | 8000 | Database, Auth, Proxy to AI       | Everything       |
| **Frontend**    | 3000 | Web UI                            | User interface   |

---

## 🔍 Service Health Check Commands

Run these to verify all services are healthy:

```bash
# AI Service Health
curl http://localhost:8001/health
# Expected: {"status":"ok","patches":1024,"service":"simple_ai"}

# API Backend Health
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"0.1.0",...}

# Test AI Classification Endpoint
curl -X POST "http://localhost:8001/classify?dataset_id=demo&bbox=[512,256,128,128]"
# Expected: JSON with classification results

# Test AI Detection Endpoint
curl "http://localhost:8001/detect?q=galaxy&datasetId=demo&confidence_threshold=0.6"
# Expected: JSON with detection results

# Test API Proxy to AI
curl "http://localhost:8000/search?q=bright&datasetId=andromeda&topK=5"
# Expected: JSON with search results
```

---

## ⚡ Quick Restart (If Something Breaks)

If things stop working:

1. **Stop all services** (Ctrl+C in each terminal)
2. **Wait 5 seconds**
3. **Restart in order:**

```bash
# Terminal 1: AI Service
cd ai && python simple_app.py

# Terminal 2: API Backend
cd apps/api && python -m uvicorn app.main:app --reload --port 8000

# Terminal 3: Frontend
cd apps/web && npm run dev
```

4. **Refresh browser** (Ctrl+Shift+R for hard refresh)

---

## 📝 Windows Batch Script (Optional)

Create `START_ALL.bat` in the root directory:

```batch
@echo off
echo Starting Astro-Zoom Platform with AI Features...
echo.

echo [1/3] Starting AI Service on port 8001...
start "AI Service" cmd /k "cd ai && python simple_app.py"
timeout /t 3

echo [2/3] Starting API Backend on port 8000...
start "API Backend" cmd /k "cd apps/api && python -m uvicorn app.main:app --reload --port 8000"
timeout /t 3

echo [3/3] Starting Frontend on port 3000...
start "Frontend" cmd /k "cd apps/web && npm run dev"

echo.
echo All services starting...
echo Wait for all services to show "ready" before opening browser
echo.
echo Then open: http://localhost:3000
pause
```

Then just run: `START_ALL.bat`

---

## 🎯 Summary

**For AI features to work, you MUST run:**

1. ✅ **AI Service** (Terminal 1) - `cd ai && python simple_app.py`
2. ✅ **API Backend** (Terminal 2) - `cd apps/api && python -m uvicorn app.main:app --reload --port 8000`
3. ✅ **Frontend** (Terminal 3) - `cd apps/web && npm run dev`

**Without AI service:**

- ❌ Auto-classification won't work
- ❌ Object detection won't work
- ❌ Semantic search won't work
- ✅ Basic viewer, annotations (without AI), compare mode still work

**With all 3 services:**

- ✅ Everything works perfectly!

---

## 🚀 You're Ready!

Once all 3 services show "ready", open http://localhost:3000 and enjoy all the AI features! 🎉
