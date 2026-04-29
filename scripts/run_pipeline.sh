#!/bin/bash
set -e
cd /opt/mbg
source venv/bin/activate

echo "=== WAITING FOR TAGGING TO FINISH ==="
while screen -ls | grep -q tagging; do
  echo "tagging still running..."; sleep 30
done
echo "tagging done"

echo "=== PHASE 3: SENTIMENT ==="
python3 run_sentiment.py >> /opt/mbg/sentiment.log 2>&1
echo "sentiment done"

echo "=== PHASE 4: TOPICS ==="
python3 run_topics.py >> /opt/mbg/topics.log 2>&1
echo "topics done"

echo "=== UPLOADING OUTPUTS TO DO SPACES ==="
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

echo "=== ALL DONE — files saved to DO Spaces ==="
venv/bin/s3cmd ls $BUCKET/output/
