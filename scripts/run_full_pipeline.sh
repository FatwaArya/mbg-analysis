#!/bin/bash
# Complete MBG Analysis Pipeline Orchestrator
# Runs: Inference → Language Tagging → Preprocessing → Sentiment → Topics → Validation → Upload

set -e
cd /opt/mbg
source venv/bin/activate

LOGDIR="/opt/mbg/logs"
mkdir -p "$LOGDIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PIPELINE_LOG="$LOGDIR/pipeline_${TIMESTAMP}.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$PIPELINE_LOG"
}

log "=========================================="
log "MBG PIPELINE START"
log "=========================================="

# Step 1: Inference (if needed)
if [ ! -f "data/processed/tweets_relevant.csv" ]; then
    log "Step 1: Running inference..."
    python3 inference.py 2>&1 | tee -a "$PIPELINE_LOG"
    log "✓ Inference complete"
else
    log "Step 1: Skipping inference (tweets_relevant.csv exists)"
fi

# Step 2: Language Tagging
log "Step 2: Running language detection..."
python3 scripts/tag_language.py 2>&1 | tee -a "$PIPELINE_LOG"
log "✓ Language tagging complete"

# Step 3: Text Preprocessing
log "Step 3: Running text preprocessing..."
python3 scripts/preprocess_text.py 2>&1 | tee -a "$PIPELINE_LOG"
log "✓ Preprocessing complete"

# Step 4: Sentiment Analysis
log "Step 4: Running sentiment analysis..."
python3 run_sentiment.py 2>&1 | tee -a "$PIPELINE_LOG"
log "✓ Sentiment analysis complete"

# Step 5: Topic Modeling
log "Step 5: Running topic modeling..."
python3 run_topics.py 2>&1 | tee -a "$PIPELINE_LOG"
log "✓ Topic modeling complete"

# Step 6: Data Validation
log "Step 6: Validating data contract..."
python3 scripts/validate_data_contract.py 2>&1 | tee -a "$PIPELINE_LOG"
if [ $? -ne 0 ]; then
    log "✗ Data validation FAILED. Aborting."
    exit 1
fi
log "✓ Data validation passed"

# Step 7: Upload to DO Spaces
log "Step 7: Uploading to DO Spaces..."
BUCKET="s3://mbg-scraper-network-20260419071440"

s3cmd put data/output/tweets_with_sentiment.csv  $BUCKET/output/ 2>&1 | tee -a "$PIPELINE_LOG"
s3cmd put data/output/tweets_with_topics.csv     $BUCKET/output/ 2>&1 | tee -a "$PIPELINE_LOG"
s3cmd put data/output/topic_info.csv             $BUCKET/output/ 2>&1 | tee -a "$PIPELINE_LOG"
s3cmd put data/processed/tweets_relevant.csv     $BUCKET/processed/ 2>&1 | tee -a "$PIPELINE_LOG"

log "✓ Upload complete"

# Step 8: Generate Summary
log "=========================================="
log "PIPELINE SUMMARY"
log "=========================================="
log "tweets_relevant:        $(wc -l < data/processed/tweets_relevant.csv) rows"
log "tweets_with_sentiment:  $(wc -l < data/output/tweets_with_sentiment.csv) rows"
log "tweets_with_topics:     $(wc -l < data/output/tweets_with_topics.csv) rows"
log "topics discovered:      $(tail -n +2 data/output/topic_info.csv | wc -l)"
log "=========================================="
log "Pipeline log: $PIPELINE_LOG"
log "PIPELINE COMPLETE"
log "=========================================="
