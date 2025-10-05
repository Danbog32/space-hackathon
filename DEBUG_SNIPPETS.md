# 🔍 Debugging Snippet Preview Issue

## Changes Made

### 1. Added Console Logging
- `AnnotationsList.tsx` now logs annotation metadata to browser console
- Shows whether `snippet_preview` exists in each annotation

### 2. Added UI Feedback
- When snippets toggle is ON and no preview exists, shows: "No snippet preview available"
- This helps identify which annotations have/don't have snippet data

## How to Debug

### Step 1: Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Create a new annotation (Press `3`, draw rectangle)
4. Look for logs like:
   ```
   Annotation 123 metadata: {snippet_preview: "data:image/jpeg;base64,...", ...}
   Has snippet_preview: true
   ```

### Step 2: Create Fresh Annotation
1. **Open** http://localhost:3000
2. **Click** "Andromeda Galaxy"
3. **Press** `3` for Annotate mode
4. **Draw** a rectangle (click twice)
5. **Wait** for AI classification
6. **Check** if snippet appears in annotation list

### Step 3: Verify Toggle
1. **Click** 🖼️ Snippets button in toolbar
2. Should toggle between:
   - **ON**: Shows snippets (or "No snippet preview available")
   - **OFF**: Hides snippet section entirely

## Common Issues

### Issue 1: Old Annotations Don't Have Snippets
**Problem:** Annotations created before this feature won't have snippet data

**Solution:** 
- Delete old annotations
- Create new ones with AI classification
- Only new annotations will have snippets

### Issue 2: Base64 Images Too Large
**Problem:** Base64 images can be 100KB+ and might not save to database

**Solution:**
- Check backend logs for errors
- Look for SQLite size limit errors
- Snippets are resized to max 400x400px to reduce size

### Issue 3: Metadata Not Persisting
**Problem:** Metadata might not be saved/loaded correctly

**Debug Steps:**
1. Check API response in Network tab:
   ```
   POST /annotations/{id}
   Response should include metadata field
   ```

2. Check database directly:
   ```bash
   cd data
   sqlite3 astro.db
   SELECT id, label, metadata FROM annotation;
   ```

3. Look for NULL or empty metadata

## Expected Behavior

### ✅ Working Correctly:
```
1. Draw rectangle
2. AI analyzes (shows popup with snippet)
3. Annotation appears in list
4. Snippet preview shows in annotation card
5. Toggle hides/shows snippet
```

### ❌ Not Working:
```
1. Draw rectangle  
2. AI analyzes (popup appears)
3. Annotation appears in list
4. Shows "No snippet preview available"
   OR
   Nothing appears at all
```

## Quick Test Script

Open browser console and paste:
```javascript
// Check if showSnippets is enabled
const store = window.__ZUSTAND__;
console.log('Snippets toggle:', store?.getState()?.showSnippets);

// Check annotation metadata
const annotations = store?.getState()?.annotations || [];
annotations.forEach(ann => {
  console.log(`Annotation ${ann.id}:`, {
    hasMetadata: !!ann.metadata,
    hasSnippet: !!ann.metadata?.snippet_preview,
    snippetSize: ann.metadata?.snippet_size
  });
});
```

## Next Steps Based on Results

### If console shows "Has snippet_preview: true"
✅ Data is there, might be UI rendering issue
- Check CSS/styling
- Try different browser

### If console shows "Has snippet_preview: false" 
❌ Data not being saved
- Check backend logs
- Verify API updateAnnotation call
- Check database metadata column

### If "No snippet preview available" message appears
⚠️ Annotation exists but no snippet
- Delete annotation and create new one
- Check if AI classification completed successfully
- Verify classification response includes snippet_preview

## Manual Database Check

```bash
# Check what's actually in the database
cd data
sqlite3 astro.db

# View all annotations with metadata
SELECT id, label, length(metadata) as metadata_size FROM annotation;

# Check specific annotation
SELECT * FROM annotation WHERE id = 1;
```

## Contact Points to Check

1. **AI Service** (Port 8001)
   - Generating snippet_preview?
   - Returning base64 image?
   - Check: `apps/ai/app/main.py` lines 404-426

2. **API Backend** (Port 8000)
   - Saving metadata?
   - Returning metadata on GET?
   - Check: `apps/api/app/routers/annotations.py`

3. **Frontend** (Port 3000)
   - Receiving snippet_preview?
   - Passing to updateAnnotation?
   - Check: `apps/web/src/components/Annotator.tsx` lines 42-51

## Expected Data Flow

```
1. User draws rectangle
2. Annotator calls: api.classifyRegion(datasetId, bbox)
3. AI service returns:
   {
     primary_classification: "galaxy",
     confidence: 0.89,
     snippet_preview: "data:image/jpeg;base64,/9j/4AAQSkZJ...",
     snippet_size: "300x300"
   }
4. Annotator calls: api.updateAnnotation(id, { metadata: {...} })
5. API saves to database
6. AnnotationsList renders snippet from annotation.metadata.snippet_preview
```

If any step fails, snippets won't appear!
