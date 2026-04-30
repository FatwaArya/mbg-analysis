# MBG Pipeline Scripts

## Overview
Three scripts to run and monitor the complete MBG analysis pipeline on the VPS.

## Scripts

### 1. `run_full_pipeline.sh` - Complete Pipeline Orchestrator
Runs all 7 steps in sequence:
1. Inference (IndoBERT relevance classification)
2. Language detection (langdetect)
3. Text preprocessing (Sastrawi + spaCy)
4. Sentiment analysis (dual-model: Indonesian + English)
5. Topic modeling (BERTopic)
6. Data validation
7. Upload to DO Spaces

**Usage:**
```bash
ssh root@206.189.157.179
cd /opt/mbg
nohup bash scripts/run_full_pipeline.sh > logs/pipeline_run.log 2>&1 &
```

**Output:** Creates timestamped log in `/opt/mbg/logs/pipeline_YYYYMMDD_HHMMSS.log`

---

### 2. `monitor_pipeline.sh` - Full Status Monitor
Shows detailed status of all pipeline components:
- Running processes (with PIDs)
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

### 3. `pipeline_status.sh` - Quick Status Check
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
[7] Upload to s3://mbg-scraper-network-20260419071440/
```

---

## Key Files

### Input
- `/opt/mbg/final_parent_x_posts_mbg.csv` - Raw scraped tweets

### Intermediate
- `data/processed/tweets_relevant.csv` - After inference
- `data/processed/tweets_relevant_tagged.csv` - After language detection
- `data/processed/tweets_preprocessed.csv` - After text cleaning

### Output (used by dashboard)
- `data/output/tweets_with_sentiment.csv` - Main file (107k tweets)
- `data/output/tweets_with_topics.csv` - With topic assignments
- `data/output/topic_info.csv` - Topic metadata (51 topics)

### Checkpoints
- `data/.sentiment_checkpoint.csv` - Sentiment progress (auto-resume)
- `data/.topic_embeddings.npy` - Cached embeddings (reusable)

---

## Common Operations

### Run full pipeline from scratch
```bash
ssh root@206.189.157.179
cd /opt/mbg
# Clear old checkpoints
rm -f data/.sentiment_checkpoint.csv data/.topic_embeddings.npy
# Run pipeline
nohup bash scripts/run_full_pipeline.sh > logs/pipeline_$(date +%Y%m%d_%H%M%S).log 2>&1 &
# Monitor
watch -n 10 'bash scripts/monitor_pipeline.sh'
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
pkill -f "inference.py|run_sentiment.py|run_topics.py"
```

### Download outputs to local
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

### Out of memory?
```bash
free -h
# Kill non-essential processes
# Or restart VPS
reboot
```

### Checkpoint corrupted?
```bash
rm data/.sentiment_checkpoint.csv
# Restart from beginning
python3 run_sentiment.py
```

### Data validation fails?
```bash
python3 scripts/validate_data_contract.py
# Check which file/column is missing
# Re-run the specific step that produces it
```

---

## VPS Details
- **IP:** 206.189.157.179
- **Region:** Singapore (sgp1)
- **Specs:** 4vCPU, 8GB RAM
- **SSH:** `ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179`
- **Dashboard:** http://206.189.157.179:8501 (password: bismillahcair)
