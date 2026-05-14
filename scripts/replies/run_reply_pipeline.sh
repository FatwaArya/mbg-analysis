#!/bin/bash
# Master reply pipeline runner
set -e

INPUT="${1:-/opt/mbg/data/consolidated/replies_sample.jsonl}"
LOG="/opt/mbg/logs/reply_pipeline_$(date +%Y%m%d_%H%M%S).log"

echo "=== MBG Reply Pipeline ===" | tee -a "$LOG"
echo "Input: $INPUT" | tee -a "$LOG"
echo "Started: $(date)" | tee -a "$LOG"

cd /opt/mbg
source venv/bin/activate

echo -e "\n[R1] JSONL → CSV" | tee -a "$LOG"
python3 scripts/replies/r1_jsonl_to_csv.py "$INPUT" 2>&1 | tee -a "$LOG"

CSV="${INPUT%.jsonl}.csv"
echo -e "\n[R2] Metadata enrichment" | tee -a "$LOG"
python3 scripts/replies/r2_enrich_metadata.py "$CSV" 2>&1 | tee -a "$LOG"

ENRICHED="${CSV%.csv}_enriched.csv"
echo -e "\n[R3] Depth classification" | tee -a "$LOG"
python3 scripts/replies/r3_add_depth.py "$ENRICHED" 2>&1 | tee -a "$LOG"

DEPTH="${CSV%.csv}_depth.csv"
echo -e "\n[R4] Text filtering" | tee -a "$LOG"
python3 scripts/replies/r4_filter_text.py "$DEPTH" 2>&1 | tee -a "$LOG"

FILTERED="${CSV%.csv}_filtered.csv"
echo -e "\n[R5] Language detection" | tee -a "$LOG"
python3 scripts/replies/r5_tag_language.py "$FILTERED" 2>&1 | tee -a "$LOG"

TAGGED="${CSV%.csv}_tagged.csv"
echo -e "\n[R6] Text preprocessing" | tee -a "$LOG"
python3 scripts/replies/r6_preprocess_text.py "$TAGGED" 2>&1 | tee -a "$LOG"

PREPROCESSED="${CSV%.csv}_preprocessed.csv"
echo -e "\n[R7] Sentiment analysis" | tee -a "$LOG"
python3 scripts/replies/r7_sentiment.py "$PREPROCESSED" 2>&1 | tee -a "$LOG"

SENTIMENT="${CSV%.csv}_sentiment.csv"
echo -e "\n=== PIPELINE COMPLETE ===" | tee -a "$LOG"
echo "Output: $SENTIMENT" | tee -a "$LOG"
echo "Log: $LOG" | tee -a "$LOG"
echo "Finished: $(date)" | tee -a "$LOG"
