#!/bin/bash
# Complete MBG Analysis Pipeline Orchestrator
# Runs: Inference → Language Tagging → Preprocessing → Sentiment → Topics → Validation → Upload

set -e
cd /opt/mbg

LOCKFILE="/tmp/mbg_pipeline.lock"
if [ -f "$LOCKFILE" ]; then
    LOCK_PID=$(cat "$LOCKFILE")
    if kill -0 "$LOCK_PID" 2>/dev/null; then
        echo "Pipeline already running (PID $LOCK_PID). Aborting."
        exit 1
    fi
fi
echo $$ > "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT INT TERM

source venv/bin/activate

LOGDIR="/opt/mbg/logs"
mkdir -p "$LOGDIR"
RUN_ID=$(date +%Y%m%d_%H%M%S)
PIPELINE_LOG="$LOGDIR/pipeline_${RUN_ID}.log"
START_TIME=$(date +%s)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$PIPELINE_LOG"
}

log "=========================================="
log "MBG PIPELINE START"
log "=========================================="

# Clear checkpoints and caches for fresh run
log "Clearing checkpoints and caches..."
rm -f data/.sentiment_checkpoint.csv
rm -f data/.topic_embeddings.npy
log "✓ Caches cleared"

# Step 1: Inference (always run)
log "Step 1: Running inference..."

# Check if model exists, download if missing
if [ ! -f "model/config.json" ]; then
    log "Model not found locally, downloading from Spaces..."
    mkdir -p model
    s3cmd get --recursive s3://mbg-scraper-network-20260419071440/models/mbg-indobert-finetuned/ model/ 2>&1 | tee -a "$PIPELINE_LOG"
    log "✓ Model downloaded (475MB)"
fi

python3 inference.py 2>&1 | tee -a "$PIPELINE_LOG"
cp data/output/tweets_relevant.csv data/processed/tweets_relevant.csv
log "✓ Inference complete"

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

# Step 7: Generate Manifest
log "Step 7: Generating run manifest..."
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
python3 scripts/generate_manifest.py "$RUN_ID" "$DURATION" 2>&1 | tee -a "$PIPELINE_LOG"
log "✓ Manifest generated (data/output/metadata.json)"

# Step 8: Upload to DO Spaces
log "Step 8: Uploading timestamped run to DO Spaces..."
python3 scripts/upload_run.py 2>&1 | tee -a "$PIPELINE_LOG"
if [ $? -ne 0 ]; then
    log "✗ Upload FAILED. Pipeline completed but data not versioned in Spaces."
    exit 1
fi
log "✓ Upload complete (runs/$RUN_ID/)"

# Step 9: Generate Summary
log "=========================================="
log "PIPELINE SUMMARY"
log "=========================================="
log "Run ID:                 $RUN_ID"
log "Duration:               ${DURATION}s"
log "tweets_relevant:        $(wc -l < data/processed/tweets_relevant.csv) rows"
log "tweets_with_sentiment:  $(wc -l < data/output/tweets_with_sentiment.csv) rows"
log "tweets_with_topics:     $(wc -l < data/output/tweets_with_topics.csv) rows"
log "topics discovered:      $(tail -n +2 data/output/topic_info.csv | wc -l)"
log "=========================================="
log "Pipeline log: $PIPELINE_LOG"
log "PIPELINE COMPLETE"
log "=========================================="
