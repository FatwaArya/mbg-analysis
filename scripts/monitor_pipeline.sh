#!/bin/bash
# MBG Pipeline Monitor - live refresh, accurate step status

cd /opt/mbg

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

LOCKFILE="/tmp/mbg_pipeline.lock"

step_status() {
    local pid_pattern=$1
    local done_file=$2
    local pids
    # Only count processes that are actually alive (filters out dead screen sockets)
    pids=$(pgrep -f "$pid_pattern" 2>/dev/null | while read -r pid; do kill -0 "$pid" 2>/dev/null && echo "$pid"; done | tr '\n' ' ')
    local count
    count=$(echo "$pids" | wc -w)

    # Get pipeline start time from lockfile
    local pipeline_start=0
    [ -f "$LOCKFILE" ] && pipeline_start=$(stat -c '%Y' "$LOCKFILE" 2>/dev/null || echo 0)

    if [ -n "$(echo "$pids" | tr -d ' ')" ] && [ "$count" -gt 1 ]; then
        echo -e "${YELLOW}RUNNING x${count} ⚠ DUPLICATE${NC} (PIDs: $pids)"
    elif [ -n "$(echo "$pids" | tr -d ' ')" ]; then
        echo -e "${GREEN}RUNNING${NC} (PID: $pids)"
    elif [ -n "$done_file" ] && [ -f "$done_file" ]; then
        local file_mtime
        file_mtime=$(stat -c '%Y' "$done_file" 2>/dev/null || echo 0)
        local mtime_str
        mtime_str=$(stat -c '%y' "$done_file" | cut -d'.' -f1)
        if [ "$file_mtime" -ge "$pipeline_start" ]; then
            echo -e "${CYAN}DONE${NC} ($mtime_str)"
        else
            echo -e "${YELLOW}PREV RUN${NC} ($mtime_str)"
        fi
    else
        echo -e "${RED}IDLE${NC}"
    fi
}

file_info() {
    local f=$1
    if [ -f "$f" ]; then
        local rows size mtime
        rows=$(wc -l < "$f")
        size=$(du -h "$f" | cut -f1)
        mtime=$(stat -c '%y' "$f" | cut -d'.' -f1)
        echo -e "${GREEN}✓${NC} $(basename "$f"): $rows rows, $size — $mtime"
    else
        echo -e "${RED}✗${NC} $(basename "$f"): missing"
    fi
}

while true; do
    clear
    echo -e "${BLUE}══════════════════════════════════════════${NC}"
    echo -e "${BLUE}  MBG PIPELINE MONITOR  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}══════════════════════════════════════════${NC}"

    # Pipeline lock
    if [ -f "$LOCKFILE" ]; then
        LOCK_PID=$(cat "$LOCKFILE")
        if kill -0 "$LOCK_PID" 2>/dev/null; then
            echo -e "\n  Pipeline: ${GREEN}RUNNING${NC} (orchestrator PID $LOCK_PID)"
        else
            echo -e "\n  Pipeline: ${YELLOW}STALE LOCK${NC} (PID $LOCK_PID dead — run: rm $LOCKFILE)"
        fi
    else
        echo -e "\n  Pipeline: ${RED}NOT RUNNING${NC}"
    fi

    # Step status
    echo -e "\n${BLUE}[STEPS]${NC}"
    echo -e "  1. inference.py      $(step_status 'python.*inference\.py' '')"
    echo -e "  2. tag_language.py   $(step_status 'python.*tag_language\.py' 'data/.tagging_done')"
    echo -e "  3. preprocess_text   $(step_status 'python.*preprocess_text\.py' 'data/.preprocessing_done')"
    echo -e "  4. run_sentiment.py  $(step_status 'python.*run_sentiment\.py' 'data/output/tweets_with_sentiment.csv')"
    echo -e "  5. run_topics.py     $(step_status 'python.*run_topics\.py' 'data/output/tweets_with_topics.csv')"
    echo -e "  6. validate          $(step_status 'python.*validate_data' '')"
    echo -e "  7. upload_run.py     $(step_status 'python.*upload_run\.py' '')"

    # Sentiment progress
    if pgrep -f 'python.*run_sentiment\.py' > /dev/null 2>&1; then
        SENT_PROGRESS=$(tail -1 /opt/mbg/sentiment.log 2>/dev/null | grep -oP '\d+/\d+' | tail -1)
        [ -n "$SENT_PROGRESS" ] && echo -e "\n  Sentiment progress: ${YELLOW}${SENT_PROGRESS}${NC}"
    fi

    # Output files
    echo -e "\n${BLUE}[OUTPUT FILES]${NC}"
    for f in \
        data/processed/tweets_relevant.csv \
        data/processed/tweets_relevant_tagged.csv \
        data/processed/tweets_preprocessed.csv \
        data/output/tweets_with_sentiment.csv \
        data/output/tweets_with_topics.csv \
        data/output/topic_info.csv; do
        echo -e "  $(file_info "$f")"
    done

    # Latest log tail
    echo -e "\n${BLUE}[LATEST LOG]${NC}"
    LATEST_LOG=$(ls -t logs/pipeline_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        echo "  $LATEST_LOG"
        tail -4 "$LATEST_LOG" | sed 's/^/  /'
    else
        echo "  No pipeline logs found"
    fi

    # Resources
    echo -e "\n${BLUE}[RESOURCES]${NC}"
    echo "  Mem: $(free -h | awk '/^Mem:/ {print $3"/"$2}')"
    echo "  Disk: $(df -h /opt/mbg | awk 'NR==2 {print $3"/"$2" ("$5" used)"}')"

    echo -e "\n${BLUE}══════════════════════════════════════════${NC}"
    echo "  Refreshing every 10s — Ctrl+C to exit"
    sleep 10
done
