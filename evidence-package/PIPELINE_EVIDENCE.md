# Pipeline Evidence — MBG Discourse Analysis

## Pipeline Run History

All pipeline runs are timestamped and stored in DigitalOcean Spaces under `runs/{run_id}/`.

| Run ID | Files | Status | Storage |
|--------|-------|--------|---------|
| `20260430_112954` | sentiment, topics, topic_info | Success | `s3://bucket/runs/20260430_112954/` |
| `20260430_122619` | sentiment, topics, topic_info | Success | `s3://bucket/runs/20260430_122619/` |
| `20260501_040318` | sentiment, topics, topic_info | Success | `s3://bucket/runs/20260501_040318/` |
| `20260502_063532` | sentiment, topics, topic_info | Success | `s3://bucket/runs/20260502_063532/` |

Latest manifest: `s3://mbg-scraper-network-20260419071440/latest_run.json`

## Storage Contents (DigitalOcean Spaces)

**Bucket:** `mbg-scraper-network-20260419071440`
**Region:** `sgp1` (Singapore)

```
bucket/
├── analysis/                    # 77 CSV analysis outputs
│   ├── corpus_combined.csv       (212 MB — combined parent+reply data)
│   ├── reply_tree.csv            (87 MB — reply thread structure)
│   ├── replies_with_sentiment.csv (207 MB — reply sentiment)
│   ├── user_bot_scores.csv       (11.8 MB — bot detection)
│   ├── user_influence_scores.csv (9 MB — influence scoring)
│   ├── sentiment_over_time.csv   (temporal sentiment trends)
│   ├── topic_sentiment_matrix.csv (topic × sentiment crosstab)
│   ├── controversy_*.csv         (controversy scores)
│   ├── co_reply_*.csv            (co-reply network)
│   └── ... (67 additional files)
├── data/
│   └── mbg-final-parent-post - final-merged-x-parent-posts.csv (71 MB — raw)
├── models/
│   └── mbg-indobert-finetuned/   (fine-tuned IndoBERT model)
├── output/                       (legacy output files)
├── replies/
│   └── replies_all_dedup.jsonl   (289 MB — raw reply data)
├── runs/                         (4 timestamped pipeline runs)
│   ├── 20260430_112954/
│   ├── 20260430_122619/
│   ├── 20260501_040318/
│   └── 20260502_063532/
└── latest_run.json               (current run manifest)
```

## Git Development History

The project was developed over 30+ commits on the `main` branch, showing progressive feature development:

```
74ac6b7 Fix co-reply network: pre-compute layout to avoid timeout, fix ego color KeyError
f868f8b Add LDA+BERTopic topic modeling pipeline and reply-based SNA with community centrality
7dfded0 fix: replace broken Talk vs Amplify by Sentiment with ratio distribution
a980995 Update app.py navigation cards for new 7-page structure
3870a24 Consolidate dashboard from 16 pages to 7 research-driven pages
f86f48c Add co-reply network analysis with community detection and ego network explorer
995ddfc fix: lower bot threshold to 0.50, optimize SNA script
8ea9cc6 fix: remove topic_id from r11 influence analysis
fa3e90f Add bot detection, SNA, thread analysis, and influence analysis pipeline
25fec64 fix: update deploy workflow to include analysis scripts + fix ID type joins
2f36608 feat: add 5 reply analysis scripts + 2 new dashboard pages
a6d91a1 fix: use GPU (device=0) instead of CPU for R7 sentiment
6b6601c feat: add tqdm progress bars to R7 sentiment analysis
e8ebef6 feat: add R8-R10 reply pipeline stages and dashboard page
90d5778 fix: use batched nlp.pipe() for English preprocessing in R6
f106d33 fix: add tqdm progress bars and reduce spaCy truncation in R6
a0925ef feat: add Colab notebook for reply pipeline
62a9b17 Reply Data Pipeline (R1-R7) (#5)
05bec8e fix: preserve tweet ID precision by reading id column as string
... and 15+ earlier commits
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       GitHub Repository                          │
│  analysis/  dashboard/  scripts/  ingestion/  data/  docs/       │
└──────────────────┬──────────────────────────────────────────────┘
                   │ git push (main)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (CI/CD)                        │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │ Deploy       │    │ Run Pipeline     │    │ Validate      │  │
│  │ Dashboard    │    │ (manual trigger) │    │ Data Contract │  │
│  └──────┬───────┘    └────────┬─────────┘    └───────────────┘  │
│         │                     │                                  │
└─────────┼─────────────────────┼──────────────────────────────────┘
          │                     │
          ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DigitalOcean VPS (mbg-analysis)               │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │ Dashboard    │    │ Pipeline Runner  │    │ Data Store    │  │
│  │ (Streamlit)  │    │ (shell scripts)  │    │ /opt/mbg/data │  │
│  │ :8501        │    │ Python analysis  │    │               │  │
│  └──────┬───────┘    └────────┬─────────┘    └───────┬───────┘  │
│         │                     │                        │         │
└─────────┼─────────────────────┼────────────────────────┼─────────┘
          │                     │                        │
          ▼                     ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DigitalOcean Spaces (Object Storage)          │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐  │
│  │ Pipeline     │    │ Analysis CSVs    │    │ Raw Data &    │  │
│  │ Runs (runs/) │    │ (analysis/)      │    │ Model (model/)│  │
│  └──────────────┘    └──────────────────┘    └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Research Materials Inventory

| Category | Count | Location |
|----------|-------|----------|
| Analysis scripts | 20+ | `analysis/*.py` |
| Pipeline scripts | 15+ | `scripts/*.sh`, `scripts/*.py` |
| Dashboard pages | 7 | `dashboard/pages/` |
| Analysis CSVs | 77 | `data/analysis/` + Spaces |
| Pipeline runs | 4 | Spaces `runs/` |
| Git commits | 30+ | GitHub `main` branch |
| Raw data | ~167K tweets | `data/raw/` |
| Processed data | 107K tweets | `data/processed/` |
| Reply data | ~289 MB JSONL | Spaces `replies/` |
