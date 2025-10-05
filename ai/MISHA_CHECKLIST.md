# ✅ Misha's AI Task Checklist

**Print this out or keep it open during the hackathon!**

---

## 🎯 H0-H2: Kickoff (TEAM)
- [ ] Scope confirmed with team
- [ ] Development environment ready
- [ ] Can access repository
- [ ] Communication channels set up

---

## ⚡ H2-H6: FIRST PIXELS (Priority 1 - CRITICAL)

### Environment Setup (30 min)
- [ ] Python 3.9+ installed and working
- [ ] `cd ai && pip install -r requirements.txt` completes
- [ ] CLIP model loads: `python -c "from models.clip_model import ClipEncoder; clip = ClipEncoder()"`
- [ ] FAISS imports: `python -c "import faiss; print(faiss.__version__)"`

### Build Index (1 hour)
- [ ] Sample tiles exist in `../infra/tiles/andromeda/`
- [ ] Run: `python build_real_index.py --dataset-id andromeda --tiles-dir ../infra/tiles --max-patches 500`
- [ ] Index created: `data/andromeda.faiss` exists
- [ ] Metadata created: `data/andromeda_metadata.json` and `data/andromeda_patches.json` exist
- [ ] No errors in console output
- [ ] At least 200+ patches indexed

### Start Service (30 min)
- [ ] Run: `python app.py`
- [ ] Service starts on http://localhost:8001
- [ ] No startup errors
- [ ] Run quick test: `python test_quick.py`
- [ ] Health check passes: `curl http://localhost:8001/health`
- [ ] Datasets endpoint works: `curl http://localhost:8001/datasets`

### Basic Search Working (1 hour)
- [ ] Search endpoint responds: `curl "http://localhost:8001/search?q=star&dataset_id=andromeda&k=5"`
- [ ] Returns JSON with results array
- [ ] Results have `bbox`, `score`, `rank` fields
- [ ] Try 3 different queries: "star", "bright", "dust"
- [ ] At least one query returns results

### Integration Test (1.5 hours)
- [ ] Coordinate with Edward - API service can reach AI service
- [ ] Test proxied search: `curl "http://localhost:8000/search?q=star&datasetId=andromeda"`
- [ ] Coordinate with Bohdan - search results display on frontend
- [ ] Open http://localhost:3000 and test search UI
- [ ] Results show up on viewer (even if positions are wrong)

### 🎉 MILESTONE 1 ACHIEVED: Basic search working end-to-end!

---

## 🚀 H6-H12: IMPROVE & OPTIMIZE (Priority 2)

### Better Patch Sampling (2 hours)
- [ ] Review current patch extraction code
- [ ] Increase max patches: `--max-patches 2000`
- [ ] Enable interest point detection (optional)
- [ ] Rebuild index with new settings
- [ ] Verify more diverse patches extracted
- [ ] Test searches - results improved?

### Performance Optimization (1.5 hours)
- [ ] Run performance benchmarks: `python test_quick.py`
- [ ] Search latency <1s (cold), <100ms (warm)
- [ ] Implement NMS (copy from MISHA_AI_TASKS.md)
- [ ] Verify cache is working (repeat query is faster)
- [ ] Test with 5+ different queries
- [ ] All queries return in acceptable time

### Fix Coordinates (1.5 hours)
- [ ] Coordinate with Ivan - understand tile coordinate system
- [ ] Review DZI info: `cat ../infra/tiles/andromeda/info.dzi`
- [ ] Verify bbox coordinates in metadata
- [ ] Calculate global coordinates correctly
- [ ] Test with Bohdan - results show in correct position on map
- [ ] Click "jump to result" works correctly

### Multi-Dataset Support (1 hour)
- [ ] Create second dataset (or duplicate): `python build_real_index.py --dataset-id test2 ...`
- [ ] Verify both datasets show up: `curl http://localhost:8001/datasets`
- [ ] Search both datasets independently
- [ ] No conflicts or errors

### 🎉 MILESTONE 2 ACHIEVED: Search is fast, accurate, and well-integrated!

---

## 🎁 H12-H18: ADVANCED FEATURES (Priority 3 - Nice to Have)

### Query Expansion (1 hour)
- [ ] Implement query synonyms (see MISHA_AI_TASKS.md)
- [ ] Test expanded queries
- [ ] Better recall on semantic searches

### Batch Encoding (1 hour)
- [ ] Update `_process_patch_batch` to use `encode_images_batch`
- [ ] Rebuild index - measure speedup
- [ ] 2-5x faster indexing

### Result Thumbnails (1 hour)
- [ ] Save patch thumbnails during indexing
- [ ] Add `thumbnail_url` to metadata
- [ ] Coordinate with API - serve thumbnails
- [ ] Coordinate with Bohdan - display thumbnails

### Advanced Filters (1 hour)
- [ ] Implement spatial filter (search within bbox)
- [ ] Implement scale filter
- [ ] Test filters work
- [ ] Document usage

### Logging & Analytics (1 hour)
- [ ] Implement search analytics (see code in MISHA_AI_TASKS.md)
- [ ] Log queries and performance
- [ ] Track popular queries
- [ ] Share insights with team

---

## 🌟 H18-H24: POLISH & SAM (Priority 4 - Stretch Goals)

### SAM Integration (2 hours) - ONLY IF AHEAD OF SCHEDULE
- [ ] Download SAM checkpoint: `sam_vit_b_01ec64.pth`
- [ ] Place in `ai/checkpoints/`
- [ ] Test SAM loads: `python -c "from sam_integration import get_sam_instance; print(get_sam_instance())"`
- [ ] Test `/segment` endpoint
- [ ] Create test image and test segmentation
- [ ] Coordinate with Bohdan - integrate mask overlay

### Performance Tuning (1 hour)
- [ ] Run comprehensive benchmarks
- [ ] Optimize slow operations
- [ ] Pre-warm cache on startup
- [ ] Tune k value for optimal results
- [ ] Meet performance targets (see ARCHITECTURE.md)

### Error Handling (1 hour)
- [ ] Add better error messages
- [ ] Handle edge cases (empty query, missing dataset, etc.)
- [ ] Test invalid inputs
- [ ] Graceful fallbacks
- [ ] No crashes or exceptions

### Documentation (1 hour)
- [ ] Update README with examples
- [ ] Create demo script
- [ ] List working queries
- [ ] Document known issues
- [ ] Prepare handoff notes

### 🎉 MILESTONE 3 ACHIEVED: Production-ready AI service!

---

## 🧪 H24-H30: INTEGRATION & TESTING (Priority 1)

### Integration Testing (2 hours)
- [ ] Meet with Edward - test full API integration
- [ ] Meet with Bohdan - test frontend display
- [ ] Meet with Ivan - verify tile/data compatibility
- [ ] Check with Illia - security settings OK
- [ ] End-to-end test: open viewer → search → see results → click result → fly to location
- [ ] Test all modes: Explore, Compare, Annotate
- [ ] Test with multiple datasets

### Bug Fixes (2 hours)
- [ ] List all bugs found
- [ ] Prioritize critical bugs
- [ ] Fix critical bugs
- [ ] Re-test after fixes
- [ ] Document workarounds for non-critical bugs

### Performance Validation (1 hour)
- [ ] Run benchmarks on final system
- [ ] Verify targets met:
  - [ ] <2s first pixels
  - [ ] <1s search (cold)
  - [ ] <100ms search (warm)
  - [ ] No errors under normal use
- [ ] Stress test with many queries
- [ ] Check memory usage OK

### Demo Preparation (1 hour)
- [ ] Prepare 5-10 demo queries that work well
- [ ] Test each query multiple times
- [ ] Note interesting results
- [ ] Prepare backup queries
- [ ] Practice demo flow
- [ ] Share demo queries with team

---

## 🏁 H30-H36: FINAL POLISH & DEMO

### Final Testing (1 hour)
- [ ] Run full test checklist (see MISHA_AI_TASKS.md Step 20)
- [ ] All critical tests pass
- [ ] No errors in logs
- [ ] Service stable
- [ ] Performance acceptable

### Demo Rehearsal (1 hour)
- [ ] Practice 90-second pitch
- [ ] Practice 3-minute demo
- [ ] Prepare for Q&A
- [ ] Know your metrics (latency, accuracy, etc.)
- [ ] Have backup plan if demo fails

### Documentation Finalization (1 hour)
- [ ] README is complete
- [ ] API docs are accurate
- [ ] Known issues documented
- [ ] Future improvements listed
- [ ] Team can run the service without you

### Standby & Support (3 hours)
- [ ] Available for bug fixes
- [ ] Monitor service during demo
- [ ] Ready to explain AI components
- [ ] Support team during presentation

---

## 📊 Success Metrics

### Minimum Success (H12)
- [ ] AI service running stably
- [ ] Search endpoint working
- [ ] 3+ queries return relevant results
- [ ] Integrated with frontend
- [ ] Results display on viewer

### Target Success (H24)
- [ ] Fast search (<100ms warm)
- [ ] Accurate coordinates
- [ ] Multiple datasets supported
- [ ] Good result quality
- [ ] Smooth demo experience

### Stretch Success (H36)
- [ ] SAM segmentation working
- [ ] Advanced filters implemented
- [ ] Result thumbnails
- [ ] Performance optimized
- [ ] Production-ready

---

## 🚨 Red Flags (Stop and Get Help)

If you see any of these, ask for help immediately:

- [ ] ❌ Service won't start after 30 min debugging
- [ ] ❌ CLIP model won't load after trying CPU/GPU options
- [ ] ❌ Index building fails completely
- [ ] ❌ Search always returns 0 results
- [ ] ❌ Coordinates are completely wrong (off by orders of magnitude)
- [ ] ❌ Service crashes frequently
- [ ] ❌ Blocked waiting for another team member >1 hour

**Don't waste time debugging alone - ask the team!**

---

## 🎯 Priority Guide

If running out of time, focus on:

**CRITICAL (Must Have):**
1. Basic search working
2. Integration with API + Frontend
3. Coordinates correct
4. Service stable

**IMPORTANT (Should Have):**
5. Performance optimized
6. Multiple queries working
7. Multi-dataset support
8. Good error handling

**NICE TO HAVE (Stretch):**
9. SAM segmentation
10. Advanced filters
11. Thumbnails
12. Analytics

---

## 📱 Quick Commands Reference

```bash
# Start service
cd ai && python app.py

# Rebuild index
python build_real_index.py --dataset-id andromeda --tiles-dir ../infra/tiles

# Quick test
python test_quick.py

# Test search
curl "http://localhost:8001/search?q=star&dataset_id=andromeda&k=5" | python -m json.tool

# Check health
curl http://localhost:8001/health

# View logs
# (watch console output where app.py is running)
```

---

## 🤝 Team Contacts

- **Edward** (Backend API) - Search result format, integration
- **Bohdan** (Frontend) - Coordinate display, UI integration  
- **Ivan** (Data/Infra) - Tile structure, coordinates
- **Illia** (Security) - CORS, rate limiting

---

**Remember:** Progress over perfection! Get it working first, optimize later! 

**You've got this! 🚀✨**

---

*Last updated: H2 - Initial setup complete, infrastructure ready*

