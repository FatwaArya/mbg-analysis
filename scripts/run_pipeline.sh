#!/bin/bash
set -e
cd /opt/mbg
source venv/bin/activate

# Wait for tagging to complete (checks every 30 seconds)
echo "[$(date)] Waiting for tagging to complete..."
TAGGING_SIGNAL="/opt/mbg/data/.tagging_done"

while [ ! -f "$TAGGING_SIGNAL" ]; do
  echo "[$(date)] Tagging still running... checking again in 30s"
  sleep 30
done

echo "[$(date)] Tagging complete. Signal found:"
cat "$TAGGING_SIGNAL"

# Clean up signal file before next run
rm "$TAGGING_SIGNAL"

# Wait for preprocessing to complete
echo "[$(date)] Waiting for preprocessing to complete..."
PREPROCESS_SIGNAL="/opt/mbg/data/.preprocessing_done"

while [ ! -f "$PREPROCESS_SIGNAL" ]; do
  echo "[$(date)] Preprocessing still running... checking again in 30s"
  sleep 30
done

echo "[$(date)] Preprocessing complete. Signal found:"
cat "$PREPROCESS_SIGNAL"

# Clean up signal file before next run
rm "$PREPROCESS_SIGNAL"

echo "[$(date)] Starting preprocessing..."
python3 scripts/preprocess_text.py >> /opt/mbg/preprocess.log 2>&1
echo "[$(date)] Preprocessing complete"

echo "[$(date)] Starting sentiment analysis..."
python3 run_sentiment.py >> /opt/mbg/sentiment.log 2>&1
echo "[$(date)] Sentiment complete"

echo "[$(date)] Starting topic modeling..."
python3 run_topics.py >> /opt/mbg/topics.log 2>&1
echo "[$(date)] Topics complete"

echo "[$(date)] Uploading outputs to DO Spaces..."
BUCKET="s3://mbg-scraper-network-20260419071440"

# Core processed files
venv/bin/s3cmd put data/output/tweets_with_sentiment.csv  $BUCKET/output/tweets_with_sentiment.csv
venv/bin/s3cmd put data/output/tweets_with_topics.csv     $BUCKET/output/tweets_with_topics.csv
venv/bin/s3cmd put data/output/topic_info.csv             $BUCKET/output/topic_info.csv

# Processed intermediates
venv/bin/s3cmd put data/processed/tweets_relevant.csv         $BUCKET/processed/tweets_relevant.csv
venv/bin/s3cmd put data/processed/tweets_relevant_tagged.csv  $BUCKET/processed/tweets_relevant_tagged.csv
venv/bin/s3cmd put data/processed/tweets_rejected.csv         $BUCKET/processed/tweets_rejected.csv
venv/bin/s3cmd put data/processed/tweets_borderline.csv       $BUCKET/processed/tweets_borderline.csv

echo "[$(date)] All outputs saved to DO Spaces"
venv/bin/s3cmd ls $BUCKET/output/

# Validate data contract before dashboard deploy
echo "[$(date)] Validating data contract..."
python3 scripts/validate_data_contract.py
if [ $? -ne 0 ]; then
  echo "[ERROR] Data contract validation failed. Aborting."
  exit 1
fi
echo "[$(date)] Data contract valid."

# Pipeline summary
echo "========================================" >> /opt/mbg/logs/pipeline_summary.log
echo "Pipeline run: $(date)" >> /opt/mbg/logs/pipeline_summary.log
echo "tweets_relevant rows: $(wc -l < /opt/mbg/data/processed/tweets_relevant.csv)" >> /opt/mbg/logs/pipeline_summary.log
echo "tweets_preprocessed: $(wc -l < /opt/mbg/data/processed/tweets_preprocessed.csv)" >> /opt/mbg/logs/pipeline_summary.log
echo "tweets_with_sentiment: $(wc -l < /opt/mbg/data/output/tweets_with_sentiment.csv)" >> /opt/mbg/logs/pipeline_summary.log
echo "tweets_with_topics: $(wc -l < /opt/mbg/data/output/tweets_with_topics.csv)" >> /opt/mbg/logs/pipeline_summary.log
echo "========================================" >> /opt/mbg/logs/pipeline_summary.log
