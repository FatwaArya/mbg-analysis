# Reply Pipeline Execution Checklist

## ✅ Completed

- [x] Created feature branch `feature/reply-pipeline`
- [x] Built 7 pipeline scripts (R1-R7)
- [x] Deployed all scripts to VPS `/opt/mbg/scripts/replies/`
- [x] Created master pipeline runner `run_reply_pipeline.sh`
- [x] Tested on 1000 reply sample
- [x] Verified all stages work correctly
- [x] Created launcher script `start_reply_pipeline.sh`
- [x] Documented in `REPLY_PIPELINE.md`
- [x] Committed and pushed to GitHub

## 📋 Ready to Execute

### Option 1: Run Full Dataset Now

```bash
# From local machine (kicks off VPS processing)
./scripts/start_reply_pipeline.sh

# Monitor progress
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  'tail -f /opt/mbg/logs/reply_pipeline_*.log'

# Expected: 5-6 hours for 509k replies
```

### Option 2: Manual VPS Execution

```bash
# SSH to VPS
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179

# Download full dataset (if not exists)
s3cmd get s3://mbg-scraper-network-20260419071440/replies_all_dedup.jsonl \
  /opt/mbg/data/consolidated/replies_all_dedup.jsonl

# Run in screen
screen -S reply_pipeline
cd /opt/mbg
./scripts/replies/run_reply_pipeline.sh data/consolidated/replies_all_dedup.jsonl

# Detach: Ctrl+A, D
# Reattach: screen -r reply_pipeline
```

## 📊 Expected Output

After completion, you'll have:

```
/opt/mbg/data/consolidated/replies_all_dedup_sentiment.csv
```

With columns:
- All original reply fields
- `depth` (0, 1, or 2)
- `detected_lang` (id, en, etc.)
- `text_clean_light` (for sentiment)
- `text_clean_topic` (for topic modeling)
- `sentiment_normalized` (positive/negative/neutral)
- `sentiment_score` (confidence)

## 🔍 Verification Commands

```bash
# Check row count
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  "wc -l /opt/mbg/data/consolidated/replies_all_dedup_sentiment.csv"

# Check sentiment distribution
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  "tail -n +2 /opt/mbg/data/consolidated/replies_all_dedup_sentiment.csv | \
   cut -d',' -f<sentiment_col> | sort | uniq -c"

# Download to local
scp -i ~/.ssh/mbg_scraper_do_ed25519 \
  root@206.189.157.179:/opt/mbg/data/consolidated/replies_all_dedup_sentiment.csv \
  data/processed/
```

## 🚀 What's Next (Not Implemented Yet)

After R7 completes, you can optionally implement:

1. **R8: Reply Tree Construction**
   - Link replies to parents
   - Build conversation threads
   - Calculate reply metrics per parent

2. **R9: Reply-Specific Analysis**
   - Controversy scores (mixed sentiment replies)
   - Sentiment shift (parent → reply)
   - Talk vs amplify ratio (replies/RTs)
   - Depth-1 vs depth-2 patterns

3. **R10: Dashboard Integration**
   - Add reply analysis page
   - Visualize sentiment shifts
   - Show most controversial posts

These are separate tasks and can be done after R7 completes.

## 📝 Notes

- **No relevance filter**: Replies inherit relevance from parents
- **Depth preserved**: depth-1 and depth-2 kept separate
- **All rejections tracked**: See `*_rejected.csv` files
- **Resumable**: R7 has checkpoint support if interrupted
