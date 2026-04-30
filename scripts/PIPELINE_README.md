# MBG Pipeline Scripts

## Overview
Complete MBG analysis pipeline with **timestamped versioning** to DigitalOcean Spaces. Each pipeline run is versioned with a unique run_id, allowing historical tracking and data recovery.

**Every run processes from scratch** - no caching, no skipping. Checkpoints and embeddings are cleared at start to ensure fresh results.

## Architecture

```
Pipeline Run (20260430_174500)
  ↓
Local: /opt/mbg/data/output/*.csv (current files, overwritten each run)
  ↓
[On Success] Upload to Spaces:
  runs/20260430_174500/tweets_with_sentiment.csv
  runs/20260430_174500/tweets_with_topics.csv
  runs/20260430_174500/topic_info.csv
  runs/20260430_174500/metadata.json
  latest_run.json (manifest pointing to this run)
  ↓
Dashboard reads:
  1. Try: Fetch latest_run.json from Spaces
  2. Download files from runs/TIMESTAMP/
  3. Fallback: Read local data/output/ if Spaces fails
```

## Scripts

### 1. `run_full_pipeline.sh` - Complete Pipeline Orchestrator
Runs all 9 steps in sequence:
0. **Clear caches** (sentiment checkpoints, topic embeddings)
1. Inference (IndoBERT relevance classification) - **always runs**
2. Language detection (langdetect)
3. Text preprocessing (Sastrawi + spaCy)
4. Sentiment analysis (dual-model: Indonesian + English) - **no checkpoints**
5. Topic modeling (BERTopic) - **no embedding cache**
6. Data validation
7. **Manifest generation** (metadata.json with run_id, stats, file info)
8. **Timestamped upload to DO Spaces** (runs/{run_id}/)
9. Summary report

**Every run processes from scratch** - no file existence checks, no caching, no skipping.

**Usage:**
```bash
ssh root@206.189.157.179
cd /opt/mbg
nohup bash scripts/run_full_pipeline.sh > logs/pipeline_run.log 2>&1 &
```

**Output:** 
- Timestamped log: `/opt/mbg/logs/pipeline_{RUN_ID}.log`
- Local files: `data/output/*.csv` (overwritten each run)
- Spaces: `s3://mbg-scraper-network-20260419071440/runs/{RUN_ID}/`
- Manifest: `data/output/metadata.json` (local) + Spaces

**Run ID Format:** `YYYYMMDD_HHMMSS` (e.g., `20260430_174500`)

---

### 2. `generate_manifest.py` - Manifest Generator
Creates comprehensive metadata for each pipeline run.

**Manifest Schema:**
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
    }
  },
  "stats": {
    "total_tweets": 107375,
    "sentiment": {"negative": 43145, "neutral": 33284, "positive": 30946},
    "topics_discovered": 51,
    "outliers": 45774
  }
}
```

**Usage:**
```bash
# Standalone (for testing)
python3 scripts/generate_manifest.py 20260430_174500 3847
# Output: data/output/metadata.json
```

---

### 3. `upload_run.py` - Timestamped Spaces Uploader
Uploads pipeline run to DigitalOcean Spaces with versioning.

**Features:**
- Reads metadata.json for run_id and file info
- Uploads to `runs/{run_id}/` directory
- Generates and uploads `latest_run.json` manifest
- **Retry logic:** 3 attempts with 5s backoff for transient errors
- **Cleanup:** Removes partial uploads on failure
- **Verification:** MD5 checksums for data integrity

**Usage:**
```bash
# Called automatically by run_full_pipeline.sh
python3 scripts/upload_run.py
```

**Manual upload:**
```bash
# If pipeline succeeded but upload failed
cd /opt/mbg
source venv/bin/activate
python3 scripts/upload_run.py
```

---

### 4. `monitor_pipeline.sh` - Full Status Monitor
Shows detailed status of all pipeline components:
- **Current run info** (run_id, status from metadata.json)
- **Spaces status** (connection, latest run in Spaces)
- Running processes (with PIDs, including upload_run.py)
- Output file status (rows, size, last modified)
- Active checkpoints
- Recent log entries
- System resources (CPU, memory, disk)
- Quick sentiment statistics

**Usage:**
```bash
ssh root@206.189.157.179
cd /opt/mbg
bash scripts/monitor_pipeline.sh
```

**Tip:** Run in watch mode for live updates:
```bash
watch -n 10 'bash scripts/monitor_pipeline.sh'
```

---

### 5. `pipeline_status.sh` - Quick Status Check
Single-line summary of pipeline state. Perfect for quick checks or scripting.

**Usage:**
```bash
ssh root@206.189.157.179
cd /opt/mbg
bash scripts/pipeline_status.sh
```

**Output examples:**
- `IDLE | Files: ✓rel ✓sent ✓top`
- `RUNNING: SENT | Files: ✓rel [CHECKPOINT]`
- `RUNNING: INF TAG | Files: ✓rel`

---

## Pipeline Data Flow

```
final_parent_x_posts_mbg.csv (raw, 55k tweets)
    ↓
[1] inference.py
    ↓
tweets_relevant.csv (301k tweets classified as RELEVANT)
    ↓
[2] tag_language.py
    ↓
tweets_relevant_tagged.csv (+ detected_lang, sentiment_model)
    ↓
[3] preprocess_text.py
    ↓
tweets_preprocessed.csv (+ text_clean_light, text_clean_topic)
    ↓
[4] run_sentiment.py
    ↓
tweets_with_sentiment.csv (+ sentiment_normalized) — 107k rows
    ↓
[5] run_topics.py
    ↓
tweets_with_topics.csv (+ topic_id, topic_prob) + topic_info.csv
    ↓
[6] validate_data_contract.py
    ↓
[7] generate_manifest.py → metadata.json (run_id, stats, file info)
    ↓
[8] upload_run.py → s3://mbg-scraper-network-20260419071440/runs/{RUN_ID}/
    ├── tweets_with_sentiment.csv
    ├── tweets_with_topics.csv
    ├── topic_info.csv
    ├── metadata.json
    └── latest_run.json (manifest at bucket root)
```

---

## Key Files

### Input
- `/opt/mbg/final_parent_x_posts_mbg.csv` - Raw scraped tweets

### Intermediate
- `data/processed/tweets_relevant.csv` - After inference
- `data/processed/tweets_relevant_tagged.csv` - After language detection
- `data/processed/tweets_preprocessed.csv` - After text cleaning

### Output (local, overwritten each run)
- `data/output/tweets_with_sentiment.csv` - Main file (107k tweets)
- `data/output/tweets_with_topics.csv` - With topic assignments
- `data/output/topic_info.csv` - Topic metadata (51 topics)
- `data/output/metadata.json` - **Run manifest** (run_id, stats, file info)
- `data/output/latest_run.json` - **Latest run pointer** (uploaded to Spaces)

### Versioned in Spaces
- `s3://mbg-scraper-network-20260419071440/runs/{RUN_ID}/` - Timestamped run directory
  - `tweets_with_sentiment.csv`
  - `tweets_with_topics.csv`
  - `topic_info.csv`
  - `metadata.json`
- `s3://mbg-scraper-network-20260419071440/latest_run.json` - Current run manifest

---

## Common Operations

### Run full pipeline from scratch
```bash
ssh root@206.189.157.179
cd /opt/mbg
# Run pipeline (automatically clears caches at start)
nohup bash scripts/run_full_pipeline.sh > logs/pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1 &
# Monitor
watch -n 10 'bash scripts/monitor_pipeline.sh'
```

**Note:** Every run processes from scratch. Caches are automatically cleared.

### Check current run status
```bash
# View current run metadata
cat data/output/metadata.json | python3 -m json.tool

# Check what's in Spaces
s3cmd ls s3://mbg-scraper-network-20260419071440/runs/

# View latest run manifest
s3cmd get s3://mbg-scraper-network-20260419071440/latest_run.json - | python3 -m json.tool
```

### Resume interrupted sentiment job
```bash
# Checkpoint exists, just restart
cd /opt/mbg
source venv/bin/activate
nohup python3 run_sentiment.py > logs/sentiment_resume.log 2>&1 &
```

### Kill stale processes
```bash
# Check what's running
bash scripts/pipeline_status.sh
# Kill specific process
pkill -f "run_sentiment.py"
# Or kill all pipeline processes
pkill -f "inference.py|run_sentiment.py|run_topics.py|upload_run.py"
```

### Download specific run from Spaces
```bash
# List all runs
s3cmd ls s3://mbg-scraper-network-20260419071440/runs/

# Download specific run
RUN_ID="20260430_174500"
mkdir -p downloads/$RUN_ID
s3cmd get s3://mbg-scraper-network-20260419071440/runs/$RUN_ID/tweets_with_sentiment.csv downloads/$RUN_ID/
s3cmd get s3://mbg-scraper-network-20260419071440/runs/$RUN_ID/tweets_with_topics.csv downloads/$RUN_ID/
s3cmd get s3://mbg-scraper-network-20260419071440/runs/$RUN_ID/topic_info.csv downloads/$RUN_ID/
s3cmd get s3://mbg-scraper-network-20260419071440/runs/$RUN_ID/metadata.json downloads/$RUN_ID/
```

### Download current outputs to local machine
```bash
# From local machine
cd /Users/fatwa/Documents/coding/mbg-analyst/analysis
scp -i ~/.ssh/mbg_scraper_do_ed25519 \
  root@206.189.157.179:/opt/mbg/data/output/tweets_with_sentiment.csv \
  root@206.189.157.179:/opt/mbg/data/output/tweets_with_topics.csv \
  root@206.189.157.179:/opt/mbg/data/output/topic_info.csv \
  data/processed/
```

---

## Troubleshooting

### Pipeline stuck?
```bash
bash scripts/monitor_pipeline.sh
# Check if process is actually running or hung
top -bn1 | grep python
# Check logs
tail -f logs/pipeline_*.log
```

### Upload to Spaces failed?
```bash
# Check Spaces connectivity
s3cmd ls s3://mbg-scraper-network-20260419071440/

# Retry upload manually
cd /opt/mbg
source venv/bin/activate
python3 scripts/upload_run.py

# Check if metadata.json exists
cat data/output/metadata.json
```

### Dashboard shows "Local Files" instead of Spaces?
```bash
# Check if latest_run.json exists in Spaces
s3cmd get s3://mbg-scraper-network-20260419071440/latest_run.json -

# List all runs
s3cmd ls s3://mbg-scraper-network-20260419071440/runs/

# Dashboard will automatically fallback to local files if Spaces unavailable
# This is expected behavior - no action needed if local files are current
```

### View historical runs?
```bash
# List all timestamped runs
s3cmd ls s3://mbg-scraper-network-20260419071440/runs/

# Download specific run
RUN_ID="20260430_174500"
s3cmd get s3://mbg-scraper-network-20260419071440/runs/$RUN_ID/metadata.json -

# Or use dashboard: http://206.189.157.179:8501/run_history
```

### Out of memory?
```bash
free -h
# Kill non-essential processes
# Or restart VPS
reboot
```

### Data validation fails?
```bash
python3 scripts/validate_data_contract.py
# Check which file/column is missing
# Re-run the specific step that produces it
```

### s3cmd not configured?
```bash
# Check s3cmd config
cat ~/.s3cfg

# Test connection
s3cmd ls s3://mbg-scraper-network-20260419071440/

# If fails, reconfigure (requires DO Spaces keys)
s3cmd --configure
```

---

## VPS Details
- **IP:** 206.189.157.179
- **Region:** Singapore (sgp1)
- **Specs:** 4vCPU, 8GB RAM
- **SSH:** `ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179`
- **Dashboard:** http://206.189.157.179:8501 (password: bismillahcair)

---

## Dashboard Features

The Streamlit dashboard automatically loads data from DigitalOcean Spaces with local fallback:

### Data Loading
1. **Spaces (Primary):** Fetches `latest_run.json` and downloads CSVs from `runs/{run_id}/`
2. **Local (Fallback):** Reads from `/opt/mbg/data/output/` if Spaces unavailable
3. **Status Indicator:** Sidebar shows connection status (🌐 Spaces / 💾 Local / ❌ Offline)

### Pages
- **Home:** Overview with sentiment trends and key metrics
- **Temporal:** Volume trends, hourly patterns, negativity acceleration
- **Sentiment:** Distribution, engagement, topic breakdown
- **Topics:** BERTopic clusters, theme evolution
- **Engagement:** Virality, query effectiveness, regional gaps
- **Explorer:** Filter and search all tweets
- **Spikes:** Anomaly detection and spike analysis
- **Analysis:** Research findings and statistical tests
- **Run History:** View all historical runs, metadata, and download links

### Run Metadata Display
Sidebar shows current run information:
- Run ID (timestamp)
- Pipeline duration
- Git commit hash
- Total tweets and sentiment distribution

### Viewing Historical Runs
Navigate to **Run History** page to:
- List all runs from Spaces
- View metadata table (run_id, timestamp, duration, stats)
- Select a run to see detailed metadata
- Get download commands for specific runs

---

## Benefits of Timestamped Versioning

1. **Data Recovery:** Revert to any previous run if current data is corrupted
2. **Comparison:** Compare sentiment trends across different pipeline runs
3. **Audit Trail:** Track when data was generated and what changed
4. **Reproducibility:** Git commit hash links data to exact code version
5. **Resilience:** Dashboard works even if Spaces is temporarily unavailable
6. **No Local Bloat:** Local files overwritten each run, Spaces keeps history
