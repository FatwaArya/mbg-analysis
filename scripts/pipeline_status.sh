#!/bin/bash
# Quick pipeline status - single line summary

cd /opt/mbg 2>/dev/null || cd .

# Check what's running
RUNNING=""
pgrep -f "inference.py" >/dev/null && RUNNING="${RUNNING}INF "
pgrep -f "tag_language.py" >/dev/null && RUNNING="${RUNNING}TAG "
pgrep -f "preprocess_text.py" >/dev/null && RUNNING="${RUNNING}PRE "
pgrep -f "run_sentiment.py" >/dev/null && RUNNING="${RUNNING}SENT "
pgrep -f "run_topics.py" >/dev/null && RUNNING="${RUNNING}TOP "

# Check output files
FILES=""
[ -f "data/processed/tweets_relevant.csv" ] && FILES="${FILES}✓rel "
[ -f "data/output/tweets_with_sentiment.csv" ] && FILES="${FILES}✓sent "
[ -f "data/output/tweets_with_topics.csv" ] && FILES="${FILES}✓top "

# Checkpoint status
CHECKPOINT=""
[ -f "data/.sentiment_checkpoint.csv" ] && CHECKPOINT="[CHECKPOINT]"

if [ -z "$RUNNING" ]; then
    echo "IDLE | Files: ${FILES:-none} $CHECKPOINT"
else
    echo "RUNNING: $RUNNING | Files: ${FILES:-none} $CHECKPOINT"
fi
