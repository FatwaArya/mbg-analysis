# Methodology — MBG Discourse Analysis

## Data Collection

### Twitter/X Scraping
Tweets were collected using the Twitter/X API via 23 search queries covering:

- **General terms**: `"makan bergizi gratis"`, `"MBG"`, `"program MBG"`
- **Official entities**: `"Badan Gizi Nasional"`, `"SPPG"`, `"Satuan Pelayanan Pemenuhan Gizi"`
- **Critical terms**: `"keracunan MBG"`, `"korupsi MBG"`, `"gagal MBG"`
- **Regional terms**: `"MBG Papua"`, `"MBG NTT"`, `"MBG Jawa"`
- **Positive coverage**: `"manfaat MBG"`, `"gizi gratis"`
- **Policy angles**: `"anggaran MBG"`, `"APBN MBG"`, `"dana MBG"`

Both `top` and `latest` scrape tabs were used for comprehensive coverage. Date range: March 2017 – April 2026.

### Data Processing Pipeline

```
RAW SCRAPED TWEETS (~167,000)
        │
        ▼
[1] IndoBERT Relevance Filtering
    - Fine-tuned IndoBERT binary classifier
    - F1 score: 0.955
    - Threshold: >= 0.80 confidence
    - Output: ~107,000 RELEVANT tweets
        │
        ▼
[2] Text Preprocessing
    - Remove URLs, @mentions, hashtags
    - Sastrawi Indonesian stemmer
    - Stopword removal (Indonesian)
    - Filter: >= 3 terms remaining
        │
        ▼
[3] Sentiment Analysis
    - Model: w11wo/indonesian-roberta-base-sentiment-classifier
    - 3 classes: positive, negative, neutral
    - Batched inference for performance
    - Output: tweets_with_sentiment.csv (107,039 rows)
        │
        ▼
[4] Topic Modeling (Hybrid)
    ├── LDA: k=2..20, coherence score optimization
    └── Per-LDA-topic BERTopic (UMAP + HDBScan)
    - Output: 51 topics, tweets_with_topics.csv, topic_info.csv
        │
        ▼
[5] Reply Analysis Pipeline (R1–R7)
    ├── R1: JSONL → CSV conversion
    ├── R2: Enrich metadata (parent tweet lookup)
    ├── R3: Add reply depth
    ├── R4: Filter text (remove bots, spam)
    ├── R5: Language detection
    ├── R6: Preprocess text (stemming, cleaning)
    └── R7: Sentiment classification
        │
        ▼
[6] Statistical & Network Analysis
    ├── Sentiment distribution & trends
    ├── Topic prevalence & sentiment crosstab
    ├── Engagement analysis (talk vs amplify)
    ├── Spike detection (z-score)
    ├── Bot detection (5-signal composite)
    ├── User influence scoring
    ├── Controversy scoring
    └── Co-reply network (Louvain communities)
```

## Analytical Methods

### Sentiment Analysis
- **Model**: Indonesian RoBERTa (`w11wo/indonesian-roberta-base-sentiment-classifier`)
- **Classes**: Positive, Negative, Neutral
- **Confidence**: Score 0–1 for each prediction
- **Post-processing**: Normalization to three-class schema

### Topic Modeling
- **Stage 1 (LDA)**: Grid search k=2..20 with coherence score (CV) to find optimal topic count
- **Stage 2 (BERTopic)**: For each LDA topic, run UMAP dimensionality reduction + HDBScan clustering to discover sub-themes
- **Output**: 51 topics with keyword labels and tweet assignments
- **Outlier handling**: Tweets with topic_id = -1 are unassigned outliers

### Reply Analysis
- **Controversy Score Formula**: `0.50 × sentiment_entropy + 0.30 × disagreement_bonus + 0.20 × volume_factor`
- Sentiment entropy measures how split replies are across positive/negative/neutral
- Disagreement bonus captures parent–reply sentiment contradiction
- Volume factor scales with log reply count (capped at ~100)
- **Stance alignment**: Classifies reply stance as agree/disagree/mixed based on majority sentiment agreement with parent

### Bot Detection
5-signal composite scoring:
1. Username anomaly (numeric suffixes, random patterns)
2. Temporal posting regularity (coefficient of variation)
3. Near-duplicate content (TF-IDF cosine similarity)
4. Engagement ratio anomalies (likes/RTs vs followers)
5. Account age vs activity ratio

Threshold for flagging: composite bot score > 0.50

### User Influence Scoring
Composite score: `log1p(total_engagement) × log1p(reply_reach) × log1p(tweet_count)`

### Network Analysis
- **Co-reply network**: Undirected graph where edge weight = number of shared parent tweets between two users
- **Community detection**: Louvain algorithm for modularity optimization
- **Centrality**: Degree, betweenness, and eigenvector centrality per user

## Statistical Tests
- **Negativity trend**: Linear regression on monthly negative percentage, with R² and p-value
- **Engagement comparison**: Mann-Whitney U test (non-parametric) for negative vs positive engagement
- **Controversy thresholds**: Empirical distribution analysis for controversial vs non-controversial classification

## Infrastructure

### Compute
- **Primary VPS**: DigitalOcean, Singapore region, 4 vCPU / 8GB RAM
- **Purpose**: Pipeline execution, dashboard hosting
- **OS**: Ubuntu 22.04 LTS

### Storage
- **Primary**: DigitalOcean Spaces (S3-compatible), `sgp1` region
- **Bucket**: `mbg-scraper-network-20260419071440`
- **Contents**: Pipeline outputs (timestamped runs), analysis CSVs, model files
- **Local fallback**: `/opt/mbg/data/` on VPS

### Code & Deployment
- **Version control**: GitHub (`FatwaArya/mbg-analysis`)
- **CI/CD**: GitHub Actions (auto-deploy dashboard on push to `main`)
- **Dashboard**: Streamlit + Plotly, served via systemd service on port 8501

### Reproducibility
- Every pipeline run is timestamped (`YYYYMMDD_HHMMSS`)
- Outputs uploaded to `runs/{run_id}/` in Spaces
- `latest_run.json` manifest at bucket root tracks current run
- Git commit hash recorded in each manifest for code-data linkage
- Local files overwritten each run (no caching), ensuring fresh processing
