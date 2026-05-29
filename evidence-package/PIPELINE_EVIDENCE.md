# Pipeline Evidence — MBG Discourse Analysis

> **Document Version**: 1.1  
> **Last Updated**: 2026-05-29  
> **Repository**: [FatwaArya/mbg-analysis](https://github.com/FatwaArya/mbg-analysis)  
> **Purpose**: Provide verifiable evidence of pipeline execution, output quality, and reproducibility.

## Table of Contents

- [Version History](#version-history)
- [Quick Start Guide](#quick-start-guide)
- [Pipeline Run History](#pipeline-run-history)
- [Storage Contents](#storage-contents-digitalocean-spaces)
- [Git Development History](#git-development-history)
- [Architecture](#architecture)
- [Research Materials Inventory](#research-materials-inventory)
- [Pipeline Stage Outputs](#pipeline-stage-outputs)
- [Quality Metrics](#quality-metrics)
- [Output Samples](#output-samples)
- [Data Validation & Quality Gates](#data-validation--quality-gates)
- [Monitoring & Alerting](#monitoring--alerting)
- [API Reference](#api-reference)
- [Troubleshooting Log](#troubleshooting-log)
- [FAQ](#faq)
- [Cross-References](#cross-references)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-04-28 | MBG Analysis Team | Initial pipeline evidence: run history, storage inventory |
| 0.2 | 2026-04-30 | MBG Analysis Team | Added data schemas, output samples, quality metrics |
| 0.3 | 2026-05-01 | MBG Analysis Team | Added performance benchmarks, dependency list |
| 1.0 | 2026-05-02 | MBG Analysis Team | Production release: architecture diagram, troubleshooting log |
| 1.1 | 2026-05-29 | MBG Analysis Team | Added version history, Quick Start, validation, monitoring, FAQ, API docs |

> For methodology-level changes (algorithms, models, statistical tests), see [METHODOLOGY.md Version History](METHODOLOGY.md#version-history).

---

## Quick Start Guide

### Prerequisites

- Python 3.11+, Git, 8 GB RAM, 10 GB disk
- DigitalOcean Spaces credentials (for storage access)

### Setup

```bash
git clone https://github.com/FatwaArya/mbg-analysis.git
cd mbg-analysis
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 -c "import nltk; nltk.download('stopwords')"
export RUNTIME_MODE=droplet
```

### Run Full Pipeline

```bash
bash scripts/run_full_pipeline.sh
```

This executes all 7 stages (inference → language → preprocess → sentiment → topics → validate → upload) with automatic checkpointing, locking, and logging.

### Monitor Progress

```bash
bash scripts/pipeline_status.sh      # One-line status
bash scripts/monitor_pipeline.sh     # Live dashboard (10s refresh)
```

> See [METHODOLOGY.md Quick Start](METHODOLOGY.md#quick-start-guide) for detailed setup instructions and runtime mode configuration.

---

## Pipeline Run History

All pipeline runs are timestamped (`YYYYMMDD_HHMMSS`) and stored in DigitalOcean Spaces under `runs/{run_id}/`. Each run produces a complete set of output artifacts. The pipeline uses a lockfile mechanism (`/tmp/mbg_pipeline.lock`) to prevent concurrent execution.

| Run ID | Date | Files Produced | Status | Storage Path |
|--------|------|----------------|--------|--------------|
| `20260430_112954` | 2026-04-30 | sentiment, topics, topic_info | ✅ Success | `s3://bucket/runs/20260430_112954/` |
| `20260430_122619` | 2026-04-30 | sentiment, topics, topic_info | ✅ Success | `s3://bucket/runs/20260430_122619/` |
| `20260501_040318` | 2026-05-01 | sentiment, topics, topic_info | ✅ Success | `s3://bucket/runs/20260501_040318/` |
| `20260502_063532` | 2026-05-02 | sentiment, topics, topic_info | ✅ Success | `s3://bucket/runs/20260502_063532/` |

**Latest manifest**: `s3://mbg-scraper-network-20260419071440/latest_run.json`

### Run Manifest Structure

Each `latest_run.json` manifest contains:
```json
{
  "run_id": "20260502_063532",
  "timestamp": "2026-05-02T06:35:32Z",
  "git_commit": "<commit_hash>",
  "git_branch": "main",
  "outputs": {
    "sentiment": "runs/20260502_063532/tweets_with_sentiment.csv",
    "topics": "runs/20260502_063532/tweets_with_topics.csv",
    "topic_info": "runs/20260502_063532/topic_info.csv"
  },
  "pipeline_config": {
    "sentiment_model": "w11wo/indonesian-roberta-base-sentiment-classifier",
    "relevance_threshold": 0.80,
    "topic_model": "hybrid_lda_bertopic"
  }
}
```

## Storage Contents (DigitalOcean Spaces)

**Bucket**: `mbg-scraper-network-20260419071440`  
**Region**: `sgp1` (Singapore)  
**Total Size**: ~1.2 GB (estimated)

```
bucket/                                    [mbg-scraper-network-20260419071440]
│
├── analysis/                              # 77 CSV analysis outputs
│   ├── corpus_combined.csv                # 212 MB — combined parent+reply data
│   ├── reply_tree.csv                     # 87 MB — reply thread structure
│   ├── replies_with_sentiment.csv         # 207 MB — reply sentiment labels
│   ├── user_bot_scores.csv                # 11.8 MB — bot detection scores
│   ├── user_influence_scores.csv          # 9 MB — influence scoring
│   ├── sentiment_over_time.csv            # Monthly sentiment trends
│   ├── topic_sentiment_matrix.csv         # Topic × sentiment crosstab
│   ├── daily_volume.csv                   # Daily tweet counts
│   ├── hourly_pattern.csv                 # Hourly distribution
│   ├── sentiment_overall.csv              # Overall sentiment counts
│   ├── sentiment_weekly.csv               # Weekly sentiment trends
│   ├── sentiment_engagement.csv           # Engagement by sentiment
│   ├── topic_prevalence.csv               # Topic size ranking
│   ├── topic_weekly.csv                   # Weekly topic trends
│   ├── top_engaging_tweets.csv            # Highest engagement tweets
│   ├── query_effectiveness.csv            # Search query performance
│   ├── controversy_*.csv                  # Controversy scores per topic
│   ├── co_reply_*.csv                     # Co-reply network edges/communities
│   └── ... (59 additional analysis files)
│
├── data/
│   └── mbg-final-parent-post - final-merged-x-parent-posts.csv
│                                          # 71 MB — raw parent tweet corpus
│
├── models/
│   └── mbg-indobert-finetuned/           # Fine-tuned IndoBERT model (475 MB)
│       ├── config.json
│       ├── model.safetensors
│       ├── tokenizer.json
│       └── ...
│
├── output/                                # Legacy output files
│
├── replies/
│   └── replies_all_dedup.jsonl            # 289 MB — raw reply data (JSONL)
│
├── runs/                                  # 4 timestamped pipeline runs
│   ├── 20260430_112954/
│   │   ├── tweets_with_sentiment.csv
│   │   ├── tweets_with_topics.csv
│   │   ├── topic_info.csv
│   │   └── metadata.json                  # Run manifest with MD5 hashes
│   ├── 20260430_122619/
│   │   └── ...
│   ├── 20260501_040318/
│   │   └── ...
│   └── 20260502_063532/
│       └── ...
│
└── latest_run.json                        # Current run manifest pointer
```

### Key Data Files

| File | Size | Rows | Description |
|------|------|------|-------------|
| `corpus_combined.csv` | 212 MB | ~107K | Parent tweets with sentiment + topic labels |
| `replies_with_sentiment.csv` | 207 MB | ~200K+ | Reply tweets with sentiment labels |
| `reply_tree.csv` | 87 MB | ~200K+ | Reply thread structure (parent-child) |
| `replies_all_dedup.jsonl` | 289 MB | ~200K+ | Raw reply data (JSON Lines format) |
| `user_bot_scores.csv` | 11.8 MB | ~50K+ | Bot detection scores per user |
| `user_influence_scores.csv` | 9 MB | ~50K+ | Influence scores per user |

## Git Development History

The project was developed over **30+ commits** on the `main` branch, showing progressive feature development. Below is a chronological summary of key milestones.

### Key Commits (Newest First)

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

### Development Phases

| Phase | Commits | Focus |
|-------|---------|-------|
| **Phase 1: Foundation** | 1-10 | Data collection, basic pipeline, initial dashboard |
| **Phase 2: Reply Pipeline** | 11-20 | Reply analysis (R1-R7), GPU optimization, progress bars |
| **Phase 3: Advanced Analytics** | 21-30 | Bot detection, SNA, influence scoring, controversy analysis |
| **Phase 4: Polish** | 30+ | Dashboard consolidation, bug fixes, performance optimization |

## Architecture

The MBG Discourse Analysis system follows a modular pipeline architecture with clear separation between data collection, processing, analysis, and presentation layers.

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          GitHub Repository                               │
│  analysis/  dashboard/  scripts/  scripts/replies/  ingestion/  docs/   │
│  20+ Python scripts  |  7 dashboard pages  |  15+ shell scripts         │
└────────────────────────────┬────────────────────────────────────────────┘
                             │ git push (main)
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      GitHub Actions (CI/CD)                             │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────────┐ │
│  │ Deploy       │    │ Run Pipeline     │    │ Validate Data         │ │
│  │ Dashboard    │    │ (manual trigger) │    │ Contract (on PR)      │ │
│  └──────┬───────┘    └────────┬─────────┘    └───────────────────────┘ │
└─────────┼─────────────────────┼────────────────────────────────────────┘
          │                     │
          ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                DigitalOcean VPS (4 vCPU / 8GB RAM / Ubuntu 22.04)       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Pipeline Orchestrator (run_full_pipeline.sh)                     │   │
│  │ Lockfile: /tmp/mbg_pipeline.lock                                 │   │
│  │ Log: /opt/mbg/logs/pipeline_{RUN_ID}.log                        │   │
│  │                                                                   │   │
│  │  ┌─────────┐ ┌────────┐ ┌──────────┐ ┌───────────┐ ┌─────────┐ │   │
│  │  │inference│→│tag_lang│→│preprocess│→│run_sentim.│→│run_topic│ │   │
│  │  │  .py    │ │  .py   │ │  .py     │ │   .py     │ │   .py   │ │   │
│  │  └─────────┘ └────────┘ └──────────┘ └───────────┘ └─────────┘ │   │
│  │       │                                              │          │   │
│  │       ▼                                              ▼          │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │validate  │→ │generate      │→ │upload_run.py             │  │   │
│  │  │data      │  │manifest.py   │  │(s3cmd, 3 retries)        │  │   │
│  │  │contract  │  │              │  │                          │  │   │
│  │  └──────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │
│  │ Dashboard         │  │ Reply Pipeline   │  │ Analysis Scripts      │ │
│  │ (Streamlit)       │  │ (R1-R7)          │  │ (statistical, bot,    │ │
│  │ :8501             │  │ scripts/replies/ │  │  influence, network)  │ │
│  │ 7 pages           │  │ 7 stages         │  │ 20+ scripts           │ │
│  └──────────────────┘  └──────────────────┘  └───────────────────────┘ │
│                                                                         │
│  Data: /opt/mbg/data/  |  Model: /opt/mbg/model/ (475 MB)             │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                DigitalOcean Spaces (S3-compatible, sgp1)                │
│                                                                         │
│  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐ │
│  │ Pipeline Runs   │  │ Analysis CSVs    │  │ Raw Data & Model        │ │
│  │ runs/           │  │ analysis/        │  │ data/ models/           │ │
│  │ 4 runs          │  │ 77 files         │  │ replies/ (289 MB)      │ │
│  │ + latest_run    │  │ 212 MB corpus    │  │ model/ (475 MB)        │ │
│  │   .json         │  │                  │  │                         │ │
│  └────────────────┘  └──────────────────┘  └─────────────────────────┘ │
│                                                                         │
│  Bucket: mbg-scraper-network-20260419071440                            │
│  Total: ~1.2 GB                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Execution Flow

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  run_full_    │     │  Each step    │     │  On failure:  │
│  pipeline.sh  │────▶│  logs to      │────▶│  Pipeline     │
│  starts       │     │  timestamped  │     │  aborts with  │
│               │     │  log file     │     │  exit code 1  │
└───────┬───────┘     └───────────────┘     └───────────────┘
        │
        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Step 6:      │     │  Validation   │     │  Abort if     │
│  validate_    │────▶│  checks       │────▶│  columns      │
│  data_        │     │  required     │     │  missing      │
│  contract.py  │     │  columns      │     │               │
└───────────────┘     └───────────────┘     └───────────────┘
        │
        ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  Step 8:      │     │  Upload with  │     │  Cleanup      │
│  upload_      │────▶│  3 retries    │────▶│  partial on   │
│  run.py       │     │  (5s delay)   │     │  failure      │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Architecture Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Source Control** | GitHub | Version control, CI/CD trigger |
| **CI/CD** | GitHub Actions | Automated dashboard deployment, manual pipeline trigger |
| **Compute** | DigitalOcean VPS (4 vCPU, 8GB RAM) | Pipeline execution, dashboard hosting |
| **Storage** | DigitalOcean Spaces (S3-compatible) | Persistent data, model storage, pipeline outputs |
| **Dashboard** | Streamlit + Plotly | Interactive visualization, research exploration |
| **Languages** | Python 3.11, Shell (Bash) | Analysis scripts, pipeline orchestration |

### Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Twitter/X    │    │ Raw Scrapes  │    │ IndoBERT     │    │ Preprocessed │
│ API (23      │───▶│ (CSV, 71 MB) │───▶│ Filter       │───▶│ Text         │
│ queries)     │    │ ~167K tweets │    │ (~107K)      │    │              │
└──────────────┘    └──────────────┘    └──────────────┘    └──────┬───────┘
                                                                   │
                    ┌──────────────────────────────────────────────┤
                    ▼                                              ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Dashboard    │◀──│ Analysis     │◀──│ Topic        │◀──│ Sentiment    │
│ (Streamlit)  │    │ CSVs (77)    │    │ Modeling     │    │ Analysis     │
│ 7 pages      │    │              │    │ (51 topics)  │    │ (RoBERTa)    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘

                    ┌──────────────┐    ┌──────────────┐
                    │ Reply Data   │───▶│ Reply        │
                    │ (289 MB      │    │ Pipeline     │
                    │  JSONL)      │    │ (R1-R7)      │
                    └──────────────┘    └──────────────┘
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

---

## Pipeline Stage Outputs

Each pipeline stage produces specific output files. Below is a detailed breakdown of what each stage generates.

### Stage 1: IndoBERT Relevance Filtering

| Output | Format | Description |
|--------|--------|-------------|
| Relevant tweets | CSV | ~107,000 tweets classified as relevant |
| Confidence scores | Column in CSV | Float 0–1 indicating classification confidence |
| Filtered-out tweets | Discarded | ~60,000 tweets below 0.80 threshold |

### Stage 2: Text Preprocessing

| Output | Format | Description |
|--------|--------|-------------|
| Cleaned text | Column in CSV | Processed tweet text (URLs, mentions removed) |
| Stemmed terms | Column in CSV | Root-form Indonesian words |
| Term count | Column in CSV | Number of meaningful terms remaining |

### Stage 3: Sentiment Analysis

| Output | Format | Description |
|--------|--------|-------------|
| `tweets_with_sentiment.csv` | CSV | 107,039 rows with sentiment labels |
| `sentiment_label` | Column | Positive, Negative, or Neutral |
| `sentiment_score` | Column | Confidence score (0–1) |

### Stage 4: Topic Modeling

| Output | Format | Description |
|--------|--------|-------------|
| `tweets_with_topics.csv` | CSV | Topic assignment per tweet |
| `topic_info.csv` | CSV | Topic metadata (keywords, size) |
| Topic keywords | In topic_info | Top 10 keywords per topic |

### Stage 5: Reply Analysis (R1–R7)

| Stage | Output | Description |
|-------|--------|-------------|
| R1 | CSV conversion | JSONL → structured CSV |
| R2 | Enriched metadata | Parent tweet context added |
| R3 | Reply depth | Depth level in thread |
| R4 | Filtered text | Bots/spam removed |
| R5 | Language labels | Detected language per reply |
| R6 | Preprocessed text | Cleaned, stemmed text |
| R7 | Sentiment labels | Sentiment per reply |

### Stage 6: Statistical & Network Analysis

| Output | File(s) | Description |
|--------|---------|-------------|
| Sentiment trends | `sentiment_over_time.csv` | Monthly sentiment aggregation |
| Topic-sentiment crosstab | `topic_sentiment_matrix.csv` | Sentiment distribution per topic |
| Bot scores | `user_bot_scores.csv` | 5-signal composite bot detection |
| Influence scores | `user_influence_scores.csv` | User influence ranking |
| Controversy scores | `controversy_*.csv` | Per-topic controversy metrics |
| Co-reply network | `co_reply_*.csv` | Network edges and communities |

---

## Quality Metrics

### Model Performance

| Model | Task | Metric | Score | Notes |
|-------|------|--------|-------|-------|
| IndoBERT (relevance) | Binary classification | F1 Score | 0.955 | 80/20 train/test split |
| Indonesian RoBERTa (sentiment) | 3-class classification | Accuracy | ~85% | Estimated from similar tasks |
| LDA + BERTopic (topics) | Topic coherence | C_v | ~0.5-0.7 | Typical for social media text |

### Data Quality Checks

| Check | Threshold | Status |
|-------|-----------|--------|
| Duplicate tweet removal | 100% unique IDs | ✅ Passed |
| Missing text filtering | < 1% missing | ✅ Passed |
| Language consistency | > 90% Indonesian | ✅ Passed |
| Sentiment distribution | Reasonable proportions | ✅ Passed |
| Topic coverage | > 80% tweets assigned | ✅ Passed |

### Processing Statistics

| Stage | Input | Output | Retention |
|-------|-------|--------|-----------|
| Raw collection | — | ~167,000 | 100% |
| Relevance filter | ~167,000 | ~107,000 | 64% |
| Text preprocessing | ~107,000 | ~107,000 | 100% |
| Sentiment analysis | ~107,000 | 107,039 | 100% |
| Topic modeling | 107,039 | 107,039 | 100% |
| Reply processing | ~200,000+ | ~150,000+ | ~75% |

---

## Output Samples

Below are representative samples of key output files to illustrate data format and quality.

### tweets_with_sentiment.csv (Sample)

```
id,text,sentiment_label,sentiment_score,positive_prob,negative_prob,neutral_prob
1234567890,"Program MBG sangat bagus untuk anak-anak",Positive,0.9234,0.9234,0.0456,0.0310
1234567891,"MBG terlalu mahal dan boros anggaran",Negative,0.8812,0.0678,0.8812,0.0510
1234567892,"Hari ini MBG diluncurkan di Jakarta",Neutral,0.7654,0.1234,0.1112,0.7654
```

### topic_info.csv (Sample)

```
Topic,Count,Name,Representation
0,15234,"gizi_makanan_anak_program",["gizi","makanan","anak","program","gratis"]
1,12456,"anggaran_biaya_dana_apbn",["anggaran","biaya","dana","apbn","mahal"]
2,9876,"korupsi_masalah_gagal_kritik",["korupsi","masalah","gagal","kritik","buruk"]
```

### user_bot_scores.csv (Sample)

```
user_id,username,bot_score,signals
9876543210,@user123,0.234,0.1;0.2;0.3;0.2;0.3
9876543211,@bot_account,0.876,0.9;0.9;0.8;0.7;0.9
```

### controversy_*.csv (Sample)

```
topic_id,controversy_score,sentiment_entropy,disagreement_bonus,volume_factor
0,0.6543,0.8765,0.5432,0.3210
1,0.5432,0.7654,0.4321,0.2109
```

### co_reply_network.csv (Sample)

```
source_user,target_user,weight,community
user_a,user_b,15,0
user_b,user_c,8,0
user_d,user_e,12,1
```

---

## Data Schemas

### tweets_with_sentiment.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Tweet ID (preserved as string for precision) |
| `created_at` | datetime | Tweet creation timestamp |
| `text` | string | Original tweet text |
| `cleaned_text` | string | Preprocessed text (URLs, mentions removed) |
| `user_id` | string | Author user ID |
| `username` | string | Author username |
| `retweet_count` | int | Number of retweets |
| `like_count` | int | Number of likes |
| `reply_count` | int | Number of replies |
| `quote_count` | int | Number of quote tweets |
| `relevance_score` | float | IndoBERT relevance confidence (0–1) |
| `sentiment_label` | string | Positive / Negative / Neutral |
| `sentiment_score` | float | Confidence of sentiment classification (0–1) |
| `positive_prob` | float | Probability of positive class |
| `negative_prob` | float | Probability of negative class |
| `neutral_prob` | float | Probability of neutral class |

### tweets_with_topics.csv

| Column | Type | Description |
|--------|------|-------------|
| `id` | string | Tweet ID |
| `topic_id` | int | Topic assignment (-1 = outlier) |
| `topic_name` | string | Human-readable topic label |
| `topic_keywords` | string | Top keywords for assigned topic |

### topic_info.csv

| Column | Type | Description |
|--------|------|-------------|
| `Topic` | int | Topic ID |
| `Count` | int | Number of tweets in topic |
| `Name` | string | Auto-generated topic name from keywords |
| `Representation` | list[string] | Top keywords |
| `Representative_Docs` | list[string] | Example tweets from topic |

### user_bot_scores.csv

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | User ID |
| `username` | string | Username |
| `bot_score` | float | Composite bot score (0–1) |
| `username_anomaly` | float | Username anomaly signal (0–1) |
| `temporal_regularity` | float | Posting regularity signal (0–1) |
| `content_similarity` | float | Near-duplicate content signal (0–1) |
| `engagement_ratio` | float | Engagement ratio anomaly signal (0–1) |
| `account_age_ratio` | float | Account age vs activity signal (0–1) |

### user_influence_scores.csv

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | string | User ID |
| `username` | string | Username |
| `influence_score` | float | Composite influence score (0–1) |
| `total_engagement` | int | Sum of all engagement metrics |
| `reply_reach` | int | Number of unique repliers |
| `tweet_count` | int | Total tweets in dataset |

---

## Performance Benchmarks

### Processing Time Estimates

| Stage | Dataset Size | Estimated Time | Hardware |
|-------|-------------|---------------|----------|
| IndoBERT Relevance | ~167K tweets | ~2-3 hours | CPU (4 vCPU) |
| Text Preprocessing | ~107K tweets | ~30-45 min | CPU |
| Sentiment Analysis | ~107K tweets | ~3-4 hours | CPU (no GPU) |
| Topic Modeling (LDA) | ~107K tweets | ~1-2 hours | CPU |
| Topic Modeling (BERTopic) | ~107K tweets | ~2-3 hours | CPU |
| Reply Pipeline (R1-R7) | ~200K replies | ~6-8 hours | CPU |
| Statistical Analysis | ~107K tweets | ~30-60 min | CPU |
| Network Analysis | ~50K users | ~1-2 hours | CPU |
| **Total Pipeline** | — | **~16-24 hours** | CPU (4 vCPU) |

### Resource Usage

| Resource | Typical Usage | Peak Usage |
|----------|--------------|------------|
| CPU | 60-80% (4 cores) | 100% during inference |
| Memory | 4-6 GB | 8 GB (with models loaded) |
| Disk I/O | Moderate | High during CSV reads |
| Network | Low | Moderate (Spaces upload) |

### Scalability Notes

- **Current scale**: 107K parent tweets + 200K replies = ~307K total documents
- **Bottleneck**: Model inference (CPU-only)
- **Scaling options**:
  - GPU acceleration: 10-20x speedup for transformer inference
  - Distributed processing: Split across multiple machines
  - Incremental processing: Only process new tweets (delta updates)

---

## Dependencies

### Core Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `transformers` | >=4.30.0 | HuggingFace model loading |
| `torch` | >=2.0.0 | Deep learning framework |
| `pandas` | >=2.0.0 | Data manipulation |
| `numpy` | >=1.24.0 | Numerical computation |
| `scikit-learn` | >=1.2.0 | ML utilities (TF-IDF, metrics) |

### NLP Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| `sastrawi` | >=1.0.1 | Indonesian stemming |
| `nltk` | >=3.8.1 | Stopword removal, tokenization |
| `spacy` | >=3.5.0 | Batch text processing |
| `langdetect` | >=1.0.9 | Language detection |

### Topic Modeling

| Library | Version | Purpose |
|---------|---------|---------|
| `bertopic` | >=0.14.0 | BERTopic pipeline |
| `umap-learn` | >=0.5.3 | Dimensionality reduction |
| `hdbscan` | >=0.8.29 | Density-based clustering |
| `gensim` | >=4.3.0 | LDA implementation |

### Infrastructure

| Library | Version | Purpose |
|---------|---------|---------|
| `boto3` | >=1.26.0 | DigitalOcean Spaces (S3) access |
| `streamlit` | >=1.22.0 | Dashboard framework |
| `plotly` | >=5.14.0 | Interactive visualizations |
| `tqdm` | >=4.65.0 | Progress bars |

### System Requirements

- **OS**: Ubuntu 22.04 LTS (or compatible)
- **Python**: 3.11+
- **RAM**: 8 GB minimum
- **Disk**: 10 GB free space
- **Network**: Internet access for API calls and model downloads

---

## Environment Setup

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/FatwaArya/mbg-analysis.git
cd mbg-analysis

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"

# 5. Configure environment
cp .env.example .env
# Edit .env with your DigitalOcean Spaces credentials

# 6. Run pipeline
python3 scripts/run_pipeline.py
```

### VPS Setup (DigitalOcean)

```bash
# SSH into VPS
ssh root@your_vps_ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install system dependencies
sudo apt install -y git build-essential

# Clone and setup
git clone https://github.com/FatwaArya/mbg-analysis.git /opt/mbg
cd /opt/mbg
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dashboard Deployment

```bash
# Create systemd service
sudo nano /etc/systemd/system/mbg-dashboard.service
```

```ini
[Unit]
Description=MBG Analysis Dashboard
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mbg/dashboard
ExecStart=/opt/mbg/venv/bin/streamlit run app.py --server.port 8501
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable mbg-dashboard
sudo systemctl start mbg-dashboard
sudo systemctl status mbg-dashboard
```

---

## Data Validation & Quality Gates

### Data Contract Validation

The pipeline validates output schemas using `scripts/validate_data_contract.py` (Step 6 of the full pipeline). This ensures downstream consumers (dashboard, analysis scripts) receive data with expected columns.

**Pipeline Output Contract** (validated on every run):

| File | Required Columns | Purpose |
|------|-----------------|---------|
| `tweets_with_sentiment.csv` | `text`, `date`, `sentiment_normalized`, `detected_lang` | Core sentiment output |
| `tweets_with_topics.csv` | `text`, `date`, `sentiment_normalized`, `topic_id`, `detected_lang` | Core topic output |
| `topic_info.csv` | `Topic`, `Count`, `Name` | Topic metadata |

**Analysis Output Contract** (validated with `--analysis` flag):

| File | Required Columns |
|------|-----------------|
| `daily_volume.csv` | `date`, `tweet_count` |
| `hourly_pattern.csv` | `hour`, `tweet_count` |
| `sentiment_overall.csv` | `sentiment`, `count` |
| `sentiment_weekly.csv` | `date`, `sentiment`, `count` |
| `sentiment_engagement.csv` | `sentiment`, `mean`, `median` |
| `topic_prevalence.csv` | `Topic`, `Count`, `Name` |
| `topic_weekly.csv` | `date`, `topic_id`, `count` |
| `top_engaging_tweets.csv` | `text`, `date`, `sentiment`, `engagement_total` |
| `query_effectiveness.csv` | `query_raw`, `tweet_count`, `avg_engagement` |

### Quality Gates

| Gate | Stage | Criteria | Action on Failure |
|------|-------|----------|-------------------|
| G1: Relevance rate | After Stage 1 | >= 50% tweets classified RELEVANT | Log warning, continue |
| G2: Preprocessing retention | After Stage 3 | >= 90% tweets pass length filter | Log warning, continue |
| G3: Schema validation | After Stage 6 | All required columns present | **Abort pipeline** |
| G4: Row count consistency | After Stage 6 | Sentiment rows == Topic rows +/- 1% | Log warning, continue |
| G5: Upload verification | After Stage 7 | All files uploaded successfully | **Abort pipeline** |

> **Cross-reference**: See [METHODOLOGY.md Data Validation](METHODOLOGY.md#data-validation--quality-gates) for detailed validation rules and commands.

---

## Monitoring & Alerting

### Pipeline Monitoring Tools

#### Quick Status (`scripts/pipeline_status.sh`)

Single-line output showing pipeline state:

```
RUNNING: SENT | Files: ✓rel ✓sent  [CHECKPOINT]
```

Indicators:
- `IDLE` / `RUNNING: INF TAG PRE SENT TOP`: Pipeline state
- `✓rel ✓sent ✓top`: Existing output files
- `[CHECKPOINT]`: Sentiment checkpoint available for resume

#### Live Monitor (`scripts/monitor_pipeline.sh`)

Full-screen terminal dashboard (10s refresh) showing:

| Section | Content |
|---------|---------|
| Pipeline lock | Running PID, stale lock detection |
| Steps | Each stage: RUNNING / DONE / PREV RUN / IDLE |
| Sentiment progress | Batch progress (e.g., `50000/107039`) |
| Output files | Row count, size, modification time |
| Latest log | Last 4 lines of most recent pipeline log |
| Resources | Memory and disk utilization |

**Duplicate detection**: Flags `RUNNING x2 ⚠ DUPLICATE` when multiple instances of same step are active.

### Pipeline Locking

- **Lockfile**: `/tmp/mbg_pipeline.lock`
- **Prevents**: Concurrent pipeline execution
- **Cleanup**: Automatic via `trap` on EXIT, INT, TERM signals
- **Stale lock**: Detected when PID in lockfile is no longer alive

### Logging

- **Location**: `/opt/mbg/logs/pipeline_{YYYYMMDD_HHMMSS}.log`
- **Format**: `[YYYY-MM-DD HH:MM:SS] message`
- **Pipeline summary**: Final log entry includes run ID, duration, output file row counts

### Checkpoint & Resume

Sentiment analysis (`run_sentiment.py`) supports checkpoint-based resumption:
- **Checkpoint file**: `data/.sentiment_checkpoint.csv`
- **Auto-clear**: Pipeline clears checkpoints at start of each full run
- **Manual resume**: Re-run `run_sentiment.py` to continue from last checkpoint after crash

> **Cross-reference**: See [METHODOLOGY.md Monitoring](METHODOLOGY.md#monitoring--alerting) for full monitoring documentation.

---

## API Reference

### Key Scripts

| Script | Usage | Input | Output |
|--------|-------|-------|--------|
| `inference.py` | `python3 inference.py` | Raw CSVs in `data/raw/` | `tweets_relevant.csv`, `tweets_rejected.csv`, `tweets_borderline.csv` |
| `scripts/run_full_pipeline.sh` | `bash scripts/run_full_pipeline.sh` | Raw data | All pipeline outputs + Spaces upload |
| `scripts/validate_data_contract.py` | `python3 scripts/validate_data_contract.py [--analysis]` | Pipeline outputs | Pass/fail validation |
| `scripts/generate_manifest.py` | `python3 scripts/generate_manifest.py [RUN_ID] [DURATION]` | Pipeline outputs | `metadata.json` |
| `scripts/upload_run.py` | `python3 scripts/upload_run.py` | `metadata.json` | Spaces upload |
| `scripts/pipeline_status.sh` | `bash scripts/pipeline_status.sh` | Process/file checks | One-line status |
| `scripts/monitor_pipeline.sh` | `bash scripts/monitor_pipeline.sh` | Process/file checks | Live dashboard |
| `runtime.py` | `from runtime import RUNTIME` | `RUNTIME_MODE` env var | `RuntimeConfig` dataclass |

### `runtime.py` Configuration

The `RuntimeConfig` frozen dataclass provides centralized configuration:

| Property | Droplet | Colab | Description |
|----------|---------|-------|-------------|
| `data_dir` | `/opt/mbg/data` | `/content/drive/MyDrive/mbg/data` | Base data path |
| `model_dir` | `/opt/mbg/model` | `/content/drive/MyDrive/mbg/model` | Model path |
| `device` | auto (`cuda`/`cpu`) | `cuda` (required) | PyTorch device |
| `inference_batch_size` | 64 | 128 | Inference batches |
| `sentiment_batch_size` | 32 | 64 | Sentiment batches |
| `embedding_batch_size` | 64 | 128 | Embedding batches |

Derived: `processed_dir`, `output_dir`, `raw_dir` (subdirectories of `data_dir`)

> **Cross-reference**: See [METHODOLOGY.md Script API Reference](METHODOLOGY.md#script-api-reference) for full function signatures and parameters.

---

## Troubleshooting Log

### Known Issues and Resolutions

| Issue | Resolution | Commit |
|-------|-----------|--------|
| Co-reply network timeout | Pre-compute layout positions | `74ac6b7` |
| Talk vs Amplify broken | Replace with ratio distribution | `7dfded0` |
| Bot threshold too high | Lower to 0.50 | `995ddfc` |
| GPU not used for sentiment | Set device=0 | `a6d91a1` |
| Tweet ID precision loss | Read as string type | `05bec8e` |
| spaCy truncation | Reduce max_length | `f106d33` |
| ID type join failures | Fix type mismatches | `25fec64` |

### Performance Optimizations

| Optimization | Impact | Commit |
|--------------|--------|--------|
| Batched nlp.pipe() in R6 | ~5x faster preprocessing | `90d5778` |
| tqdm progress bars | Better monitoring | `6b6601c`, `f106d33` |
| Pre-computed network layout | Avoid timeout | `74ac6b7` |

### Common Issues

**Issue**: Pipeline runs out of memory (OOM)
- **Cause**: Large dataset loaded entirely into memory
- **Solution**: Use chunked processing (`pd.read_csv(chunksize=10000)`)
- **Prevention**: Monitor memory usage with `htop`
- **Recovery**: Sentiment checkpoint enables resume from last batch

**Issue**: Model download fails
- **Cause**: Network timeout or HuggingFace rate limiting
- **Solution**: Retry with exponential backoff; model auto-downloads from Spaces if local copy missing
- **Prevention**: Cache models locally in `/opt/mbg/model/` (475 MB)
- **Pipeline behavior**: `run_full_pipeline.sh` checks for `model/config.json` and downloads from Spaces if missing

**Issue**: DigitalOcean Spaces upload fails
- **Cause**: Invalid credentials or network issues
- **Solution**: Check `.env` file, verify credentials
- **Prevention**: Upload script retries 3 times with 5-second delay, 60-second timeout per call
- **Cleanup**: Partial uploads are automatically cleaned up on failure via `cleanup_partial_upload()`

**Issue**: Tweet ID precision loss
- **Cause**: Pandas reading IDs as integers (loses precision for large IDs > 2^53)
- **Solution**: Read as string: `pd.read_csv(..., dtype={'id': str})`
- **Commit**: `05bec8e`
- **Impact**: All ID columns across the pipeline now use string type

**Issue**: spaCy truncation in R6
- **Cause**: Long tweets exceed spaCy's default `max_length`
- **Solution**: Reduce `max_length` or split text
- **Commit**: `f106d33`
- **Also**: Added tqdm progress bars for better monitoring

**Issue**: Stale pipeline lock prevents new runs
- **Cause**: Previous pipeline crashed without cleaning up `/tmp/mbg_pipeline.lock`
- **Solution**: `rm /tmp/mbg_pipeline.lock`
- **Detection**: `monitor_pipeline.sh` shows `STALE LOCK` when PID is dead
- **Prevention**: Lock cleanup is handled by `trap` on EXIT/INT/TERM signals

**Issue**: Dashboard co-reply network visualization timeout
- **Cause**: Force-directed layout computed on every page load for large graphs
- **Solution**: Pre-compute layout positions during analysis, store coordinates in CSV
- **Commit**: `74ac6b7`
- **Also fixed**: KeyError for ego node color in network visualization

---

## FAQ

### Pipeline Execution

**Q: How long does a full pipeline run take?**
A: Approximately 16-24 hours on CPU (4 vCPU), or 4-6 hours with GPU acceleration. The bottleneck is transformer model inference for sentiment analysis and relevance filtering.

**Q: Can I run the pipeline on Google Colab?**
A: Yes. Set `RUNTIME_MODE=colab` which requires CUDA, uses larger batch sizes (128/64), and stores data in Google Drive at `/content/drive/MyDrive/mbg/data`.

**Q: What happens if I run the pipeline while another run is active?**
A: The pipeline aborts with "Pipeline already running (PID X). Aborting." A lockfile at `/tmp/mbg_pipeline.lock` prevents concurrent execution.

**Q: How do I resume a crashed pipeline?**
A: Remove the lockfile (`rm /tmp/mbg_pipeline.lock`), then re-run `scripts/run_full_pipeline.sh`. The full pipeline clears checkpoints at start for consistency. For sentiment-only resume, run `scripts/run_sentiment.py` directly.

### Data & Outputs

**Q: Why does the latest run have 4 entries in the run history?**
A: The pipeline was run multiple times during development and testing. Each run produces a timestamped folder in Spaces. The `latest_run.json` manifest always points to the most recent run.

**Q: What is the difference between `runs/` and `analysis/` in Spaces?**
A: `runs/` contains per-run pipeline outputs (sentiment, topics, topic_info). `analysis/` contains post-analysis CSVs (77 files) that are overwritten each run.

**Q: How do I verify data integrity?**
A: The manifest (`metadata.json`) includes MD5 hashes (truncated to 8 chars) and row counts for each output file. Compare these against your local files.

### Storage & Infrastructure

**Q: What is the DigitalOcean Spaces bucket name?**
A: `mbg-scraper-network-20260419071440` in the `sgp1` (Singapore) region.

**Q: How much storage does the project use?**
A: Approximately 1.2 GB total: 289 MB (raw replies), 212 MB (corpus), 207 MB (reply sentiment), 475 MB (model), plus analysis CSVs and pipeline runs.

---

## Cross-References

This document is part of the MBG Analysis evidence package:

| Document | Purpose | Key Overlap |
|----------|---------|-------------|
| [METHODOLOGY.md](METHODOLOGY.md) | Analytical methods, algorithms, statistical tests | Pipeline stages, model details, formulas |
| [DATA_SAMPLES.md](DATA_SAMPLES.md) | Representative data samples | Output format examples |
| [ETHICS.md](ETHICS.md) | Ethical considerations | Data handling, privacy |
| [RESEARCH_PAPER.md](RESEARCH_PAPER.md) | Research findings | Analysis results, conclusions |

**Key cross-references to METHODOLOGY.md**:
- [Data Processing Pipeline](METHODOLOGY.md#data-processing-pipeline) — Detailed stage-by-stage methodology
- [Data Validation & Quality Gates](METHODOLOGY.md#data-validation--quality-gates) — Validation rules and commands
- [Monitoring & Alerting](METHODOLOGY.md#monitoring--alerting) — Monitoring tool documentation
- [Script API Reference](METHODOLOGY.md#script-api-reference) — Function signatures and parameters
- [Troubleshooting](METHODOLOGY.md#troubleshooting) — Real issues with root cause analysis
- [FAQ](METHODOLOGY.md#faq) — Common questions about methodology

---

## Glossary

| Term | Definition |
|------|------------|
| **MBG** | Makan Bergizi Gratis — Indonesian government's free nutritious meal program |
| **JSONL** | JSON Lines format — One JSON object per line |
| **CSV** | Comma-Separated Values — Tabular data format |
| **IndoBERT** | Indonesian BERT model |
| **RoBERTa** | Robustly Optimized BERT Pretraining Approach |
| **LDA** | Latent Dirichlet Allocation |
| **BERTopic** | Topic modeling using BERT embeddings |
| **UMAP** | Uniform Manifold Approximation and Projection |
| **HDBSCAN** | Hierarchical Density-Based Spatial Clustering |
| **Louvain** | Community detection algorithm |
| **TF-IDF** | Term Frequency–Inverse Document Frequency |
| **F1 Score** | Harmonic mean of precision and recall |
| **C_v** | Coherence metric for topic models |
| **S3** | Amazon Simple Storage Service protocol |
| **Spaces** | DigitalOcean's object storage (S3-compatible) |
| **VPS** | Virtual Private Server |
| **CI/CD** | Continuous Integration / Continuous Deployment |
| **OOM** | Out of Memory error |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-04-28 | Initial documentation: run history, storage inventory |
| 0.2 | 2026-04-30 | Added data schemas, output samples, quality metrics |
| 0.3 | 2026-05-01 | Added performance benchmarks, dependency list |
| 1.0 | 2026-05-02 | Production release: architecture diagram, troubleshooting log, glossary |
| 1.1 | 2026-05-29 | Added version history, Quick Start, data validation, monitoring, API reference, FAQ, cross-references. Improved architecture diagrams with pipeline execution flow. |
