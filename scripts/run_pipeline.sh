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

echo "=== UPLOADING TO SPACES ==="
venv/bin/s3cmd put data/output/tweets_with_sentiment.csv s3://mbg-scraper-network-20260419071440/output/tweets_with_sentiment.csv
venv/bin/s3cmd put data/output/tweets_with_topics.csv s3://mbg-scraper-network-20260419071440/output/tweets_with_topics.csv
venv/bin/s3cmd put data/output/topic_info.csv s3://mbg-scraper-network-20260419071440/output/topic_info.csv
echo "=== ALL DONE ==="
