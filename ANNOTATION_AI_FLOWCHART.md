# 🔬 Annotation with AI Classification Flowchart

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                             │
│  User draws rectangle on image in Annotate mode                │
│  (Click 1: Start point, Click 2: End point)                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FRONTEND (Annotator.tsx)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Calculate rectangle geometry:                         │  │
│  │    - x, y (top-left corner)                              │  │
│  │    - width, height                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2. Create annotation with temporary label                │  │
│  │    POST /annotations                                     │  │
│  │    {                                                     │  │
│  │      datasetId: "andromeda",                            │  │
│  │      type: "rect",                                      │  │
│  │      geometry: {x, y, width, height},                   │  │
│  │      label: "Classifying...",     ← Temporary!          │  │
│  │      color: "#ff0000"                                   │  │
│  │    }                                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              API BACKEND (Port 8000)                            │
│  app/routers/annotations.py                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 3. Save annotation to SQLite database                    │  │
│  │    INSERT INTO annotation (...)                          │  │
│  │    VALUES (id=123, label="Classifying...", ...)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 4. Return created annotation with ID                     │  │
│  │    { id: "123", label: "Classifying...", ... }          │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FRONTEND (Annotator.tsx)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 5. Store annotation ID in state                          │  │
│  │    setCurrentAnnotationId("123")                         │  │
│  │                                                           │  │
│  │ 6. Add annotation to viewer store                        │  │
│  │    (Rectangle appears with "Classifying..." label)       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 7. Trigger AI Classification                             │  │
│  │    classifyMutation.mutate([x, y, width, height])       │  │
│  │    POST /classify?datasetId=andromeda&bbox=x,y,w,h      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         API BACKEND (Port 8000) - Classify Router               │
│  app/routers/classify.py                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 8. Parse bbox string to validate format                  │  │
│  │    "100,200,50,75" → [100, 200, 50, 75]                 │  │
│  │                                                           │  │
│  │ 9. Map dataset ID                                        │  │
│  │    "andromeda" → "demo" (for AI service)                │  │
│  │                                                           │  │
│  │ 10. Proxy request to AI service                          │  │
│  │     POST http://localhost:8001/classify                  │  │
│  │     params: {datasetId: "demo", bbox: "100,200,50,75"}  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│           AI SERVICE (Port 8001)                                │
│  apps/ai/app/main.py                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 11. Receive classification request                       │  │
│  │     Parse bbox: "100,200,50,75" → [100, 200, 50, 75]   │  │
│  │                                                           │  │
│  │ 12. Run AI Classification (Currently Simulated)          │  │
│  │     • Select random object type from:                    │  │
│  │       [galaxy, nebula, star, star cluster,              │  │
│  │        supernova, planet, black hole, quasar]           │  │
│  │     • Generate confidence score (0.75-0.95)              │  │
│  │     • Generate alternative classifications               │  │
│  │                                                           │  │
│  │ 13. Return classification result                         │  │
│  │     {                                                     │  │
│  │       primary_classification: "galaxy",                  │  │
│  │       confidence: 0.89,                                  │  │
│  │       all_classifications: [                             │  │
│  │         {type: "galaxy", confidence: 0.89, rank: 1},    │  │
│  │         {type: "nebula", confidence: 0.07, rank: 2},    │  │
│  │         {type: "star", confidence: 0.04, rank: 3}       │  │
│  │       ],                                                  │  │
│  │       bbox: [100, 200, 50, 75]                          │  │
│  │     }                                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         API BACKEND (Port 8000) - Classify Router               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 14. Receive AI response and format                       │  │
│  │     Add datasetId back to response                       │  │
│  │     Return to frontend                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FRONTEND (Annotator.tsx)                        │
│  classifyMutation.onSuccess()                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 15. Receive classification result                        │  │
│  │     { primary_classification: "galaxy",                  │  │
│  │       confidence: 0.89, ... }                            │  │
│  │                                                           │  │
│  │ 16. Update annotation with classification                │  │
│  │     PATCH /annotations/123                               │  │
│  │     {                                                     │  │
│  │       label: "galaxy",           ← Updated!              │  │
│  │       description: "AI Classified: 89.0% confidence"    │  │
│  │     }                                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              API BACKEND (Port 8000)                            │
│  app/routers/annotations.py                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 17. Update annotation in database                        │  │
│  │     UPDATE annotation                                    │  │
│  │     SET label = "galaxy",                                │  │
│  │         description = "AI Classified: 89.0% confidence", │  │
│  │         updated_at = NOW()                               │  │
│  │     WHERE id = 123                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 FRONTEND (Annotator.tsx)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 18. Update viewer store with new annotation              │  │
│  │     updateAnnotation("123", {                            │  │
│  │       label: "galaxy",                                   │  │
│  │       description: "AI Classified: 89.0% confidence"    │  │
│  │     })                                                    │  │
│  │                                                           │  │
│  │ 19. Show classification popup                            │  │
│  │     ┌─────────────────────────────────────┐            │  │
│  │     │ 🔬 AI Classification                │            │  │
│  │     │ Detected: galaxy                    │            │  │
│  │     │ Confidence: 89.0%                   │            │  │
│  │     │                                     │            │  │
│  │     │ Other possibilities:                │            │  │
│  │     │ • nebula    7.0%                   │            │  │
│  │     │ • star      4.0%                   │            │  │
│  │     └─────────────────────────────────────┘            │  │
│  │                                                           │  │
│  │ 20. Re-render canvas with updated label                  │  │
│  │     Rectangle now shows "galaxy" instead of              │  │
│  │     "Classifying..."                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    FINAL RESULT                                 │
│  ✅ Annotation persisted with AI-generated label                │
│  ✅ Label visible on canvas: "galaxy"                           │
│  ✅ Popup shows classification confidence                       │
│  ✅ Can view in Annotations List panel                          │
│  ✅ Survives page refresh (stored in database)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. **Frontend (React/Next.js)** - Port 3000
- **File:** `apps/web/src/components/Annotator.tsx`
- **Responsibilities:**
  - Handle user drawing interactions
  - Create temporary annotation
  - Trigger AI classification
  - Update annotation with AI result
  - Display classification popup

### 2. **API Backend (FastAPI)** - Port 8000
- **Files:**
  - `apps/api/app/routers/annotations.py` - CRUD operations
  - `apps/api/app/routers/classify.py` - Classification proxy
- **Responsibilities:**
  - Store/retrieve annotations in SQLite
  - Proxy classification requests to AI service
  - Format and validate data

### 3. **AI Service (FastAPI)** - Port 8001
- **File:** `apps/ai/app/main.py`
- **Responsibilities:**
  - Receive classification requests
  - Analyze image regions (currently simulated)
  - Return object type predictions with confidence

### 4. **Database (SQLite)**
- **File:** `apps/api/astro.db`
- **Table:** `annotation`
- **Stores:** All annotation data including AI-generated labels

---

## Data Flow Summary

```
User Draw → Create Annotation → Save to DB → Get ID →
→ Call AI Service → Get Classification → Update Annotation →
→ Update DB → Update UI → Show Result
```

---

## API Endpoints Used

1. **POST** `/annotations` - Create new annotation
2. **POST** `/classify?datasetId=X&bbox=x,y,w,h` - Get AI classification
3. **PATCH** `/annotations/{id}` - Update annotation label
4. **POST** `http://localhost:8001/classify` - AI service endpoint

---

## Error Handling

- Network errors → Show "Classification failed" message
- Invalid bbox → 400 Bad Request
- AI service down → 503 Service Unavailable
- Timeout → 30 second timeout on classification

---

## Performance

- **Classification time:** ~200-500ms (simulated)
- **With real AI:** Depends on model complexity
- **Database updates:** < 10ms
- **UI updates:** Instant (React state management)

---

## Future Enhancements

1. **Real AI Integration:**
   - Replace mock with CLIP/YOLO models
   - Add confidence thresholds
   - Support multiple object detection

2. **User Feedback:**
   - Allow users to correct AI predictions
   - Learn from corrections
   - Show classification history

3. **Advanced Features:**
   - Object segmentation (SAM)
   - Batch classification
   - Export annotations with labels
