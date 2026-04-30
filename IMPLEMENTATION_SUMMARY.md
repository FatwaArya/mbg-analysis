# Timestamped Pipeline Runs Implementation Summary

## Overview
Successfully implemented timestamped pipeline runs with DigitalOcean Spaces versioning, comprehensive manifest generation, and automatic dashboard fallback loading.

**Every pipeline run processes from scratch** - no caching, no checkpoints, no file existence checks. This ensures consistent, reproducible results for each timestamped run.

## What Was Implemented

### 1. Manifest Generation (`scripts/generate_manifest.py`)
- Computes file metadata: row counts, file sizes, MD5 hashes
- Extracts statistics: sentiment distribution, topic counts, outliers
- Captures git commit hash for reproducibility
- Generates comprehensive JSON manifest with run metadata
- Can be run standalone for testing

### 2. Pipeline Metadata Capture (`scripts/run_full_pipeline.sh`)
- **Clears all caches at start** (sentiment checkpoints, topic embeddings)
- **Always runs inference** (no file existence check)
- Captures `RUN_ID` at pipeline start (format: `YYYYMMDD_HHMMSS`)
- Tracks execution duration (start time → end time)
- Calls `generate_manifest.py` after validation with run_id and duration
- Displays run metadata in summary output
- Updated from 7 to 9 steps (added cache clearing and manifest generation)

### 3. Timestamped Upload (`scripts/upload_run.py`)
- Reads `metadata.json` to get run_id and file information
- Uploads all files to `s3://bucket/runs/{run_id}/`
- Generates and uploads `latest_run.json` manifest at bucket root
- **Retry logic:** 3 attempts with 5-second exponential backoff
- **Error handling:** Cleans up partial uploads on failure
- **Verification:** Uses MD5 checksums for data integrity

### 4. Spaces Data Loader (`dashboard/spaces_loader.py`)
- Fetches `latest_run.json` from Spaces (cached for 5 minutes)
- Downloads CSVs directly to memory (no local caching needed)
- `load_with_fallback()` function: tries Spaces → falls back to local files
- Connection status checking (Spaces/Local/Offline)
- Run info formatting for display
- Detailed error messages when fallback occurs

### 5. Dashboard Integration
**Updated Files:**
- `dashboard/app.py` - Main dashboard with sidebar showing connection status and run info
- `dashboard/pages/0_temporal.py` - Temporal analysis
- `dashboard/pages/1_sentiment.py` - Sentiment analysis
- `dashboard/pages/2_topics.py` - Topic analysis (loads both topic_info and tweets_with_topics)
- `dashboard/pages/3_engagement.py` - Engagement metrics
- `dashboard/pages/4_explorer.py` - Tweet explorer
- `dashboard/pages/5_spikes.py` - Spike detection
- `dashboard/pages/6_analysis.py` - Research findings (analysis CSVs stay local-only)

**Features:**
- Sidebar shows data source indicator (🌐 Spaces / 💾 Local / ❌ Offline)
- Displays run metadata: run_id, timestamp, duration, git commit
- Automatic fallback with warning messages
- Consistent error handling across all pages

### 6. Run History Viewer (`dashboard/pages/7_run_history.py`)
- Lists all runs from `s3://bucket/runs/`
- Displays metadata table: run_id, timestamp, duration, row counts, sentiment %
- Allows selecting historical runs to view detailed metadata
- Shows download commands for specific runs
- Cached for 60 seconds (list) and 5 minutes (metadata)

### 7. Monitoring Enhancements (`scripts/monitor_pipeline.sh`)
- Shows current run_id from `metadata.json`
- Displays Spaces connection status
- Shows latest run in Spaces
- Monitors `upload_run.py` process status
- All existing monitoring features preserved

### 8. Error Handling & Recovery
**Upload Script:**
- 3 retry attempts with 5-second backoff for transient errors
- Timeout handling (60 seconds per operation)
- Partial upload cleanup on failure
- Keyboard interrupt handling

**Dashboard:**
- Specific error messages when Spaces unavailable
- Graceful fallback to local files
- Warning messages explain why fallback occurred
- No crashes when Spaces is down

### 9. Documentation (`scripts/PIPELINE_README.md`)
- Complete architecture diagram
- Updated pipeline flow (9 steps)
- Manifest schema documentation
- New troubleshooting sections for Spaces connectivity
- Dashboard features and data loading explanation
- Common operations with Spaces commands
- Benefits of timestamped versioning

## Architecture

```
Pipeline Run (20260430_174500)
  ↓
Local: /opt/mbg/data/output/*.csv (overwritten each run)
  ↓
[On Success] Upload to Spaces:
  runs/20260430_174500/tweets_with_sentiment.csv
  runs/20260430_174500/tweets_with_topics.csv
  runs/20260430_174500/topic_info.csv
  runs/20260430_174500/metadata.json
  latest_run.json (manifest at bucket root)
  ↓
Dashboard reads:
  1. Try: Fetch latest_run.json from Spaces
  2. Download files from runs/TIMESTAMP/
  3. Fallback: Read local data/output/ if Spaces fails
```

## Manifest Schema

```json
{
  "run_id": "20260430_174500",
  "timestamp": "2026-04-30T17:45:00+07:00",
  "git_commit": "8782aee",
  "duration_seconds": 3847,
  "status": "success",
  "files": {
    "tweets_with_sentiment": {
      "path": "runs/20260430_174500/tweets_with_sentiment.csv",
      "rows": 107375,
      "size_mb": 71.2,
      "md5": "a3f5c8..."
    },
    "tweets_with_topics": {
      "path": "runs/20260430_174500/tweets_with_topics.csv",
      "rows": 300235,
      "size_mb": 73.1,
      "md5": "b2e9d1..."
    },
    "topic_info": {
      "path": "runs/20260430_174500/topic_info.csv",
      "rows": 52,
      "size_mb": 0.05,
      "md5": "c4a7f2..."
    }
  },
  "stats": {
    "total_tweets": 107375,
    "sentiment": {
      "negative": 43145,
      "neutral": 33284,
      "positive": 30946
    },
    "topics_discovered": 51,
    "outliers": 45774
  }
}
```

## Files Modified

### New Files Created (5)
1. `scripts/generate_manifest.py` - Manifest generation module
2. `scripts/upload_run.py` - Timestamped upload script
3. `dashboard/spaces_loader.py` - Spaces data loader utility
4. `dashboard/pages/7_run_history.py` - Run history viewer
5. `IMPLEMENTATION_SUMMARY.md` - This file

### Files Modified (10)
1. `scripts/run_full_pipeline.sh` - Added run_id capture and manifest generation
2. `scripts/monitor_pipeline.sh` - Added Spaces status monitoring
3. `dashboard/app.py` - Integrated Spaces loader with sidebar
4. `dashboard/pages/0_temporal.py` - Updated to use Spaces loader
5. `dashboard/pages/1_sentiment.py` - Updated to use Spaces loader
6. `dashboard/pages/2_topics.py` - Updated to use Spaces loader
7. `dashboard/pages/3_engagement.py` - Updated to use Spaces loader
8. `dashboard/pages/4_explorer.py` - Updated to use Spaces loader
9. `dashboard/pages/5_spikes.py` - Updated to use Spaces loader
10. `dashboard/pages/6_analysis.py` - Added comment (analysis CSVs stay local)
11. `scripts/PIPELINE_README.md` - Comprehensive documentation update

## Key Features

### ✅ Versioning
- Every pipeline run gets unique timestamp ID
- All outputs stored in `runs/{run_id}/` directory
- Historical runs preserved indefinitely
- No local disk bloat (local files overwritten)

### ✅ Discovery
- `latest_run.json` manifest at bucket root
- Dashboard automatically finds current run
- Run history page lists all available runs

### ✅ Metadata
- Comprehensive manifest with row counts, file sizes, MD5 hashes
- Statistics: sentiment distribution, topic counts, outliers
- Git commit hash for reproducibility
- Pipeline duration tracking

### ✅ Resilience
- 3-retry logic with exponential backoff
- Partial upload cleanup on failure
- Dashboard fallback to local files
- Clear error messages

### ✅ Monitoring
- Current run_id displayed in monitor
- Spaces connection status
- Upload process tracking
- Run metadata in dashboard sidebar

## Benefits

1. **Data Recovery:** Revert to any previous run if needed
2. **Comparison:** Compare results across different pipeline runs
3. **Audit Trail:** Know exactly when data was generated
4. **Reproducibility:** Git hash links data to code version + fresh processing each run
5. **Resilience:** Dashboard works even if Spaces is down
6. **No Bloat:** Local files overwritten, Spaces keeps history
7. **Consistency:** No caching ensures identical processing for each run

## Testing Checklist

- [ ] Run `python3 scripts/generate_manifest.py` standalone
- [ ] Run full pipeline and verify `metadata.json` created
- [ ] Check that `runs/{run_id}/` directory created in Spaces
- [ ] Verify `latest_run.json` uploaded to bucket root
- [ ] Open dashboard and confirm Spaces connection (🌐 icon)
- [ ] Navigate to Run History page and view all runs
- [ ] Simulate Spaces outage and verify local fallback works
- [ ] Check monitor script shows run_id and Spaces status
- [ ] Verify retry logic by temporarily breaking Spaces connection

## Next Steps (Optional Enhancements)

1. **Cleanup Policy:** Auto-delete runs older than N days
2. **Compression:** Gzip CSVs before upload to save space
3. **Incremental Upload:** Only upload changed files
4. **Dashboard Caching:** Cache downloaded CSVs locally for performance
5. **Email Notifications:** Alert on pipeline success/failure
6. **Metrics Dashboard:** Track pipeline duration trends over time
7. **Diff Viewer:** Compare two runs side-by-side
8. **Rollback Command:** One-click revert to previous run

## Deployment Notes

- No changes needed to GitHub Actions deploy workflow
- Dashboard automatically uses new loader on next deployment
- Existing local files remain as fallback
- First run after deployment will create first timestamped version
- All subsequent runs will be versioned automatically

---

**Implementation Date:** 2026-04-30  
**Status:** ✅ Complete  
**All 11 tasks completed successfully**
