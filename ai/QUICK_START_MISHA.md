# 🚀 Quick Start for Misha - TL;DR

**Your Mission:** Make AI search work for space imagery

---

## ⚡ 5-Minute Quick Start

```bash
# 1. Navigate to AI directory
cd C:\Users\miked\space-hackathon\ai

# 2. Install dependencies (if not done)
pip install -r requirements.txt

# 3. Build index from sample tiles
python build_real_index.py --dataset-id andromeda --tiles-dir ../infra/tiles --max-patches 500

# 4. Start AI service
python app.py

# 5. Test it works
curl "http://localhost:8001/search?q=star%20cluster&dataset_id=andromeda&k=5"
```

**Expected:** Service starts on port 8001, search returns JSON with bounding boxes

---

## 📋 Your Core Tasks (in order)

### ✅ Phase 1: H2-H6 (FIRST 4 HOURS)
**Goal:** Basic search working

1. **Build FAISS index** (30 min)
   - Run `build_real_index.py` 
   - Creates searchable embeddings from tiles

2. **Start service** (10 min)
   - Run `app.py`
   - Service on port 8001

3. **Test search** (20 min)
   - `curl` various queries
   - Verify results have proper bbox coordinates

4. **Integration test** (2 hours)
   - Work with Edward to connect API ↔ AI service
   - Work with Bohdan to display results on frontend

**✅ Milestone 1:** Can search "star" and see pins on image

---

### ⏳ Phase 2: H6-H12 (NEXT 6 HOURS)
**Goal:** Better results, faster performance

1. **Improve sampling** (2 hours)
   - Use interest point detection
   - Increase patches to 2000
   - Better coverage of interesting features

2. **Optimize performance** (2 hours)
   - Add NMS (non-max suppression) for overlapping results
   - Verify caching works
   - Target: <100ms search latency

3. **Multi-dataset** (1 hour)
   - Index multiple time periods
   - Support dataset switching

4. **Fix coordinates** (1 hour)
   - Ensure bbox maps correctly to image
   - Work with Ivan on tile coordinate system

**✅ Milestone 2:** 3+ different queries work well, results show in right place

---

### 🎁 Phase 3: H12-H24 (IF TIME)
**Goal:** Polish & stretch goals

1. **Advanced features** (3 hours)
   - Query expansion with synonyms
   - Spatial filters (search within region)
   - Result thumbnails

2. **SAM integration** (3 hours) - **STRETCH**
   - Download checkpoint
   - Test segmentation endpoint
   - Integrate with annotation workflow

3. **Performance tuning** (2 hours)
   - Benchmark all components
   - Pre-warm cache
   - Final optimizations

**✅ Milestone 3:** Production-ready service

---

## 🎯 What "Done" Looks Like

At minimum (H12):
- [x] AI service running on port 8001
- [ ] `/search?q=<query>` returns results
- [ ] At least 3 demo queries work well:
  - "bright star"
  - "dust cloud"
  - "galaxy core"
- [ ] Results display correctly on frontend (work with Bohdan)
- [ ] Search latency <1 second

Stretch goals:
- [ ] SAM segmentation working
- [ ] Advanced filters (spatial, scale)
- [ ] Result thumbnails

---

## 🔥 Most Important Tasks

**Priority 1 (MUST DO):**
1. ✅ Build index from tiles
2. ✅ Start AI service  
3. Get search endpoint working with API service
4. Verify coordinates map correctly to image
5. Test 3+ queries work well

**Priority 2 (SHOULD DO):**
6. Optimize performance (<100ms)
7. Add NMS for better results
8. Support multiple datasets

**Priority 3 (NICE TO HAVE):**
9. SAM integration
10. Advanced filters
11. Result thumbnails

---

## 🐛 Quick Troubleshooting

**Service won't start?**
```bash
# Check Python
python --version  # Should be 3.9+

# Check dependencies
pip list | grep -E "torch|faiss|open_clip"

# Try CPU mode explicitly
# Edit models/clip_model.py, line 73, add: device="cpu"
```

**No search results?**
```bash
# Verify index exists
ls -lh data/*.faiss

# Check index has vectors
python -c "from utils.faiss_helper import DatasetIndexManager; from pathlib import Path; mgr = DatasetIndexManager(Path('data')); mgr.load_dataset('andromeda'); print(mgr.get_dataset_info('andromeda'))"

# Rebuild if needed
python build_real_index.py --dataset-id andromeda --tiles-dir ../infra/tiles
```

**Coordinates wrong on frontend?**
- Check with Bohdan on expected format
- Verify tile coordinate conversion
- Test with level 0 tiles first (simplest)

---

## 🤝 Who to Ask for Help

- **Edward** (Backend): API integration, search result format
- **Bohdan** (Frontend): Coordinate system, display format
- **Ivan** (Data): Tile structure, dataset paths
- **Illia** (Security): Rate limiting, CORS

---

## 📞 Quick Test Commands

```bash
# Health check
curl http://localhost:8001/health

# List datasets
curl http://localhost:8001/datasets

# Search
curl "http://localhost:8001/search?q=star&dataset_id=andromeda&k=5" | jq

# Get embedding
curl "http://localhost:8001/embed?text=galaxy" | jq '.embedding_dim'

# Cache stats
curl http://localhost:8001/search/cache_stats

# Clear cache
curl -X POST http://localhost:8001/search/clear_cache
```

---

## 📚 Full Guide

See **MISHA_AI_TASKS.md** for detailed step-by-step instructions with code examples.

---

**Remember:** 
- ✅ Get basic search working FIRST (H6)
- ⚡ Optimize SECOND (H12)  
- 🎁 Polish/SAM LAST (H24+)

**You've got 36 hours. Focus on core functionality first!**

🚀 **GO BUILD SOMETHING AWESOME!** ✨

