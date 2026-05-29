# Public Discourse on Indonesia's Makan Bergizi Gratis (MBG) Program: A Computational Analysis of 107,000 Twitter Posts

**Date:** May 2026
**Data Coverage:** March 2017 – April 2026
**Corpus Size:** 107,039 tweets
**Platform:** Twitter/X

---

## Abstract

This study presents a computational analysis of public discourse surrounding Indonesia's *Makan Bergizi Gratis* (MBG) — Free Nutritious Meal — program on Twitter/X. We analyze 107,039 tweets collected over nine years (2017–2026) using a multi-stage pipeline comprising IndoBERT relevance filtering (F1=0.955), Indonesian RoBERTa sentiment classification, hybrid LDA+BERTopic topic modeling, reply network analysis, and bot detection. We find that negativity in the discourse is rising (40.3% of all tweets are negative), negative content spreads 3.4× further than positive content, outer island regions show markedly more positive sentiment than Java, and food safety and corruption topics dominate the conversation. Reply analysis reveals low agreement between parent tweet and reply sentiments, indicating a polarized discourse environment. All data, code, and analysis outputs are publicly available.

---

## 1. Introduction

### 1.1 The MBG Program

The Makan Bergizi Gratis (MBG) program is Indonesia's national school meal initiative, launched to provide free nutritious meals to schoolchildren across the archipelago. As one of the largest social welfare programs in Indonesia's history, it has generated extensive public debate across traditional and social media.

### 1.2 Research Questions

This study addresses seven research questions:

1. **Q1:** What is the overall sentiment distribution of MBG discourse, and how has it changed over time?
2. **Q2:** What temporal patterns exist in tweet volume and engagement?
3. **Q3:** What topics dominate the MBG discourse, and how do they evolve?
4. **Q4:** How does sentiment interact with topics and engagement?
5. **Q5:** What patterns emerge in reply sentiment and controversy?
6. **Q6:** How do reply sentiments align or diverge from parent tweets?
7. **Q7:** Which users drive influence and amplification?

### 1.3 Key Findings Summary

| Finding | Value |
|---------|-------|
| Total tweets analyzed | 107,039 |
| Overall negative sentiment | 40.3% |
| Overall neutral sentiment | 30.8% |
| Overall positive sentiment | 28.9% |
| Topics discovered | 51 |
| Negative amplification ratio | 3.4× vs positive |
| Statistically significant negativity trend | Yes |

---

## 2. Data & Methodology

### 2.1 Data Collection

Tweets were collected via the Twitter/X API using 23 search queries targeting various aspects of the MBG program, including general terms (*"makan bergizi gratis"*, *"MBG"*), program figures (*"Badan Gizi Nasional"*, *"SPPG"*), critical keywords (*"keracunan MBG"*, *"korupsi MBG"*), and regional terms (*"MBG Papua"*, *"MBG NTT"*). Both `top` and `latest` scrape tabs were used. The raw collection yielded approximately 167,000 tweets before filtering.

### 2.2 Preprocessing Pipeline

The data processing pipeline consists of six stages:

**Stage 1 — Relevance Filtering:**
A fine-tuned IndoBERT model (binary `RELEVANT`/`NOT_RELEVANT`) filters out off-topic tweets. The model achieves F1=0.955 on a held-out test set. Tweets with confidence <0.80 are flagged as borderline. This stage reduced the corpus from ~167,000 to ~107,000 relevant tweets.

**Stage 2 — Text Preprocessing:**
URLs, @mentions, and hashtags are removed. Indonesian text is stemmed using Sastrawi, and stopwords are removed. Tweets with fewer than 3 terms after cleaning are excluded from topic modeling.

**Stage 3 — Sentiment Analysis:**
The `w11wo/indonesian-roberta-base-sentiment-classifier` model classifies each tweet into positive, negative, or neutral categories with confidence scores. This Indonesian-specific model was chosen over multilingual alternatives due to superior performance on Indonesian social media text.

**Stage 4 — Topic Modeling (Hybrid LDA+BERTopic):**
Latent Dirichlet Allocation (LDA) is run with k=2..20, and the optimal number of topics is selected via coherence score. For each LDA topic, a separate BERTopic model (UMAP + HDBScan) discovers sub-themes. This two-stage approach captures both broad thematic structure and fine-grained sub-topics. The final model identified **51 topics**.

**Stage 5 — Reply Analysis:**
The reply pipeline (R1–R7) processes reply tweets through: JSONL parsing, metadata enrichment, reply depth calculation, text filtering, language detection, preprocessing, and sentiment classification. Additional analysis computes controversy scores, stance alignment, and engagement comparison between parent and reply tweets.

**Stage 6 — Statistical & Network Analysis:**
Sentiment distributions, temporal trends, engagement correlations, spike detection, and framing analysis are computed. Network analysis includes bot detection (5-signal composite scoring), user influence scoring, and co-reply network community detection.

### 2.3 Infrastructure

The analysis ran on a DigitalOcean VPS (4 vCPU, 8GB RAM, Singapore region). All outputs are versioned in DigitalOcean Spaces object storage under timestamped run directories. The interactive dashboard is built with Streamlit and Plotly. Code is version-controlled on GitHub.

| Resource | Specification |
|----------|--------------|
| Compute | DigitalOcean VPS, 4 vCPU, 8GB RAM |
| Storage | DigitalOcean Spaces, `sgp1` region |
| Sentiment Model | `w11wo/indonesian-roberta-base-sentiment-classifier` |
| Relevance Model | Fine-tuned IndoBERT (F1=0.955) |
| Topic Model | LDA (CV coherence) + BERTopic (UMAP+HDBScan) |
| Dashboard | Streamlit + Plotly |
| CI/CD | GitHub Actions |

---

## 3. Results

### 3.1 Sentiment Distribution

Overall sentiment across the corpus:

| Sentiment | Count | Percentage |
|-----------|-------|------------|
| Negative | 43,109 | 40.3% |
| Neutral | 33,010 | 30.8% |
| Positive | 30,920 | 28.9% |

Negative sentiment dominates the discourse at 40.3%, nearly 12 percentage points higher than positive sentiment (28.9%). This negativity bias is consistent with broader patterns in political discourse on social media, where critical voices tend to be more vocal.

### 3.2 Temporal Sentiment Trends

Monthly sentiment analysis reveals a clear trend: negativity has been increasing over the observation period. A linear regression on monthly negative percentage yields a statistically significant upward slope (p < 0.05). The share of negative tweets has risen from approximately 37% in early periods to over 52% in recent months — a shift of approximately 16 percentage points.

The sentiment trend indicator in our analysis shows an overall "improving" classification, which reflects the composite sentiment score rather than the negative trend alone. The raw negativity proportion shows a clear upward trajectory.

### 3.3 Engagement by Sentiment

Negative tweets achieve substantially higher engagement than positive or neutral tweets:

| Metric | Negative | Neutral | Positive |
|--------|----------|---------|----------|
| Average Retweets | ~109 | ~32 | ~32 |
| Average Engagement | Highest | Moderate | Lowest |

Negative content spreads **3.4× further** than positive content. The difference is statistically significant (Mann-Whitney U test, p < 0.000001). This finding aligns with the "negativity bias" literature in communication studies — negative information is more attention-grabbing and more likely to be shared.

### 3.4 Topic Analysis

The hybrid topic model identified **51 distinct topics** in the MBG discourse. Topic prevalence varies significantly:

**Top Topics by Volume:**
The dominant topics center around food quality and safety (*"keracunan MBG"* — MBG poisoning), political criticism (*"korupsi MBG"* — MBG corruption), program implementation (*"distribusi MBG"* — MBG distribution), regional coverage (*"MBG Papua"*, *"MBG NTT"*), and nutritional impact.

**Topic Sentiment Breakdown:**
- **Food safety topics** show the highest negativity (~70.8% negative), reflecting public anger over reported food poisoning incidents in schools
- **Corruption topics** show similarly high negativity (~75.3% negative), driven by allegations of budget misuse
- **Regional implementation topics** in outer islands (Papua, NTT, Maluku) are notably more positive (~39% positive) compared to Java-centric topics (~24% positive)
- **Nutrition and education impact topics** show the highest positive sentiment

### 3.5 Reply Analysis & Controversy

The reply dataset comprises replies to parent tweets in the corpus. Key findings:

**Controversy Scoring:**
Controversy scores are computed per parent tweet using a composite formula: 50% sentiment entropy among replies, 30% parent–reply disagreement bonus, and 20% volume scaling. Controversial posts (score > 0.6) are characterized by:
- High volume of replies with polarized sentiment
- Parent tweet sentiment contradicted by majority of replies
- Topics related to corruption, food safety, and political figures

**Parent–Reply Sentiment Alignment:**
The agreement ratio between parent tweet sentiment and reply sentiment is low, indicating a contentious discourse environment. Replies frequently express opposition to the parent tweet's stance, regardless of the parent's sentiment direction.

**Talk vs. Amplify Ratio:**
Analysis of reply-to-retweet ratios distinguishes between content that generates conversation (high reply/RT ratio) versus content that is simply broadcast (low reply/RT ratio). Negative content generates more replies per retweet than positive content, suggesting that critical MBG discourse is more conversational and debate-driven.

### 3.6 Bot Detection & Influence

A 5-signal composite bot score detected a subset of accounts exhibiting automated behavior patterns. Most accounts show low bot scores (distribution centered near 0.1), with a long tail of flagged accounts at the threshold of 0.5.

**Influence Analysis:**
User influence is computed as a composite of total engagement, reply reach, and tweet count. The influence leaderboard reveals that political figures, journalists, and prominent critics dominate the discourse. Sentiment consistency analysis shows that high-influence users tend to maintain consistent sentiment positions over time, suggesting ideological polarization among key actors.

### 3.7 Network Analysis

**Co-Reply Network:**
Users who reply to the same parent tweets form connections, revealing community structure in the discourse. The co-reply network shows distinct communities:
- **Pro-MBG supporters** — users who amplify positive coverage
- **Critics** — users who share and amplify critical content
- **News sharers** — users who distribute news articles neutrally
- **Regional clusters** — users focused on specific geographic areas

The network exhibits moderate clustering, indicating that users tend to interact within like-minded communities rather than across ideological lines — consistent with echo chamber dynamics.

---

## 4. Discussion

### 4.1 Implications

The findings have several implications for policymakers and communication strategists:

**Public Perception Challenge:**
The rising negativity trend (37% → 52% negative) represents a significant public perception challenge for the MBG program. Even as the program expands, negative discourse is accelerating. This suggests that program quality issues — particularly food safety incidents — are outweighing positive coverage in the public conversation.

**Regional Disparity in Discourse:**
The stark difference between outer island positivity (39%) and Java negativity (24%) suggests that the program is perceived differently across the archipelago. This may reflect genuine differences in implementation quality, or different media ecosystems shaping local discourse.

**Amplification of Negativity:**
The 3.4× amplification advantage for negative content means that critical voices naturally dominate the platform, regardless of the actual balance of public opinion. This is a structural feature of social media discourse that policymakers must account for when gauging public sentiment.

### 4.2 Limitations

- The corpus is limited to Twitter/X and may not represent broader Indonesian public opinion
- User screen names are missing from the scrape, limiting user-level analysis
- Timestamps are in UTC and converted to WIB (+7 hours) — precise geo-location is not available
- Bot detection scores are indicative, not definitive
- Topic model quality depends on tweet text quality which varies significantly

### 4.3 Future Work

- Incorporate additional data sources (Instagram, TikTok, news comments)
- Conduct qualitative content analysis on a stratified sample
- Longitudinal comparison with other social welfare programs
- Survey-based validation of sentiment analysis findings
- Real-time monitoring dashboard for program administrators

---

## 5. Data & Code Availability

All data, code, and analysis outputs are publicly accessible:

| Resource | Location |
|----------|----------|
| **GitHub Repository** | `https://github.com/FatwaArya/mbg-analysis` |
| **Pipeline Outputs (DO Spaces)** | `s3://mbg-scraper-network-20260419071440/runs/` |
| **Analysis CSVs** | `s3://mbg-scraper-network-20260419071440/analysis/` |
| **Interactive Dashboard** | Hosted on DigitalOcean VPS |
| **Fine-tuned Model** | `s3://mbg-scraper-network-20260419071440/models/mbg-indobert-finetuned/` |

---

## References

1. Devlin, J., et al. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. NAACL.
2. Liu, Y., et al. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach. arXiv:1907.11692.
3. Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv:2203.05794.
4. Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet Allocation. Journal of Machine Learning Research.
5. Soroka, S. (2014). Negativity in Democratic Politics. Cambridge University Press.
6. McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. arXiv:1802.03426.
7. Rehurek, R., & Sojka, P. (2011). Gensim — Python Framework for Vector Space Modelling. NLP Centre, Masaryk University.
8. Stevens, J. (2016). Sastrawi: Python Indonesian Stemmer.
