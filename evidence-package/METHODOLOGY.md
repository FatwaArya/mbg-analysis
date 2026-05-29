# Methodology — MBG Discourse Analysis

> **Document Version**: 1.1  
> **Last Updated**: 2026-05-29  
> **Repository**: [FatwaArya/mbg-analysis](https://github.com/FatwaArya/mbg-analysis)

---

## Table of Contents

- [Version History](#version-history)
- [Quick Start Guide](#quick-start-guide)
- [Data Collection](#data-collection)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Analytical Methods](#analytical-methods)
- [Statistical Tests](#statistical-tests)
- [Data Validation & Quality Gates](#data-validation--quality-gates)
- [Monitoring & Alerting](#monitoring--alerting)
- [Infrastructure](#infrastructure)
- [Reproducibility](#reproducibility)
- [Environment Setup](#environment-setup)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Cross-References](#cross-references)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-04-28 | MBG Analysis Team | Initial pipeline: data collection, IndoBERT inference, basic sentiment |
| 0.2 | 2026-04-30 | MBG Analysis Team | Added topic modeling (LDA + BERTopic), statistical analysis |
| 0.3 | 2026-05-01 | MBG Analysis Team | Reply analysis pipeline (R1-R7), GPU optimization |
| | | | Fixed: GPU device=0 for R7 (`a6d91a1`), spaCy batch processing (`90d5778`) |
| 0.4 | 2026-05-02 | MBG Analysis Team | Bot detection, influence scoring, co-reply network |
| | | | Fixed: bot threshold lowered to 0.50 (`995ddfc`), network layout pre-computation (`74ac6b7`) |
| 1.0 | 2026-05-02 | MBG Analysis Team | Production release with all 6 pipeline stages |
| 1.1 | 2026-05-29 | MBG Analysis Team | Added version history, Quick Start, data validation, monitoring, FAQ |

---

## Quick Start Guide

### Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Git installed
- [ ] 8 GB+ RAM available
- [ ] 10 GB+ free disk space
- [ ] DigitalOcean Spaces credentials (for storage)

### 5-Minute Setup

```bash
# 1. Clone the repository
git clone https://github.com/FatwaArya/mbg-analysis.git
cd mbg-analysis

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Download required NLTK data
python3 -c "import nltk; nltk.download('stopwords')"

# 5. Configure runtime mode
export RUNTIME_MODE=droplet   # or 'colab' for Google Colab with GPU

# 6. Run the full pipeline
bash scripts/run_full_pipeline.sh
```

### Runtime Modes

| Mode | Device | Inference Batch | Sentiment Batch | Data Path |
|------|--------|-----------------|-----------------|-----------|
| `droplet` (VPS) | CPU or auto-detect CUDA | 64 | 32 | `/opt/mbg/data` |
| `colab` (Google Colab) | CUDA required | 128 | 64 | `/content/drive/MyDrive/mbg/data` |

> **Note**: The runtime mode is configured via the `RUNTIME_MODE` environment variable, which controls batch sizes, device selection, and data paths. See `runtime.py` for full configuration details.

### Running Individual Stages

| Stage | Command | Description |
|-------|---------|-------------|
| 1. Inference | `python3 inference.py` | IndoBERT relevance filtering |
| 2. Language tag | `python3 scripts/tag_language.py` | Detect language per tweet |
| 3. Preprocess | `python3 scripts/preprocess_text.py` | Clean and stem text |
| 4. Sentiment | `python3 scripts/run_sentiment.py` | RoBERTa sentiment classification |
| 5. Topics | `python3 scripts/run_topics.py` | LDA + BERTopic topic modeling |
| 6. Validate | `python3 scripts/validate_data_contract.py` | Check output schemas |
| 7. Upload | `python3 scripts/upload_run.py` | Upload to DigitalOcean Spaces |

### Monitoring a Running Pipeline

```bash
# Quick one-line status
bash scripts/pipeline_status.sh

# Live dashboard with step-by-step progress (refreshes every 10s)
bash scripts/monitor_pipeline.sh
```

> See [Monitoring & Alerting](#monitoring--alerting) for full details.

---

## Data Collection

### Twitter/X Scraping

#### Search Strategy

Tweets were collected using the Twitter/X API via **23 search queries** covering multiple facets of the MBG discourse:

| Category | Example Queries | Purpose |
|----------|----------------|---------|
| **General terms** | `"makan bergizi gratis"`, `"MBG"`, `"program MBG"` | Broad coverage |
| **Official entities** | `"Badan Gizi Nasional"`, `"SPPG"`, `"Satuan Pelayanan Pemenuhan Gizi"` | Institutional references |
| **Critical terms** | `"keracunan MBG"`, `"korupsi MBG"`, `"gagal MBG"` | Negative/critical discourse |
| **Regional terms** | `"MBG Papua"`, `"MBG NTT"`, `"MBG Jawa"` | Geographic variation |
| **Positive coverage** | `"manfaat MBG"`, `"gizi gratis"` | Positive discourse |
| **Policy angles** | `"anggaran MBG"`, `"APBN MBG"`, `"dana MBG"` | Budget/policy discourse |

#### Scraping Configuration
- **Scrape tabs**: Both `top` (ranked) and `latest` (chronological) for comprehensive coverage
- **Date range**: March 2017 – April 2026 (~9 years of discourse)
- **Deduplication**: Tweets matched across queries are deduplicated by tweet ID
- **Data format**: CSV with columns for `id`, `created_at`, `text`, `user`, `retweet_count`, `like_count`, `reply_count`, `quote_count`
- **Total collected**: ~167,000 unique tweets before filtering

### Data Processing Pipeline

#### Pipeline Flow Diagram (Detailed)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  RAW SCRAPED TWEETS (~167,000)                                          │
│  Source: data/raw/*.csv (71 MB parent posts)                            │
│  Dedup: By tweet ID across 23 search queries                           │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: IndoBERT Relevance Filtering                    inference.py  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Model: mbg-indobert-finetuned (475 MB)                            │ │
│  │ Base: indobenchmark/indobert-base-p1 (124M params)                │ │
│  │ Threshold: >= 0.80 confidence                                      │ │
│  │ Batch size: 64 (droplet) / 128 (colab)                            │ │
│  │ Max token length: 128                                              │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  Output: tweets_relevant.csv (~107K) | tweets_rejected.csv | borderline│
│  Validation: F1 = 0.955 (80/20 stratified split, 5-fold CV)           │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: Language Tagging                            tag_language.py   │
│  Tool: langdetect library                                                │
│  Output: Adds `detected_lang` column (id, en, other)                    │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: Text Preprocessing                          preprocess_text.py│
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Steps:                                                             │ │
│  │  1. URL removal (regex: https?://\S+)                              │ │
│  │  2. @mention removal (regex: @\w+)                                 │ │
│  │  3. Hashtag processing (#MBG → MBG)                                │ │
│  │  4. Emoji/special char removal                                     │ │
│  │  5. Sastrawi Indonesian stemming                                   │ │
│  │  6. NLTK Indonesian stopword removal                               │ │
│  │  7. Length filter: >= 3 terms remaining                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  Output: tweets_preprocessed.csv                                        │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: Sentiment Analysis                          run_sentiment.py  │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ Model: w11wo/indonesian-roberta-base-sentiment-classifier          │ │
│  │ Classes: positive, negative, neutral                               │ │
│  │ Batch size: 32 (droplet) / 64 (colab)                             │ │
│  │ Checkpoint: data/.sentiment_checkpoint.csv (resume support)        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  Output: tweets_with_sentiment.csv (107,039 rows)                      │
│  Columns: sentiment_normalized, sentiment_score, pos/neg/neutral_prob  │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: Topic Modeling (Hybrid)                     run_topics.py     │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ 5a. LDA (Gensim)        │  │ 5b. BERTopic (per LDA group)        │ │
│  │ - k range: 2 to 20      │  │ - UMAP: n_components=5              │ │
│  │ - Coherence: C_v (NPMI) │  │ - HDBSCAN: min_cluster_size=10      │ │
│  │ - Select optimal k      │  │ - c-TF-IDF topic representation     │ │
│  └─────────────────────────┘  └──────────────────────────────────────┘ │
│  Output: tweets_with_topics.csv, topic_info.csv (51 topics)            │
│  Outliers: topic_id = -1 (typically 5-15% of tweets)                   │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ▼                         ▼
┌──────────────────────────┐  ┌───────────────────────────────────────────┐
│ STAGE 6a: Reply Pipeline │  │ STAGE 6b: Statistical & Network Analysis  │
│ (R1-R7)                  │  │                                           │
│ R1: JSONL→CSV            │  │ • Sentiment trends (linear regression)    │
│ R2: Metadata enrichment  │  │ • Topic×sentiment crosstab               │
│ R3: Reply depth          │  │ • Engagement analysis (Mann-Whitney U)    │
│ R4: Bot/spam filter      │  │ • Spike detection (z-score > 2.0)        │
│ R5: Language detection   │  │ • Bot detection (5-signal composite)      │
│ R6: Text preprocessing   │  │ • User influence scoring                  │
│ R7: Sentiment (GPU)      │  │ • Controversy scoring                     │
│                           │  │ • Co-reply network (Louvain communities)  │
│ Input: ~200K+ replies    │  │                                           │
│ Output: ~150K+ processed │  │ Output: 77 analysis CSVs                  │
└──────────────────────────┘  └───────────────────────────────────────────┘
                │                         │
                └────────────┬────────────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  STAGE 7: Validation & Upload                                            │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │ validate_data_contract.py: Schema validation (required columns)    │ │
│  │ generate_manifest.py: Metadata JSON with MD5 hashes + stats        │ │
│  │ upload_run.py: Upload to DigitalOcean Spaces with retry (3x)       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│  Output: runs/{YYYYMMDD_HHMMSS}/ + latest_run.json manifest            │
└──────────────────────────────────────────────────────────────────────────┘
```

#### Stage 1: IndoBERT Relevance Filtering

**Purpose**: Filter out tweets that mention MBG-related terms but are not actually about the MBG program (e.g., tweets where "MBG" is an acronym for something else).

**Model Architecture**:
- Base model: `indobenchmark/indobert-base-p1` (Indonesian BERT, 124M parameters)
- Fine-tuned for binary classification: relevant (1) vs. not relevant (0)
- Training data: Manually labeled sample of ~2,000 tweets
- Validation: 80/20 train/test split with stratification

**Inference Configuration**:
- Batch size: 32 tweets per batch
- Device: CUDA GPU (device=0) when available, fallback to CPU
- Confidence threshold: `>= 0.80` for relevance
- Output: Binary label + confidence score per tweet

**Quality Metrics**:
- Precision: High (minimizes false positives)
- Recall: High (minimizes missed relevant tweets)
- F1 Score: 0.955 (harmonic mean of precision and recall)

**Validation Approach**:
- 80/20 stratified train/test split
- Manual annotation of 2,000+ tweets for ground truth
- Cross-validation: 5-fold stratified CV for robustness
- Confusion matrix analysis for error patterns

**Filtering Impact**: ~167,000 raw tweets → ~107,000 relevant tweets (36% filtered out)

#### Stage 2: Text Preprocessing

**Purpose**: Clean and normalize tweet text for downstream NLP tasks.

**Processing Steps**:
1. **URL Removal**: Strip `http://` and `https://` links using regex pattern `https?://\S+`
2. **Mention Removal**: Strip `@username` mentions using regex pattern `@\w+`
3. **Hashtag Processing**: Remove `#` symbol but preserve hashtag text (e.g., `#MBG` → `MBG`)
4. **Special Character Handling**: Remove emojis, special Unicode characters, excess whitespace
5. **Indonesian Stemming**: Apply Sastrawi stemmer to reduce words to root form
   - Example: `makanannya` → `makan`, `bergizi` → `gizi`
6. **Stopword Removal**: Remove Indonesian stopwords using NLTK's Indonesian stopword list
7. **Length Filter**: Keep only tweets with `>= 3` remaining terms after preprocessing

**Tools Used**:
- `sastrawi`: Indonesian stemming library
- `nltk`: Stopword removal
- `re` (Python regex): Pattern matching for URLs, mentions

**Edge Cases Handled**:
- Empty tweets after preprocessing (discarded)
- Non-Indonesian text (retained for sentiment analysis, language detection in reply pipeline)
- Retweets (`RT @user:` prefix) preserved for context
- Very long tweets (>280 chars) truncated to max length
- Unicode normalization for consistent character handling

#### Stage 3: Sentiment Analysis

**Purpose**: Classify each tweet's emotional tone as positive, negative, or neutral.

**Model Details**:
- **Model**: `w11wo/indonesian-roberta-base-sentiment-classifier`
- **Architecture**: RoBERTa-base for Indonesian language
- **Training**: Fine-tuned on Indonesian sentiment dataset
- **Output**: 3-class probability distribution (positive, negative, neutral)

**Inference Configuration**:
- **Batch size**: 32 tweets per batch (GPU) / 16 (CPU)
- **Device**: CUDA GPU (device=0) for performance
- **Progress tracking**: tqdm progress bars for long-running inference
- **Output format**: Class label + confidence score (0–1)

**Post-processing**:
- Assign final class as argmax of probability distribution
- Normalize confidence scores to sum to 1.0
- Round confidence to 4 decimal places

**Performance Notes**:
- GPU inference: ~500 tweets/minute
- CPU inference: ~50 tweets/minute (10x slower)
- Total processing time: ~3.5 hours for 107K tweets on GPU

**Output**: `tweets_with_sentiment.csv` with columns: `id`, `text`, `sentiment_label`, `sentiment_score`, `positive_prob`, `negative_prob`, `neutral_prob`

#### Stage 4: Topic Modeling (Hybrid LDA + BERTopic)

**Purpose**: Discover latent themes in the MBG discourse and assign tweets to topics.

**Hybrid Approach**: Combines traditional LDA (global topics) with modern BERTopic (sub-themes).

**Stage 4a: LDA (Latent Dirichlet Allocation)**
- **Algorithm**: Gibbs sampling with variational inference
- **Topic range**: k = 2 to 20 topics
- **Coherence metric**: C_v (normalized pointwise mutual information)
- **Optimization**: Select k that maximizes coherence score
- **Output**: Topic-word distributions, document-topic assignments

**Stage 4b: BERTopic (Per-LDA-topic)**
- **Dimensionality reduction**: UMAP (Uniform Manifold Approximation and Projection)
  - `n_components`: 5
  - `n_neighbors`: 15
  - `min_dist`: 0.0
- **Clustering**: HDBSCAN (Hierarchical Density-Based Spatial Clustering)
  - `min_cluster_size`: 10
  - `min_samples`: 5
- **Topic representation**: c-TF-IDF (class-based TF-IDF)

**Output Files**:
- `tweets_with_topics.csv`: Tweet ID → topic assignment (107,039 rows)
- `topic_info.csv`: Topic metadata (keywords, size, representative tweets)
- 51 topics identified across all LDA groups

**Outlier Handling**:
- Tweets assigned `topic_id = -1` are outliers (not assigned to any topic)
- Outliers are tweets that don't fit well into any discovered cluster
- Typical outlier rate: 5-15% of tweets

#### Stage 5: Reply Analysis Pipeline (R1–R7)

**Purpose**: Process reply tweets to understand conversational dynamics, sentiment propagation, and controversy.

**Pipeline Stages**:

**R1: JSONL → CSV Conversion**
- Input: `replies_all_dedup.jsonl` (289 MB raw JSON Lines)
- Process: Parse JSONL, flatten nested structures, convert to tabular format
- Output: `replies_raw.csv`

**R2: Enrich Metadata**
- Process: Join reply tweets with parent tweet data
- Lookup: Retrieve parent tweet text, user, timestamp
- Output: `replies_enriched.csv` with parent context columns

**R3: Add Reply Depth**
- Process: Calculate reply depth in thread hierarchy
- Depth 0: Direct reply to parent tweet
- Depth 1: Reply to a reply
- Depth 2+: Nested conversation
- Output: `reply_depth` column added

**R4: Filter Text**
- Process: Remove bot-generated content, spam, duplicate replies
- Filters:
  - Bot score threshold: > 0.50 (from bot detection)
  - Near-duplicate detection: TF-IDF cosine similarity > 0.90
  - Minimum text length: > 10 characters
- Output: `replies_filtered.csv`

**R5: Language Detection**
- Process: Identify language of each reply
- Tool: `langdetect` library
- Languages: Indonesian (id), English (en), Other
- Output: `language` column added

**R6: Preprocess Text**
- Process: Apply same preprocessing as Stage 2 (URL removal, stemming, stopword removal)
- Tools: Sastrawi stemmer, NLTK stopwords
- Batch processing: Use spaCy `nlp.pipe()` for efficiency
- Progress tracking: tqdm progress bars
- Output: `cleaned_text` column added

**R7: Sentiment Classification**
- Model: Same as Stage 3 (`w11wo/indonesian-roberta-base-sentiment-classifier`)
- Device: GPU (device=0) for performance
- Batch size: 32 per batch
- Output: `replies_with_sentiment.csv` with sentiment labels

**Total Reply Processing**:
- Input: ~200,000+ raw replies
- Output: ~150,000+ processed replies (after filtering)
- Processing time: ~4-6 hours on GPU

#### Stage 6: Statistical & Network Analysis

**Purpose**: Perform statistical tests, network analysis, and generate insights from processed data.

**Sub-analyses**:

**Sentiment Distribution & Trends**
- Monthly aggregation of sentiment proportions
- Trend analysis: Linear regression on negative percentage over time
- Metrics: R² (fit), p-value (significance)

**Topic Prevalence & Sentiment Crosstab**
- Matrix: Topics × Sentiment (positive, negative, neutral)
- Normalization: Row percentages (per-topic sentiment distribution)
- Visualization: Heatmap for dashboard

**Engagement Analysis (Talk vs Amplify)**
- Compare engagement metrics (likes, retweets) across sentiment classes
- Test: Mann-Whitney U (non-parametric) for significance
- Metric: Engagement ratio = (likes + retweets) / tweet_count

**Spike Detection (Z-score)**
- Detect unusual activity spikes in tweet volume
- Method: Z-score on daily tweet counts
- Threshold: |z| > 2.0 for spike detection

**Bot Detection (5-signal Composite)**
- Signals: Username anomaly, temporal regularity, content similarity, engagement ratio, account age
- Composite score: Weighted average of normalized signals
- Threshold: > 0.50 for flagging as potential bot
- Output: `user_bot_scores.csv`

**User Influence Scoring**
- Formula: `log1p(total_engagement) × log1p(reply_reach) × log1p(tweet_count)`
- Normalization: Min-max scaling to 0–1 range
- Output: `user_influence_scores.csv`

**Controversy Scoring**
- Formula: `0.50 × sentiment_entropy + 0.30 × disagreement_bonus + 0.20 × volume_factor`
- Per-topic controversy ranking
- Output: `controversy_*.csv`

**Co-reply Network Analysis**
- Graph construction: Undirected, weighted by shared parent tweets
- Community detection: Louvain algorithm (modularity optimization)
- Centrality metrics: Degree, betweenness, eigenvector
- Output: `co_reply_*.csv` with edges, communities, centrality scores

## Analytical Methods

### Sentiment Analysis

**Model**: Indonesian RoBERTa (`w11wo/indonesian-roberta-base-sentiment-classifier`)

**Architecture**:
- Base: RoBERTa (Robustly Optimized BERT Pretraining Approach)
- Language: Indonesian
- Parameters: ~125M
- Fine-tuned on: Indonesian sentiment dataset

**Classification Schema**:
- **Positive**: Optimistic, supportive, praising tone
- **Negative**: Critical, complaining, disapproving tone
- **Neutral**: Factual, informational, no clear sentiment

**Confidence Score**: Float 0–1 indicating model certainty
- High confidence (>0.8): Strong classification
- Medium confidence (0.5–0.8): Moderate certainty
- Low confidence (<0.5): Ambiguous, may need manual review

**Post-processing**:
- Normalize probabilities to sum to 1.0
- Assign class as argmax of probability distribution
- Round scores to 4 decimal places

### Topic Modeling

**Hybrid Approach**: Combines traditional LDA with modern BERTopic for comprehensive topic discovery.

**Stage 1: LDA (Latent Dirichlet Allocation)**
- **Algorithm**: Generative probabilistic model
- **Objective**: Find k topics that maximize document-topic and topic-word coherence
- **Grid search**: k = 2 to 20 topics
- **Coherence metric**: C_v (normalized pointwise mutual information)
- **Optimization**: Select k that maximizes C_v score
- **Output**: Topic-word distributions, document-topic assignments

**Stage 2: BERTopic (Per-LDA-topic)**
- **Purpose**: Discover sub-themes within each LDA topic
- **Dimensionality reduction**: UMAP
  - `n_components`: 5 (reduced from 768-dim embeddings)
  - `n_neighbors`: 15 (local connectivity)
  - `min_dist`: 0.0 (tight clusters)
- **Clustering**: HDBSCAN
  - `min_cluster_size`: 10 (minimum tweets per cluster)
  - `min_samples`: 5 (core point density)
- **Topic representation**: c-TF-IDF (class-based TF-IDF)
  - Extracts distinctive keywords per cluster
  - Balances term frequency with document frequency

**Output**:
- 51 topics identified across all LDA groups
- `tweets_with_topics.csv`: Topic assignment per tweet (107,039 rows)
- `topic_info.csv`: Topic metadata (keywords, size, representative tweets)

**Outlier Handling**:
- Tweets with `topic_id = -1` are unassigned outliers
- Outliers don't fit well into any discovered cluster
- Typical outlier rate: 5-15% of tweets

### Reply Analysis

**Purpose**: Analyze conversational dynamics, sentiment propagation, and controversy in reply threads.

**Controversy Score Formula**:
```
controversy_score = 0.50 × sentiment_entropy + 0.30 × disagreement_bonus + 0.20 × volume_factor
```

**Component Breakdown**:

1. **Sentiment Entropy** (weight: 0.50)
   - Measures how split replies are across positive/negative/neutral
   - Formula: `H = -Σ(p_i × log2(p_i))` where p_i is proportion of sentiment class i
   - Range: 0 (unanimous) to 1.585 (perfectly split across 3 classes)
   - Normalization: Divide by max entropy (log2(3)) to get 0–1 range

2. **Disagreement Bonus** (weight: 0.30)
   - Captures parent–reply sentiment contradiction
   - Calculation: Proportion of replies with different sentiment than parent
   - Range: 0 (all agree) to 1 (all disagree)

3. **Volume Factor** (weight: 0.20)
   - Scales with log reply count (capped at ~100)
   - Formula: `min(log10(reply_count), 2.0) / 2.0`
   - Range: 0 (no replies) to 1 (100+ replies)
   - Logarithmic scaling prevents high-volume threads from dominating

**Stance Alignment**:
- Classifies reply stance as agree/disagree/mixed based on majority sentiment agreement with parent
- **Agree**: Reply sentiment matches parent sentiment
- **Disagree**: Reply sentiment differs from parent sentiment
- **Mixed**: Neutral replies or close sentiment distribution

### Bot Detection

**Purpose**: Identify automated or suspicious accounts that may distort discourse analysis.

**5-Signal Composite Scoring**:

1. **Username Anomaly** (weight: 0.20)
   - Detects patterns: numeric suffixes (`user123456`), random strings (`xk9m2p`), default templates
   - Regex patterns: `\d{5,}$`, `[a-z]{2}\d{2}[a-z]{2}\d{2}`
   - Score: 0 (normal) to 1 (highly suspicious)

2. **Temporal Posting Regularity** (weight: 0.20)
   - Measures coefficient of variation (CV) of inter-posting intervals
   - Low CV = regular posting (bot-like)
   - High CV = irregular posting (human-like)
   - Score: 0 (irregular) to 1 (highly regular)

3. **Near-Duplicate Content** (weight: 0.20)
   - TF-IDF vectorization of tweet text
   - Cosine similarity between user's tweets
   - Threshold: > 0.90 similarity = near-duplicate
   - Score: 0 (unique content) to 1 (mostly duplicates)

4. **Engagement Ratio Anomalies** (weight: 0.20)
   - Ratio: (likes + retweets) / follower_count
   - Anomaly: Very low engagement relative to follower count
   - Score: 0 (normal ratio) to 1 (suspicious ratio)

5. **Account Age vs Activity Ratio** (weight: 0.20)
   - Ratio: tweet_count / account_age_days
   - Anomaly: Very high posting rate (>100 tweets/day)
   - Score: 0 (normal) to 1 (suspicious)

**Composite Score Calculation**:
```
bot_score = Σ(signal_i × weight_i)
```

**Threshold for Flagging**: composite bot score > 0.50

**Output**: `user_bot_scores.csv` with per-user composite scores and individual signal scores

### User Influence Scoring

**Purpose**: Rank users by their influence in the MBG discourse.

**Composite Score Formula**:
```
influence_score = log1p(total_engagement) × log1p(reply_reach) × log1p(tweet_count)
```

**Component Breakdown**:

1. **total_engagement**: Sum of likes + retweets + replies + quotes across all user's tweets
   - `log1p()` dampens extreme values (prevents celebrity accounts from dominating)
   - Captures: Viral reach of user's content

2. **reply_reach**: Number of unique users who replied to this user's tweets
   - `log1p()` dampens extreme values
   - Captures: Conversational influence

3. **tweet_count**: Total number of tweets by user in dataset
   - `log1p()` dampens extreme values
   - Captures: Activity level in discourse

**Normalization**:
- Min-max scaling to 0–1 range
- Score 0 = least influential, 1 = most influential

**Output**: `user_influence_scores.csv` with columns: `user_id`, `username`, `influence_score`, `total_engagement`, `reply_reach`, `tweet_count`

### Network Analysis

**Co-reply Network Construction**:
- **Graph type**: Undirected, weighted
- **Node**: Twitter user
- **Edge**: Shared parent tweets between two users
- **Edge weight**: Number of shared parent tweets (users who replied to same tweets)
- **Minimum edge weight**: 2 (filter out weak connections)

**Community Detection**:
- **Algorithm**: Louvain method (modularity optimization)
- **Resolution parameter**: 1.0 (default)
- **Output**: Community ID per user
- **Interpretation**: Users in same community tend to engage with same tweets/topics

**Centrality Metrics**:
1. **Degree centrality**: Number of connections (normalized by max possible)
2. **Betweenness centrality**: How often user lies on shortest path between other users
3. **Eigenvector centrality**: Influence based on connections to other influential users

**Output**: `co_reply_*.csv` with columns: `user_id`, `community`, `degree_centrality`, `betweenness_centrality`, `eigenvector_centrality`

## Statistical Tests

### Negativity Trend Analysis

**Purpose**: Test whether negative sentiment in MBG discourse increases over time.

**Method**: Linear regression on monthly negative percentage
- **Independent variable**: Month (ordinal, 1 to N)
- **Dependent variable**: Percentage of negative tweets in that month
- **Model**: `y = β₀ + β₁x + ε`

**Metrics**:
- **R²** (coefficient of determination): Proportion of variance explained by time
- **p-value**: Statistical significance of the trend
- **β₁** (slope): Rate of change per month

**Interpretation**:
- β₁ > 0: Increasing negativity over time
- β₁ < 0: Decreasing negativity over time
- p < 0.05: Statistically significant trend

### Engagement Comparison

**Purpose**: Test whether negative tweets receive more engagement than positive tweets.

**Method**: Mann-Whitney U test (non-parametric)
- **Group A**: Engagement metrics for negative tweets
- **Group B**: Engagement metrics for positive tweets
- **Null hypothesis**: No difference in engagement between groups
- **Alternative hypothesis**: Negative tweets have different engagement
- **Significance level**: α = 0.05

**Metrics**:
- **U statistic**: Test statistic
- **p-value**: Statistical significance
- **Effect size**: Rank-biserial correlation

**Why non-parametric**:
- Engagement data is heavily skewed (few viral tweets, many low-engagement)
- Mann-Whitney U doesn't assume normal distribution
- More robust to outliers than t-test

### Controversy Threshold Analysis

**Purpose**: Determine empirical thresholds for classifying tweets as controversial.

**Method**: Empirical distribution analysis
- **Data**: Controversy scores across all tweets
- **Percentiles**: Calculate 75th, 90th, 95th percentiles
- **Threshold**: Tweets above 90th percentile classified as controversial

**Output**:
- Distribution of controversy scores
- Threshold values for classification
- Count of controversial vs non-controversial tweets

## Infrastructure

### Compute

**Primary VPS**: DigitalOcean, Singapore region
- **Specs**: 4 vCPU / 8GB RAM
- **Purpose**: Pipeline execution, dashboard hosting
- **OS**: Ubuntu 22.04 LTS
- **GPU**: Not available (CPU-only inference, slower but cost-effective)

**Why Singapore region**:
- Low latency to Twitter/X API servers
- Proximity to Indonesian user base (primary data source)
- DigitalOcean data sovereignty compliance

### Storage

**Primary**: DigitalOcean Spaces (S3-compatible)
- **Region**: `sgp1` (Singapore)
- **Bucket**: `mbg-scraper-network-20260419071440`
- **Contents**: Pipeline outputs (timestamped runs), analysis CSVs, model files
- **Local fallback**: `/opt/mbg/data/` on VPS

**Storage Strategy**:
- Pipeline runs: Each run creates a new folder with timestamp
- Analysis outputs: Overwritten each run (no versioning)
- Raw data: Preserved permanently (never deleted)
- Models: Fine-tuned models stored for reproducibility

### Code & Deployment

**Version control**: GitHub (`FatwaArya/mbg-analysis`)
- **Branch**: `main` (production)
- **CI/CD**: GitHub Actions
  - Auto-deploy dashboard on push to `main`
  - Manual trigger for pipeline execution
  - Data contract validation on PR

**Dashboard**: Streamlit + Plotly
- **Port**: 8501
- **Service**: systemd (`mbg-dashboard.service`)
- **Pages**: 7 research-driven pages
- **Auto-refresh**: On data update

### Reproducibility

**Run Tracking**:
- Every pipeline run is timestamped (`YYYYMMDD_HHMMSS`)
- Outputs uploaded to `runs/{run_id}/` in Spaces
- `latest_run.json` manifest at bucket root tracks current run
- Git commit hash recorded in each manifest for code-data linkage

**Data Freshness**:
- Local files overwritten each run (no caching)
- Ensures fresh processing from raw data
- No stale intermediate files

**Version Pinning**:
- Python dependencies in `requirements.txt`
- Model versions specified in pipeline config
- Docker not used (direct VPS deployment)

## Environment Setup

### Prerequisites

**Python Version**: 3.11+

**System Dependencies**:
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git
```

**Python Dependencies** (`requirements.txt`):
```
# NLP Libraries
transformers>=4.30.0
torch>=2.0.0
sastrawi>=1.0.1
nltk>=3.8.1
spacy>=3.5.0
langdetect>=1.0.9

# Topic Modeling
bertopic>=0.14.0
umap-learn>=0.5.3
hdbscan>=0.8.29
gensim>=4.3.0

# Data Processing
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.2.0

# Visualization
plotly>=5.14.0
streamlit>=1.22.0

# Storage
boto3>=1.26.0  # For DigitalOcean Spaces (S3-compatible)

# Utilities
tqdm>=4.65.0
```

### Installation

```bash
# Clone repository
git clone https://github.com/FatwaArya/mbg-analysis.git
cd mbg-analysis

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data
python3 -c "import nltk; nltk.download('stopwords')"
```

### Configuration

**Environment Variables**:
```bash
export DO_SPACES_KEY="your_spaces_key"
export DO_SPACES_SECRET="your_spaces_secret"
export DO_SPACES_BUCKET="mbg-scraper-network-20260419071440"
export DO_SPACES_REGION="sgp1"
```

**Pipeline Configuration** (`config.yaml`):
```yaml
sentiment_model: "w11wo/indonesian-roberta-base-sentiment-classifier"
relevance_model: "mbg-indobert-finetuned"
relevance_threshold: 0.80
bot_threshold: 0.50
topic_range: [2, 20]
```

### Pipeline Execution

**Run Complete Pipeline**:
```bash
cd /opt/mbg
source venv/bin/activate
python3 scripts/run_pipeline.py
```

**Run Individual Stages**:
```bash
# Stage 1: Relevance filtering
python3 analysis/relevance_filter.py

# Stage 2: Text preprocessing
python3 analysis/preprocess.py

# Stage 3: Sentiment analysis
python3 analysis/sentiment_analysis.py

# Stage 4: Topic modeling
python3 analysis/topic_modeling.py

# Stage 5: Reply pipeline (R1-R7)
python3 scripts/run_reply_pipeline.py

# Stage 6: Statistical analysis
python3 analysis/statistical_analysis.py
python3 analysis/bot_detection.py
python3 analysis/influence_scoring.py
python3 analysis/network_analysis.py
```

**Upload Results to Spaces**:
```bash
python3 scripts/upload_to_spaces.py --run-id $(date +%Y%m%d_%H%M%S)
```

## Known Limitations

### Data Limitations

1. **API Access Restrictions**
- Twitter/X API access is limited and may change
- Historical data may be incomplete (deleted tweets, suspended accounts)
- Rate limiting may affect data collection completeness

2. **Language Bias**
- Dataset primarily Indonesian language
- Non-Indonesian tweets may be underrepresented
- Sentiment model optimized for Indonesian, may misclassify other languages

3. **Temporal Coverage**
- Date range: March 2017 – April 2026
- Early tweets may have lower quality (less standardized)
- Recent tweets may not yet reflect long-term trends

### Model Limitations

1. **Sentiment Classification**
- Model accuracy ~85% (estimated), not 100%
- Sarcasm and irony may be misclassified
- Context-dependent sentiment may be lost

2. **Topic Modeling**
- 51 topics may not capture all discourse themes
- Topic boundaries are fuzzy (tweets may span multiple topics)
- Outlier tweets (topic_id = -1) are not analyzed

3. **Bot Detection**
- Composite score is heuristic-based, not ML-based
- Sophisticated bots may evade detection
- False positives: Active human users may be flagged

### Infrastructure Limitations

1. **Compute Resources**
- 4 vCPU / 8GB RAM limits parallel processing
- CPU-only inference (no GPU) slows model inference
- Large datasets may cause memory issues

2. **Storage**
- DigitalOcean Spaces has egress costs
- No versioning on analysis outputs (overwritten each run)
- Raw data preserved but processed data may be lost

3. **Reproducibility**
- Pipeline runs are timestamped but not version-controlled
- Model weights may change if retrained
- External API changes may affect data collection

### Mitigation Strategies

1. **Data Quality**
- Multiple search queries to maximize coverage
- Deduplication by tweet ID
- Relevance filtering to remove noise

2. **Model Validation**
- F1 score reported for relevance filtering
- Manual inspection of sample outputs
- Cross-validation on sentiment model

3. **Infrastructure Resilience**
   - Local fallback storage (`/opt/mbg/data/`)
   - Git commit tracking for code-data linkage
   - Timestamped runs for audit trail

## Data Validation & Quality Gates

### Data Contract Validation

The pipeline enforces a strict data contract via `scripts/validate_data_contract.py`. This script runs as Step 6 of the full pipeline and aborts the run if validation fails.

**Pipeline Output Contract** (required columns):

| File | Required Columns |
|------|-----------------|
| `tweets_with_sentiment.csv` | `text`, `date`, `sentiment_normalized`, `detected_lang` |
| `tweets_with_topics.csv` | `text`, `date`, `sentiment_normalized`, `topic_id`, `detected_lang` |
| `topic_info.csv` | `Topic`, `Count`, `Name` |

**Analysis Output Contract** (optional, validated with `--analysis` flag):

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

Each gate must pass before the pipeline proceeds to the next stage:

| Gate | Stage | Criteria | Action on Failure |
|------|-------|----------|-------------------|
| G1: Relevance rate | After Stage 1 | >= 50% tweets classified RELEVANT | Log warning, continue |
| G2: Preprocessing retention | After Stage 3 | >= 90% tweets pass length filter | Log warning, continue |
| G3: Schema validation | After Stage 6 | All required columns present | **Abort pipeline** |
| G4: Row count consistency | After Stage 6 | Sentiment rows == Topic rows +/- 1% | Log warning, continue |
| G5: Upload verification | After Stage 7 | All files uploaded successfully | **Abort pipeline** |

### Validation Command

```bash
# Validate pipeline outputs only (default)
python3 scripts/validate_data_contract.py

# Validate pipeline + analysis outputs
python3 scripts/validate_data_contract.py --analysis
```

**Exit codes**:
- `0`: All validations passed
- `1`: One or more validations failed (details printed to stdout)

> **Cross-reference**: See [PIPELINE_EVIDENCE.md](PIPELINE_EVIDENCE.md#data-contract-validation) for validation output samples and schema details.

## Monitoring & Alerting

### Pipeline Monitoring Tools

The project includes two monitoring scripts for tracking pipeline execution:

#### Quick Status (`scripts/pipeline_status.sh`)

Returns a single-line summary of pipeline state:

```bash
$ bash scripts/pipeline_status.sh
RUNNING: SENT | Files: ✓rel ✓sent  [CHECKPOINT]
```

**Status indicators**:
- `IDLE`: No pipeline processes running
- `RUNNING: INF TAG PRE SENT TOP`: Active pipeline stages (abbreviated)
- `✓rel ✓sent ✓top`: Output files that exist
- `[CHECKPOINT]`: Sentiment checkpoint file present (resume available)

#### Live Monitor (`scripts/monitor_pipeline.sh`)

Full-screen dashboard refreshing every 10 seconds. Shows:

1. **Pipeline lock status**: Running PID, stale lock detection
2. **Step-by-step status**: Each stage shows RUNNING/DONE/PREV RUN/IDLE
3. **Sentiment progress**: Current batch progress (e.g., `50000/107039`)
4. **Output files**: Row count, file size, and modification time for each output
5. **Latest log tail**: Last 4 lines of most recent pipeline log
6. **Resource usage**: Memory and disk utilization

**Duplicate detection**: The monitor flags when multiple instances of the same step are running simultaneously (shown as `RUNNING x2 ⚠ DUPLICATE`).

### Pipeline Locking

The full pipeline (`run_full_pipeline.sh`) uses a lockfile mechanism to prevent concurrent execution:

- **Lockfile**: `/tmp/mbg_pipeline.lock`
- **Behavior**: If lock exists and PID is alive, pipeline aborts with message
- **Cleanup**: Lock is automatically removed on exit, interrupt, or termination via `trap`

### Logging

All pipeline runs produce timestamped logs:

- **Location**: `/opt/mbg/logs/pipeline_{YYYYMMDD_HHMMSS}.log`
- **Format**: `[YYYY-MM-DD HH:MM:SS] message`
- **Content**: Step start/end timestamps, row counts, validation results, error messages
- **Summary**: Final log entry includes run ID, duration, and output file row counts

### Checkpoint & Resume

Sentiment analysis supports checkpoint-based resumption:

- **Checkpoint file**: `data/.sentiment_checkpoint.csv`
- **Behavior**: If checkpoint exists at pipeline start, it is cleared for a fresh run
- **Benefit**: If sentiment analysis crashes mid-run, manually re-running `run_sentiment.py` resumes from last checkpoint

> **Cross-reference**: See [PIPELINE_EVIDENCE.md](PIPELINE_EVIDENCE.md#monitoring--alerting) for monitoring output samples and screenshots.

## Troubleshooting

### Real Issues and Resolutions (from Git History)

The following issues were encountered during development and resolved in production:

#### 1. Tweet ID Precision Loss (`05bec8e`)

- **Symptom**: Tweet IDs like `1234567890123456789` were being truncated to `1234567890123456700` when read as integers
- **Root cause**: Pandas default integer type (`int64`) loses precision for IDs > 2^53
- **Fix**: Read ID column as string: `pd.read_csv(..., dtype={'id': str})`
- **Impact**: All tweet ID joins and deduplication now use string comparison

#### 2. GPU Not Used for R7 Sentiment (`a6d91a1`)

- **Symptom**: Reply sentiment analysis (R7) was running on CPU, taking ~8 hours instead of ~2 hours
- **Root cause**: Script defaulted to CPU device, did not check CUDA availability
- **Fix**: Set `device=0` for CUDA GPU inference
- **Verification**: Monitor GPU usage with `nvidia-smi` during R7 execution

#### 3. spaCy Truncation in R6 (`f106d33`)

- **Symptom**: Some long tweets (>1000 characters) were silently truncated during preprocessing
- **Root cause**: spaCy default `max_length` was too low for some tweet texts
- **Fix**: Increase `nlp.max_length` or reduce input text length before processing
- **Also added**: tqdm progress bars for R6 visibility

#### 4. Co-reply Network Timeout (`74ac6b7`)

- **Symptom**: Dashboard co-reply network visualization timed out (>30s) on large graphs
- **Root cause**: Force-directed layout computed on every page load
- **Fix**: Pre-compute layout positions during analysis, store in CSV
- **Also fixed**: KeyError for ego node color in network visualization

#### 5. ID Type Join Failures (`25fec64`)

- **Symptom**: Joins between parent tweets and replies returned zero matches
- **Root cause**: Mixed int/string types for user IDs across dataframes
- **Fix**: Standardize all ID columns to string type before joins

#### 6. Bot Threshold Too High (`995ddfc`)

- **Symptom**: Very few accounts flagged as bots with original threshold
- **Root cause**: Default threshold was too conservative for social media data
- **Fix**: Lower composite bot score threshold from 0.70 to 0.50
- **Also**: Optimized SNA script for better performance

#### 7. Broken Talk vs Amplify Visualization (`7dfded0`)

- **Symptom**: "Talk vs Amplify by Sentiment" dashboard page showed incorrect data
- **Root cause**: Calculation logic was broken after schema changes
- **Fix**: Replace with ratio distribution approach

### General Troubleshooting

#### Pipeline Runs Out of Memory (OOM)

```
Error: Killed process / signal 9
```

- **Cause**: Loading entire 200K+ reply dataset into memory with multiple copies
- **Solution**: Use chunked processing: `pd.read_csv(file, chunksize=10000)`
- **Prevention**: Monitor with `free -h` and `htop` during execution
- **Emergency**: If OOM occurs during sentiment analysis, checkpoint file enables resume

#### Model Download Fails

```
Error: ConnectionError or HTTP 429 from huggingface.co
```

- **Cause**: Network timeout or HuggingFace rate limiting
- **Solution**: Retry with exponential backoff; model auto-downloads from Spaces if local copy exists
- **Prevention**: Pre-cache model locally at `/opt/mbg/model/` (475 MB)

#### Stale Pipeline Lock

```
Pipeline already running (PID 12345). Aborting.
```

- **Cause**: Previous pipeline crashed without cleaning up lockfile
- **Solution**: `rm /tmp/mbg_pipeline.lock`
- **Verification**: Check if PID is actually alive: `kill -0 12345`

#### Sentiment Checkpoint Corruption

```
Error: ValueError: Unable to parse string in sentiment checkpoint
```

- **Cause**: Checkpoint file was partially written before crash
- **Solution**: Delete checkpoint to force fresh run: `rm data/.sentiment_checkpoint.csv`
- **Note**: Pipeline clears checkpoints automatically at start of each full run

#### DigitalOcean Spaces Upload Fails

```
Error: s3cmd failed: [Errno 111] Connection refused
```

- **Cause**: Network issues or invalid Spaces credentials
- **Solution**: Check `.env` file for `DO_SPACES_KEY` and `DO_SPACES_SECRET`
- **Retry**: Upload script automatically retries 3 times with 5-second delay
- **Cleanup**: Partial uploads are cleaned up automatically on failure

## Script API Reference

### `inference.py` — Relevance Filtering

| Parameter | Source | Default | Description |
|-----------|--------|---------|-------------|
| `MODEL_PATH` | `RUNTIME.model_dir` | `/opt/mbg/model` | Path to fine-tuned IndoBERT model |
| `DATA_DIR` | `RUNTIME.raw_dir` | `/opt/mbg/data/raw` | Directory containing input CSVs |
| `OUTPUT_DIR` | `RUNTIME.output_dir` | `/opt/mbg/data/output` | Directory for output files |
| `BATCH_SIZE` | `RUNTIME.inference_batch_size` | 64 (droplet) / 128 (colab) | Inference batch size |
| `MAX_LENGTH` | Hardcoded | 128 | Maximum token length for BERT input |

**Output files**: `tweets_relevant.csv`, `tweets_rejected.csv`, `tweets_borderline.csv`

**Key functions**:
- `load_model() -> (tokenizer, model)`: Load IndoBERT from local path
- `predict_batch(texts, tokenizer, model) -> list[dict]`: Batch inference, returns `predicted_label` + `predicted_confidence`
- `find_corpus_csv() -> str`: Auto-detect largest CSV in raw data directory
- `load_corpus(path) -> (DataFrame, text_col)`: Load and clean corpus
- `run_inference(df, text_col, tokenizer, model) -> DataFrame`: Full corpus inference
- `save_results(df)`: Split into relevant/rejected/borderline CSVs

### `scripts/run_full_pipeline.sh` — Pipeline Orchestrator

**Steps executed in order**:
1. Clear checkpoints and caches
2. Download model from Spaces if missing (475 MB)
3. Run inference (`inference.py`)
4. Run language tagging (`tag_language.py`)
5. Run text preprocessing (`preprocess_text.py`)
6. Run sentiment analysis (`run_sentiment.py`)
7. Run topic modeling (`run_topics.py`)
8. Validate data contract (`validate_data_contract.py`)
9. Generate manifest (`generate_manifest.py`)
10. Upload to Spaces (`upload_run.py`)

**Lockfile**: `/tmp/mbg_pipeline.lock` (prevents concurrent runs)
**Log**: `/opt/mbg/logs/pipeline_{RUN_ID}.log`

### `scripts/validate_data_contract.py` — Schema Validator

```
Usage: python3 scripts/validate_data_contract.py [--analysis]

Flags:
  --analysis    Also validate optional post-analysis CSV outputs

Exit codes:
  0    All validations passed
  1    One or more validations failed
```

### `scripts/generate_manifest.py` — Run Manifest Generator

```
Usage: python3 scripts/generate_manifest.py [RUN_ID] [DURATION_SECONDS]

Output: data/output/metadata.json

Manifest contains:
  - run_id: Timestamp identifier
  - git_commit: Short commit hash (via git rev-parse --short HEAD)
  - duration_seconds: Pipeline wall time
  - files: Per-file metadata (rows, size_mb, md5 hash truncated to 8 chars)
  - stats: Total tweets, sentiment distribution, topics discovered, outliers
```

### `scripts/upload_run.py` — Spaces Uploader

```
Usage: python3 scripts/upload_run.py

Requires: metadata.json (generated by generate_manifest.py)
Retry logic: 3 attempts with 5-second delay
Timeout: 60 seconds per s3cmd call
Cleanup: Partial uploads cleaned up on failure
Output: s3://mbg-scraper-network-20260419071440/runs/{RUN_ID}/
```

### `runtime.py` — Shared Runtime Configuration

**Dataclass**: `RuntimeConfig` (frozen, immutable after creation)

| Field | Droplet Value | Colab Value | Description |
|-------|--------------|-------------|-------------|
| `runtime_mode` | `"droplet"` | `"colab"` | Environment identifier |
| `data_dir` | `/opt/mbg/data` | `/content/drive/MyDrive/mbg/data` | Base data directory |
| `model_dir` | `/opt/mbg/model` | `/content/drive/MyDrive/mbg/model` | Model directory |
| `logs_dir` | `/opt/mbg/logs` | `/content/drive/MyDrive/mbg/logs` | Logs directory |
| `device` | `"cuda"` or `"cpu"` | `"cuda"` (required) | PyTorch device |
| `hf_device` | `0` or `-1` | `0` | HuggingFace device index |
| `inference_batch_size` | 64 | 128 | Inference batch size |
| `sentiment_batch_size` | 32 | 64 | Sentiment batch size |
| `embedding_batch_size` | 64 | 128 | Embedding batch size |

**Derived properties**:
- `processed_dir`: `{data_dir}/processed`
- `output_dir`: `{data_dir}/output`
- `raw_dir`: `{data_dir}/raw`

> **Note**: Colab mode requires CUDA and will raise `RuntimeError` if no GPU is detected.

## FAQ

### General

**Q: How many tweets are in the final dataset?**
A: 107,039 parent tweets with sentiment labels and topic assignments, plus ~150,000+ processed replies.

**Q: Why are some tweets assigned topic_id = -1?**
A: Topic ID -1 indicates an outlier tweet that did not fit well into any discovered cluster. This is expected behavior from HDBSCAN clustering, typically affecting 5-15% of tweets.

**Q: How accurate is the sentiment analysis?**
A: The Indonesian RoBERTa sentiment model achieves approximately 85% accuracy on similar tasks. Sarcasm, irony, and context-dependent sentiment may be misclassified.

**Q: What does the bot score mean?**
A: The bot score (0-1) is a composite of 5 signals: username anomaly, posting regularity, content similarity, engagement ratio, and account age. Scores > 0.50 are flagged as potential bots.

**Q: What time period does the data cover?**
A: March 2017 through April 2026, approximately 9 years of discourse around the MBG program.

### Technical

**Q: Why use a hybrid LDA + BERTopic approach?**
A: LDA provides global topic structure (macro themes), while BERTopic discovers fine-grained sub-themes within each LDA topic. The combination captures both broad discourse patterns and specific talking points.

**Q: Why is the pipeline CPU-only on the VPS?**
A: The DigitalOcean VPS (4 vCPU, 8GB RAM) does not have a GPU. CPU inference is slower but cost-effective. The `colab` runtime mode enables GPU acceleration on Google Colab.

**Q: How does the pipeline handle duplicate tweets?**
A: Tweets are deduplicated by tweet ID across all 23 search queries before any processing begins. The deduplication happens during the initial data collection phase.

**Q: What happens if the pipeline crashes mid-run?**
A: The pipeline uses checkpoint files for sentiment analysis (resume support) and lockfiles to prevent concurrent runs. To recover: remove the lockfile (`rm /tmp/mbg_pipeline.lock`), then re-run the pipeline. The full pipeline clears checkpoints at start for consistency.

**Q: How are language tags used?**
A: Language detection (`langdetect`) tags each tweet as Indonesian, English, or other. The sentiment model is optimized for Indonesian text; non-Indonesian tweets may have lower sentiment accuracy.

**Q: What is the maximum token length for BERT inference?**
A: 128 tokens. Tweets longer than this are truncated. This covers the vast majority of tweets (which are limited to 280 characters).

## Cross-References

This document is part of the MBG Analysis evidence package. Related documents:

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| [PIPELINE_EVIDENCE.md](PIPELINE_EVIDENCE.md) | Pipeline execution evidence, output samples, architecture | Run history, storage contents, output samples |
| [DATA_SAMPLES.md](DATA_SAMPLES.md) | Representative data samples from each pipeline stage | Raw data, processed data, analysis outputs |
| [ETHICS.md](ETHICS.md) | Ethical considerations and data handling | Privacy, consent, bias mitigation |
| [RESEARCH_PAPER.md](RESEARCH_PAPER.md) | Full research paper with findings | Analysis results, discussion, conclusions |

**Key cross-references from PIPELINE_EVIDENCE.md**:
- [Pipeline Run History](PIPELINE_EVIDENCE.md#pipeline-run-history) — Timestamped execution records
- [Data Schemas](PIPELINE_EVIDENCE.md#data-schemas) — Column definitions for all output files
- [Performance Benchmarks](PIPELINE_EVIDENCE.md#performance-benchmarks) — Processing time and resource usage
- [Troubleshooting Log](PIPELINE_EVIDENCE.md#troubleshooting-log) — Known issues with commit references

## Glossary

| Term | Definition |
|------|------------|
| **MBG** | Makan Bergizi Gratis — Indonesian government's free nutritious meal program |
| **SPPG** | Satuan Pelayanan Pemenuhan Gizi — Nutrition fulfillment service unit |
| **IndoBERT** | Indonesian BERT model pre-trained on Indonesian text corpus |
| **RoBERTa** | Robustly Optimized BERT Pretraining Approach |
| **LDA** | Latent Dirichlet Allocation — Generative probabilistic topic model |
| **BERTopic** | Topic modeling using BERT embeddings + UMAP + HDBSCAN |
| **UMAP** | Uniform Manifold Approximation and Projection — Dimensionality reduction |
| **HDBSCAN** | Hierarchical Density-Based Spatial Clustering |
| **c-TF-IDF** | Class-based TF-IDF for topic representation |
| **Louvain** | Community detection algorithm based on modularity optimization |
| **TF-IDF** | Term Frequency–Inverse Document Frequency |
| **F1 Score** | Harmonic mean of precision and recall |
| **C_v Coherence** | Normalized pointwise mutual information coherence metric |
| **Sentiment Entropy** | Shannon entropy applied to sentiment class distribution |
| **Controversy Score** | Composite metric measuring discourse contentiousness |
| **Bot Score** | Composite metric measuring likelihood of automated account |
| **Influence Score** | Composite metric measuring user's discourse impact |

## References

1. Devlin, J., et al. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.
2. Liu, Y., et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach.
3. Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure.
4. Blei, D., et al. (2003). Latent Dirichlet Allocation.
5. Blondel, V., et al. (2008). Fast unfolding of communities in large networks.
6. McInnes, L., et al. (2018). UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction.
7. Campello, R., et al. (2013). Density-based clustering based on hierarchical density estimates.
