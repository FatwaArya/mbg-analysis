# Colab Notebook Fixes Applied

## Summary
Fixed the Colab notebook to match the droplet pipeline behavior and correct all path/logic errors.

## Critical Fixes

### 1. **Added Model Download Cell (New Cell 6)**
- **Issue:** Notebook assumed model exists on Drive
- **Fix:** Added cell to download IndoBERT model from Spaces (~475MB)
- **Location:** Before Stage 1

### 2. **Fixed inference.py Path (Stage 1)**
- **Issue:** Called `{CODE_DIR}/scripts/inference.py` (wrong path)
- **Fix:** Changed to `{CODE_DIR}/inference.py` (repo root)
- **Reason:** `inference.py` lives at repo root, not in scripts/

### 3. **Added Processed Directory Copy (Stage 1)**
- **Issue:** Missing copy step after inference
- **Fix:** Added `shutil.copy(RELEVANT_CSV, f"{PROCESSED_DIR}/tweets_relevant.csv")`
- **Reason:** Stage 2 expects input in `processed/` directory

### 4. **Fixed Skip Check File Names**
- **Stage 1:** Changed from checking `tweets_tagged.csv` → `tweets_relevant.csv`
- **Stage 2:** Changed from checking `tweets_preprocessed.csv` → `tweets_relevant_tagged.csv`
- **Stage 3:** Already correct (`tweets_preprocessed.csv`)
- **Stage 4:** Already correct (`tweets_with_sentiment.csv`)

### 5. **Fixed Manifest Generation Arguments (Stage 7)**
- **Issue:** Called without required arguments
- **Fix:** Pass `RUN_ID` and `duration` as command-line args
- **Added:** Notebook start time tracking in Cell 1 for duration calculation

### 6. **Updated Embedding Cache Note**
- **Issue:** Misleading message about cache usage
- **Fix:** Clarified that pipeline computes fresh embeddings each run
- **Note:** Cache is informational only, not used by default

### 7. **Added Notebook Start Time Tracking (Cell 1)**
- **Added:** `notebook_start_time = time.time()` at start
- **Added:** `import time` to Cell 1
- **Reason:** Needed for manifest duration calculation in Stage 7

## Path Consistency

All stages now use consistent path variables:
- `OUTPUT_DIR` = `/content/drive/MyDrive/mbg/data/output`
- `PROCESSED_DIR` = `/content/drive/MyDrive/mbg/data/processed`
- `RAW_DIR` = `/content/drive/MyDrive/mbg/data/raw`

## Error Handling

Maintained droplet script behavior:
- **Stage 6 (Validation):** Raises exception on failure (stops pipeline)
- **Stage 8 (Upload):** Warns on failure but continues (non-blocking)

## Removed Unnecessary Comments

Cleaned up all "FIX:" comments from cells for cleaner presentation while keeping the fixes.

## Testing Checklist

Before running on Colab:
1. ✅ Ensure T4 GPU is enabled (Runtime → Change runtime type)
2. ✅ Fill in credentials in Cell 3 (DROPLET_IP, GITHUB_REPO)
3. ✅ Upload raw CSV to Drive at `/content/drive/MyDrive/mbg/data/raw/final_parent_x_posts_mbg.csv`
4. ✅ Configure s3cmd if Spaces bucket is private (for model download and upload)

## Expected Runtime (T4 GPU)

- Stage 1 (Inference): ~15-20 min
- Stage 2 (Language): ~2-3 min
- Stage 3 (Preprocessing): ~5-8 min
- Stage 4 (Sentiment): ~20-30 min
- Stage 5 (Topics): ~30-60 min
- Stage 6-8: ~2-5 min
- **Total: ~75-130 minutes**

## Key Differences from Droplet

| Feature | Droplet | Colab |
|---------|---------|-------|
| Cache clearing | Automatic at start | Not needed (ephemeral) |
| Lockfile | Prevents concurrent runs | Not needed (single session) |
| Logging | Unified log file | Cell outputs |
| Model location | `/opt/mbg/model` | `/content/drive/MyDrive/mbg/model` |
| Data persistence | Local disk | Google Drive |

## Next Steps

1. Test notebook end-to-end on Colab
2. Verify all outputs match droplet pipeline
3. Consider adding progress bars for long-running stages
4. Optional: Add embedding cache to Drive to speed up reruns
