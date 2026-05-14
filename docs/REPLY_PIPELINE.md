# MBG Reply Data Pipeline

## Overview

Processes 509k reply tweets through 7 stages: conversion, enrichment, depth classification, filtering, language detection, preprocessing, and sentiment analysis.

**Key Decision**: Skips relevance filtering (R7 in original spec) because replies inherit context from parent posts that already passed IndoBERT filtering.

## Pipeline Stages

| Stage | Script | Description | Runtime (sample) |
|-------|--------|-------------|------------------|
| R1 | `r1_jsonl_to_csv.py` | JSONL → CSV conversion | ~5s |
| R2 | `r2_enrich_metadata.py` | Fill nulls from parent join | ~5s |
| R3 | `r3_add_depth.py` | Classify depth-1 vs depth-2 | ~3s |
| R4 | `r4_filter_text.py` | Remove spam/short/duplicates | ~5s |
| R5 | `r5_tag_language.py` | Language detection | ~30s |
| R6 | `r6_preprocess_text.py` | Sastrawi + spaCy cleaning | ~60s |
| R7 | `r7_sentiment.py` | Sentiment classification | ~120s |

**Total sample runtime**: ~4 minutes for 1000 replies  
**Estimated full runtime**: ~5-6 hours for 509k replies

## Test Results (1000 reply sample)

```
Input:     998 replies
After R4:  805 replies (193 filtered)
After R6:  799 replies (6 empty after preprocessing)
Final:     799 replies with sentiment

Sentiment breakdown:
- Negative: 539 (67.5%)
- Positive: 160 (20.0%)
- Neutral:  100 (12.5%)

Depth breakdown:
- Depth 0 (unknown parent): 563
- Depth 1 (→ parent post):  435
```

## VPS Setup

All scripts located on VPS at: `/opt/mbg/scripts/replies/`

```bash
# SSH to VPS
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179

# Directory structure
/opt/mbg/
├── data/
│   ├── consolidated/     # Input JSONL files
│   └── output/          # Final outputs
├── scripts/replies/     # Pipeline scripts
└── logs/               # Pipeline logs
```

## Running the Pipeline

### Test with sample (1000 replies)
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179
cd /opt/mbg
./scripts/replies/run_reply_pipeline.sh data/consolidated/replies_sample.jsonl
```

### Full dataset (509k replies)
```bash
# 1. Download full dataset from DO Spaces to VPS
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179
s3cmd get s3://mbg-scraper-network-20260419071440/replies_all_dedup.jsonl \
  /opt/mbg/data/consolidated/replies_all_dedup.jsonl

# 2. Run in screen session (5-6 hours)
screen -S reply_pipeline
cd /opt/mbg
./scripts/replies/run_reply_pipeline.sh data/consolidated/replies_all_dedup.jsonl
# Detach: Ctrl+A, D
# Reattach: screen -r reply_pipeline

# 3. Monitor progress
tail -f /opt/mbg/logs/reply_pipeline_*.log
```

## Output Files

```
data/consolidated/
├── replies_all_dedup.csv              # R1: Raw CSV
├── replies_all_dedup_enriched.csv     # R2: Metadata filled
├── replies_all_dedup_depth.csv        # R3: Depth classified
├── replies_all_dedup_filtered.csv     # R4: Spam removed
├── replies_all_dedup_rejected.csv     # R4: Rejected rows
├── replies_all_dedup_tagged.csv       # R5: Language detected
├── replies_all_dedup_preprocessed.csv # R6: Text cleaned
└── replies_all_dedup_sentiment.csv    # R7: Final output ✓
```

## Next Steps (Not Yet Implemented)

- R8: Build reply tree structure
- R9: Reply-specific analysis (controversy, sentiment shift)
- R10: Dashboard integration

## Notes

- **No relevance filtering**: Replies inherit relevance from parents
- **Depth preservation**: depth-1 and depth-2 kept separate for analysis
- **Rejection tracking**: All filtered rows saved with reasons
- **Checkpoint support**: R7 can resume from checkpoint if interrupted
