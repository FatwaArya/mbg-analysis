#!/bin/bash
# MBG Pipeline Monitor
# Shows real-time status of all pipeline components

set -e
cd /opt/mbg

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "MBG PIPELINE STATUS MONITOR"
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""

# Check running processes
echo -e "${BLUE}[PROCESSES]${NC}"
INFERENCE_PID=$(pgrep -f "python.*inference.py" || echo "")
SENTIMENT_PID=$(pgrep -f "python.*run_sentiment.py" || echo "")
TOPICS_PID=$(pgrep -f "python.*run_topics.py" || echo "")
PREPROCESS_PID=$(pgrep -f "python.*preprocess_text.py" || echo "")
TAGGING_PID=$(pgrep -f "python.*tag_language.py" || echo "")

[ -n "$INFERENCE_PID" ] && echo -e "  ${GREEN}✓${NC} inference.py running (PID: $INFERENCE_PID)" || echo -e "  ${RED}✗${NC} inference.py not running"
[ -n "$TAGGING_PID" ] && echo -e "  ${GREEN}✓${NC} tag_language.py running (PID: $TAGGING_PID)" || echo -e "  ${RED}✗${NC} tag_language.py not running"
[ -n "$PREPROCESS_PID" ] && echo -e "  ${GREEN}✓${NC} preprocess_text.py running (PID: $PREPROCESS_PID)" || echo -e "  ${RED}✗${NC} preprocess_text.py not running"
[ -n "$SENTIMENT_PID" ] && echo -e "  ${GREEN}✓${NC} run_sentiment.py running (PID: $SENTIMENT_PID)" || echo -e "  ${RED}✗${NC} run_sentiment.py not running"
[ -n "$TOPICS_PID" ] && echo -e "  ${GREEN}✓${NC} run_topics.py running (PID: $TOPICS_PID)" || echo -e "  ${RED}✗${NC} run_topics.py not running"
echo ""

# Check output files
echo -e "${BLUE}[OUTPUT FILES]${NC}"
check_file() {
    local file=$1
    local name=$2
    if [ -f "$file" ]; then
        local rows=$(wc -l < "$file" 2>/dev/null || echo "0")
        local size=$(du -h "$file" | cut -f1)
        local mtime=$(stat -c %y "$file" 2>/dev/null | cut -d'.' -f1 || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null)
        echo -e "  ${GREEN}✓${NC} $name: $rows rows, $size (modified: $mtime)"
    else
        echo -e "  ${RED}✗${NC} $name: NOT FOUND"
    fi
}

check_file "data/processed/tweets_relevant.csv" "tweets_relevant"
check_file "data/processed/tweets_relevant_tagged.csv" "tweets_tagged"
check_file "data/processed/tweets_preprocessed.csv" "tweets_preprocessed"
check_file "data/output/tweets_with_sentiment.csv" "tweets_with_sentiment"
check_file "data/output/tweets_with_topics.csv" "tweets_with_topics"
check_file "data/output/topic_info.csv" "topic_info"
echo ""

# Check checkpoint files
echo -e "${BLUE}[CHECKPOINTS]${NC}"
if [ -f "data/.sentiment_checkpoint.csv" ]; then
    CHECKPOINT_ROWS=$(wc -l < data/.sentiment_checkpoint.csv)
    echo -e "  ${YELLOW}⚠${NC} Sentiment checkpoint exists: $CHECKPOINT_ROWS rows processed"
else
    echo -e "  ${GREEN}✓${NC} No active checkpoints"
fi
echo ""

# Check recent logs
echo -e "${BLUE}[RECENT LOGS]${NC}"
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/pipeline_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "  Latest pipeline log: $LATEST_LOG"
        echo "  Last 5 lines:"
        tail -5 "$LATEST_LOG" | sed 's/^/    /'
    else
        echo "  No pipeline logs found"
    fi
else
    echo "  Logs directory not found"
fi
echo ""

# System resources
echo -e "${BLUE}[SYSTEM RESOURCES]${NC}"
echo "  CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% used"
echo "  Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "  Disk: $(df -h /opt/mbg | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
echo ""

# Quick stats if sentiment file exists
if [ -f "data/output/tweets_with_sentiment.csv" ]; then
    echo -e "${BLUE}[QUICK STATS]${NC}"
    source venv/bin/activate
    python3 -c "
import pandas as pd
df = pd.read_csv('data/output/tweets_with_sentiment.csv', usecols=['sentiment_normalized'])
total = len(df)
dist = df['sentiment_normalized'].value_counts()
print(f'  Total tweets: {total:,}')
print(f'  Negative: {dist.get(\"negative\", 0):,} ({dist.get(\"negative\", 0)/total*100:.1f}%)')
print(f'  Neutral:  {dist.get(\"neutral\", 0):,} ({dist.get(\"neutral\", 0)/total*100:.1f}%)')
print(f'  Positive: {dist.get(\"positive\", 0):,} ({dist.get(\"positive\", 0)/total*100:.1f}%)')
" 2>/dev/null || echo "  Unable to compute stats"
fi

echo ""
echo "=========================================="
echo "Monitor complete. Run again to refresh."
echo "=========================================="
