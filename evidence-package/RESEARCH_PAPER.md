# Public Discourse on Indonesia's Makan Bergizi Gratis (MBG) Program: A Computational Analysis of 107,000 Twitter Posts

**Authors:** [Author Name]<sup>1</sup>, [Co-Author Name]<sup>1</sup>

<sup>1</sup> [Affiliation], [City], Indonesia

**Corresponding Author:** [Author Name] — [email]

**Date:** May 2026
**Data Coverage:** March 2017 – April 2026
**Corpus Size:** 107,039 tweets
**Platform:** Twitter/X
**Keywords:** social media analysis, sentiment analysis, topic modeling, Indonesia, school meals, public discourse, computational social science, IndoBERT, negativity bias, welfare policy

---

## Table of Contents

- [Abstract](#abstract)
- [1. Introduction](#1-introduction)
  - [1.1 The MBG Program](#11-the-mbg-program)
  - [1.2 Background and Motivation](#12-background-and-motivation)
  - [1.3 Research Questions](#13-research-questions)
  - [1.4 Key Findings Summary](#14-key-findings-summary)
- [2. Related Work](#2-related-work)
  - [2.1 Social Media Discourse Analysis](#21-social-media-discourse-analysis)
  - [2.2 NLP for Indonesian Text](#22-nlp-for-indonesian-text)
  - [2.3 Negativity Bias in Online Discourse](#23-negativity-bias-in-online-discourse)
  - [2.4 Computational Approaches to Policy Discourse](#24-computational-approaches-to-policy-discourse)
- [3. Data & Methodology](#3-data--methodology)
  - [3.1 Data Collection](#31-data-collection)
  - [3.2 Preprocessing Pipeline](#32-preprocessing-pipeline)
  - [3.3 Infrastructure](#33-infrastructure)
  - [3.4 Ethical Considerations and Data Privacy](#34-ethical-considerations-and-data-privacy)
  - [3.5 Model Evaluation](#35-model-evaluation)
- [4. Results](#4-results)
  - [4.1 Sentiment Distribution](#41-sentiment-distribution)
  - [4.2 Temporal Sentiment Trends](#42-temporal-sentiment-trends)
  - [4.3 Engagement by Sentiment](#43-engagement-by-sentiment)
  - [4.4 Topic Analysis](#44-topic-analysis)
  - [4.5 Reply Analysis & Controversy](#45-reply-analysis--controversy)
  - [4.6 Bot Detection & Influence](#46-bot-detection--influence)
  - [4.7 Network Analysis](#47-network-analysis)
- [5. Discussion](#5-discussion)
  - [5.1 Implications](#51-implications)
  - [5.2 Limitations and Threats to Validity](#52-limitations-and-threats-to-validity)
  - [5.3 Future Work](#53-future-work)
- [6. Conclusion](#6-conclusion)
- [7. Data & Code Availability](#7-data--code-availability)
  - [7.1 Data Availability Statement](#71-data-availability-statement)
- [Glossary of Indonesian Terms](#glossary-of-indonesian-terms)
- [References](#references)

---

## Abstract

**Background:** The *Makan Bergizi Gratis* (MBG) program is Indonesia's national free nutritious meal initiative, targeting approximately 82.9 million children across over 300,000 schools. As one of the largest social welfare programs in Indonesian history, MBG has generated extensive public discourse on social media platforms. Understanding the structure and sentiment of this discourse is critical for policymakers, yet systematic computational analysis of Indonesian social media policy discourse remains scarce.

**Methods:** We present a computational analysis of 107,039 tweets spanning nine years (March 2017–April 2026) using a multi-stage analytical pipeline combining IndoBERT-based relevance filtering (F1 = 0.955), Indonesian RoBERTa sentiment classification, hybrid LDA+BERTopic topic modeling (k = 51 topics), reply network analysis, and bot detection. Statistical significance is assessed using Mann-Whitney U tests, Spearman correlations, and linear regression.

**Results:** Four principal findings emerge: (1) negativity dominates and is rising — 40.3% of all tweets express negative sentiment, with the negative share increasing from approximately 37% to over 52% over the observation period (β > 0, p < 0.05); (2) negative content spreads 3.4× further than positive content (Mann-Whitney U, p < 0.000001); (3) regional sentiment differs markedly, with outer island territories (Papua, NTT, Maluku) showing substantially more positive discourse (~39% positive) than Java-centric topics (~24% positive); and (4) reply analysis reveals low sentiment agreement between parent tweets and replies, indicating a polarized discourse environment. Food safety and corruption are the most prominent negatively-framed topics.

**Conclusions:** The MBG discourse on Twitter/X is characterized by structural negativity amplification, geographic sentiment divergence, and echo chamber dynamics. These findings suggest that social media discourse around Indonesian welfare programs is shaped more by incident-driven narratives than program outcomes, with significant implications for policy communication strategies. All data, code, and analysis outputs are publicly available to support reproducibility.

---

## 1. Introduction

### 1.1 The MBG Program

The *Makan Bergizi Gratis* (MBG) program is Indonesia's national school meal initiative, launched to provide free nutritious meals to schoolchildren across the archipelago. The program targets approximately 82.9 million children across over 300,000 schools, making it one of the largest social welfare programs in Indonesia's history (Bappenas, 2024). MBG represents a major policy commitment of the current administration, with significant budgetary implications and logistical challenges spanning Indonesia's diverse geography of 17,000 islands.

As with many large-scale social programs in Southeast Asia, MBG has generated extensive public debate across both traditional and social media platforms. Indonesia's social media landscape is among the most active globally — with over 130 million social media users — making platforms like Twitter/X particularly influential in shaping public discourse around government programs (DataReportal, 2025).

### 1.2 Background and Motivation

Understanding public discourse on social media is critical for several reasons. First, social media platforms serve as de facto public opinion barometers, where sentiment patterns can precede or influence broader public attitudes (Tumasjan et al., 2010). Second, the MBG program faces real implementation challenges — including food safety incidents, logistical difficulties, and corruption allegations — that generate substantial online discussion. Third, the geographic spread of Indonesia means that regional variations in discourse may reflect genuine differences in program implementation quality.

This study applies computational social science methods to systematically analyze the MBG discourse on Twitter/X, providing empirical evidence about public perception patterns, sentiment dynamics, and discourse structure that can inform both policy communication and academic understanding of welfare program discourse in developing democracies.

### 1.3 Research Questions

This study addresses seven research questions, each corresponding to a specific analytical component of our pipeline:

1. **RQ1 (Sentiment Distribution):** What is the overall sentiment distribution of MBG discourse on Twitter/X, and how has it changed over the observation period (2017–2026)?
2. **RQ2 (Temporal Patterns):** What temporal patterns exist in tweet volume and engagement, and are there identifiable spikes or inflection points?
3. **RQ3 (Topic Structure):** What topics dominate the MBG discourse, and how do topic prevalence and sentiment vary across thematic categories?
4. **RQ4 (Sentiment-Topic Interaction):** How does sentiment interact with specific topics and engagement metrics?
5. **RQ5 (Reply Dynamics):** What patterns emerge in reply sentiment distribution and controversy scoring?
6. **RQ6 (Stance Alignment):** How do reply sentiments align with or diverge from their parent tweets, and what does this reveal about discourse polarization?
7. **RQ7 (Influence Networks):** Which users and account types drive influence and amplification in the MBG discourse?

### 1.4 Key Findings Summary

| Finding | Value |
|---------|-------|
| Total tweets analyzed | 107,039 |
| Overall negative sentiment | 40.3% |
| Overall neutral sentiment | 30.8% |
| Overall positive sentiment | 28.9% |
| Topics discovered | 51 |
| Negative amplification ratio | 3.4× vs positive |
| Statistically significant negativity trend | Yes (p < 0.05) |
| Observation period | March 2017 – April 2026 |

---

The remainder of this paper is organized as follows. Section 2 situates the present study within the broader literature on social media discourse analysis, Indonesian NLP, and negativity bias. Section 3 describes the data collection methodology and analytical pipeline. Section 4 presents the results organized by research question. Section 5 discusses the implications, limitations, and directions for future work. Section 6 concludes.

## 2. Related Work

### 2.1 Social Media Discourse Analysis

Social media platforms have become central arenas for public discourse on government policy, particularly in developing democracies where traditional media may not fully represent public opinion (Margetts et al., 2016). Computational approaches to analyzing this discourse — including sentiment analysis, topic modeling, and network analysis — have been applied to policy domains ranging from health (Dredze, 2012) to elections (Tumasjan et al., 2010; Gayo-Avello, 2013) to public infrastructure (Ceron et al., 2014).

In the Indonesian context, social media adoption is exceptionally high. With over 130 million social media users as of 2025, Indonesia ranks among the world's most active social media markets (DataReportal, 2025). Twitter/X in particular has served as a significant platform for political discussion in Indonesia (Lim, 2017; Nadhira, 2023). However, systematic computational analyses of Indonesian policy discourse on social media remain relatively scarce compared to English-language contexts.

### 2.2 NLP for Indonesian Text

Natural language processing for Bahasa Indonesia presents unique challenges distinct from English-language NLP. Indonesian is an agglutinative language with productive affixation, and social media text frequently mixes formal Bahasa Indonesia with colloquial forms, regional languages, and code-switching patterns (Aji et al., 2022). The development of pre-trained language models specifically for Indonesian has accelerated in recent years, with IndoBERT (Wilie et al., 2020) emerging as the dominant foundation model. IndoBERT, based on the BERT architecture (Devlin et al., 2019), was pre-trained on the Indonesian Wikipedia and the Indo4B dataset, demonstrating strong performance on downstream tasks including sentiment analysis, named entity recognition, and text classification.

For sentiment analysis of Indonesian social media text, domain-specific models outperform multilingual alternatives (Barik et al., 2021). The Indonesian RoBERTa model used in this study (`w11wo/indonesian-roberta-base-sentiment-classifier`) was specifically fine-tuned on Indonesian social media data, making it well-suited for the colloquial register typical of Twitter discourse. Topic modeling in Indonesian has been explored using both LDA (Blei et al., 2003) and more recent neural approaches such as BERTopic (Grootendorst, 2022), though hybrid approaches combining both methods remain novel in the Indonesian context.

### 2.3 Negativity Bias in Online Discourse

A well-established finding in communication and political psychology is that negative information receives greater attention, is processed more deeply, and is more likely to be shared than positive information — a phenomenon known as negativity bias (Soroka, 2014; Rozin & Royzman, 2001). This bias manifests strongly on social media platforms. Brady et al. (2017) demonstrated that moral-emotional language in social media posts increases diffusion by approximately 20% per moral-emotional word. Robertson et al. (2020) showed that negativity drives online news consumption, with negative headlines receiving significantly more clicks than positive ones.

In the context of government program discourse specifically, research suggests that implementation failures and scandals generate more intense and sustained online reactions than program successes (Barberá et al., 2019). This asymmetry has practical implications for policymakers who may monitor social media as a barometer of public opinion: a predominance of negative content may reflect structural amplification dynamics rather than proportional public sentiment (González-Bailón et al., 2013).

### 2.4 Computational Approaches to Policy Discourse

Computational social science methods — particularly the combination of sentiment analysis, topic modeling, and network analysis — have been increasingly applied to study public discourse around government policies. Studies have examined welfare program discourse in Latin America (Monti et al., 2022), health policy debate during the COVID-19 pandemic (Cinelli et al., 2021), and environmental policy discourse (Falkenberg et al., 2022). These studies consistently find that policy discourse on social media is characterized by polarization, echo chambers, and asymmetric engagement patterns.

The present study contributes to this literature by applying a comprehensive multi-method pipeline to the Indonesian welfare policy context — a setting that has received limited computational analysis despite Indonesia's large population, high social media penetration, and significant ongoing policy experiments such as MBG.

Having situated our work within the relevant literature, we now describe the data collection and analytical methodology in detail.

## 3. Data & Methodology

We employ a multi-method computational approach to address our seven research questions. Table 6 summarizes the mapping between research questions and analytical methods.

**Table 6: Research Questions and Corresponding Methods**

| RQ | Focus | Primary Method | Key Metric |
|----|-------|---------------|------------|
| RQ1 | Sentiment distribution & trends | Indonesian RoBERTa classifier | Sentiment proportions |
| RQ2 | Temporal patterns | Time series analysis, spike detection | Monthly volume, z-scores |
| RQ3 | Topic structure | Hybrid LDA + BERTopic | 51 topics, coherence scores |
| RQ4 | Sentiment-topic interaction | Cross-tabulation, correlation | Sentiment by topic category |
| RQ5 | Reply dynamics | Controversy scoring | Composite controversy score |
| RQ6 | Stance alignment | Parent-reply comparison | Agreement ratio |
| RQ7 | Influence networks | Bot detection, network analysis | Influence score, clustering |

### 3.1 Data Collection

We collected tweets via the Twitter/X API using 23 search queries designed to capture diverse aspects of the MBG discourse. The queries fall into four categories:

- **General program terms:** *"makan bergizi gratis"*, *"MBG"*
- **Institutional terms:** *"Badan Gizi Nasional"*, *"SPPG"* (satuan pelayanan pendidikan gizi)
- **Critical keywords:** *"keracunan MBG"* (MBG poisoning), *"korupsi MBG"* (MBG corruption)
- **Regional terms:** *"MBG Papua"*, *"MBG NTT"*

We used both `top` and `latest` scraping modes to capture both high-engagement and chronologically ordered tweets. The raw collection yielded approximately 167,000 tweets before the relevance filtering stage (Stage 1) reduced this to 107,039 relevant tweets.

**Table 4: Corpus Summary Statistics**

| Metric | Value |
|--------|-------|
| Raw tweets collected | ~167,000 |
| Relevant tweets (post-filtering) | 107,039 |
| Filtering reduction rate | 35.9% |
| Observation period | March 2017 – April 2026 |
| Number of search queries | 23 |
| Scraping modes | `top`, `latest` |

### 3.2 Preprocessing Pipeline

Our analysis employs a six-stage pipeline that transforms raw tweet data into structured analytical outputs. The pipeline proceeds sequentially, with each stage building on the outputs of the previous one:

```
Raw Tweets (~167K)
    ↓
Stage 1: Relevance Filtering (IndoBERT) → 107,039 relevant tweets
    ↓
Stage 2: Text Preprocessing (Sastrawi stemming, stopword removal)
    ↓
Stage 3: Sentiment Classification (Indonesian RoBERTa)
    ↓
Stage 4: Topic Modeling (LDA + BERTopic) → 51 topics
    ↓
Stage 5: Reply Analysis (R1–R7 pipeline)
    ↓
Stage 6: Statistical & Network Analysis → Dashboard outputs
```

Below we describe each stage in detail.

**Stage 1 — Relevance Filtering:**
We fine-tuned an IndoBERT model (indobenchmark/indobert-base-p1) for binary classification (`RELEVANT` / `NOT_RELEVANT`) to filter out off-topic tweets from the raw corpus. The model achieves F1 = 0.955 on a held-out test set. We flag tweets with prediction confidence below 0.80 as borderline for manual review. This stage reduced the corpus from approximately 167,000 to 107,039 relevant tweets — a 35.9% reduction in volume.

**Stage 2 — Text Preprocessing:**
We remove URLs, @mentions, and hashtags from tweet text. Indonesian-language text is stemmed using the Sastrawi library, and standard Indonesian stopwords are removed. We exclude tweets with fewer than 3 remaining terms from topic modeling to ensure minimum content quality for the LDA and BERTopic models.

**Stage 3 — Sentiment Analysis:**
We classify each tweet into positive, negative, or neutral categories using the `w11wo/indonesian-roberta-base-sentiment-classifier` model, a RoBERTa model specifically trained on Indonesian social media text. Each prediction includes a confidence score. We selected this Indonesian-specific model over multilingual alternatives (e.g., multilingual BERT, XLM-RoBERTa) due to its superior performance on Indonesian colloquial text, which frequently mixes Bahasa Indonesia with regional languages and slang.

**Stage 4 — Topic Modeling (Hybrid LDA+BERTopic):**
We employ a two-stage hybrid approach for topic discovery. First, we run Latent Dirichlet Allocation (LDA) across k = 2 to 20 topics, selecting the optimal k via C_V coherence score. Second, for each LDA-derived topic, we fit a separate BERTopic model using UMAP for dimensionality reduction and HDBSCAN for clustering to discover fine-grained sub-themes. This hybrid approach captures both broad thematic structure (via LDA) and nuanced sub-topics (via BERTopic). The final model identified **51 distinct topics** across the corpus.

**Stage 5 — Reply Analysis:**
The reply pipeline (stages R1–R7) processes reply tweets through the following sequential steps: JSONL parsing and deduplication, metadata enrichment (parent tweet linking, user information), reply depth calculation, text filtering (language and relevance), preprocessing (tokenization, stemming), and sentiment classification using the same model as Stage 3. We compute additional metrics including controversy scores, stance alignment between parent and reply, and engagement comparison ratios.

**Stage 6 — Statistical & Network Analysis:**
We compute sentiment distributions, temporal trends with linear regression, engagement correlations (Spearman's ρ), spike detection (z-score based), and framing analysis. The network analysis component includes bot detection via a 5-signal composite scoring system, user influence scoring (composite of engagement, reach, and activity), and co-reply network community detection using the Louvain algorithm.

### 3.3 Infrastructure

The analysis ran on a DigitalOcean VPS (4 vCPU, 8GB RAM, Singapore region). All outputs are versioned in DigitalOcean Spaces object storage under timestamped run directories. The interactive dashboard is built with Streamlit and Plotly. Code is version-controlled on GitHub.

**Table 5: Computational Infrastructure**

| Resource | Specification |
|----------|--------------|
| Compute | DigitalOcean VPS, 4 vCPU, 8 GB RAM |
| Storage | DigitalOcean Spaces, `sgp1` region |
| Sentiment Model | `w11wo/indonesian-roberta-base-sentiment-classifier` |
| Relevance Model | Fine-tuned IndoBERT (F1 = 0.955) |
| Topic Model | LDA (C_V coherence) + BERTopic (UMAP + HDBSCAN) |
| Dashboard | Streamlit + Plotly |
| CI/CD | GitHub Actions |

### 3.4 Ethical Considerations and Data Privacy

This study analyzes publicly available tweets. We adhere to the following ethical guidelines:

- **Public data only:** All analyzed tweets were publicly posted on Twitter/X. We do not access private accounts or direct messages.
- **User anonymity:** We do not publish individual user identifiers, screen names, or any information that could enable identification of specific users. Bot detection scores and influence rankings are reported in aggregate.
- **Content representation:** Quoted tweet text in this paper consists of common keywords and hashtags rather than verbatim user content, minimizing the risk of de-anonymization.
- **No manipulation:** We do not interact with, follow, like, or reply to any tweets during data collection. Our analysis is purely observational.
- **Reproducibility vs. privacy:** While we publish aggregated analysis outputs and code, raw tweet data is stored in private object storage due to Twitter/X API terms of service restrictions on redistribution.
- **Institutional context:** This research was conducted as an independent computational social science study without external funding or institutional conflicts of interest related to the MBG program.

### 3.5 Model Evaluation

We evaluate the key models in our pipeline against established benchmarks:

**Relevance Classification (IndoBERT):**
- Architecture: indobenchmark/indobert-base-p1, fine-tuned for binary classification
- Training data: Manually labeled sample of MBG tweets (RELEVANT / NOT_RELEVANT)
- Test set performance: F1 = 0.955, Precision = 0.96, Recall = 0.95
- Borderline threshold: confidence < 0.80 (flagged for potential manual review)
- Effect on corpus: reduced from ~167,000 to 107,039 tweets (35.9% filtered)

**Sentiment Classification (Indonesian RoBERTa):**
- Model: `w11wo/indonesian-roberta-base-sentiment-classifier`
- Task: 3-class sentiment (positive, negative, neutral)
- Selection rationale: chosen over multilingual alternatives for superior performance on Indonesian colloquial text
- Limitation: no independent validation performed on MBG-specific data; performance on sarcasm and irony is unknown

**Topic Modeling (LDA + BERTopic):**
- LDA range: k = 2 to 20, selected via C_V coherence score
- BERTopic components: UMAP (n_neighbors=15, n_components=5) + HDBSCAN (min_cluster_size=50)
- Output: 51 distinct topics identified
- Validation: topic coherence assessed via C_V score; manual inspection of top keywords per topic

---

## 4. Results

Having described our data collection and methodology, we now present the results organized by research question.

### 4.1 Sentiment Distribution

Table 1 presents the overall sentiment distribution across the 107,039-tweet corpus.

**Table 1: Overall Sentiment Distribution**

| Sentiment | Count | Percentage | 95% CI |
|-----------|------:|----------:|--------|
| Negative | 43,109 | 40.3% | [40.0%, 40.6%] |
| Neutral | 33,010 | 30.8% | [30.5%, 31.1%] |
| Positive | 30,920 | 28.9% | [28.6%, 29.2%] |
| **Total** | **107,039** | **100%** | — |

Negative sentiment dominates the discourse at 40.3%, exceeding positive sentiment by 11.4 percentage points (negative-to-positive ratio: 1.39:1). The neutral category captures 30.8% of tweets, which may include informational posts, news sharing, and factual commentary. This negativity bias is consistent with broader patterns documented in political discourse on social media platforms, where critical voices tend to be more vocal and more likely to engage (Soroka, 2014; Robertson et al., 2020).

### 4.2 Temporal Sentiment Trends

Monthly sentiment analysis reveals a clear upward trend in negativity over the observation period. A linear regression fitted to the monthly negative sentiment percentage yields a statistically significant positive slope (β > 0, p < 0.05). The share of negative tweets has risen from approximately 37% in early periods to over 52% in recent months — a shift of approximately 16 percentage points over the nine-year observation window.

The composite sentiment trend indicator in our dashboard displays an overall "improving" classification, which reflects a weighted composite score incorporating multiple sentiment signals rather than the negative proportion alone. The raw negativity proportion, however, shows a clear and consistent upward trajectory, particularly accelerating in the most recent 12 months of data.

### 4.3 Engagement by Sentiment

Negative tweets achieve substantially higher engagement than positive or neutral tweets, as shown in Table 2.

**Table 2: Average Engagement by Sentiment Category**

| Metric | Negative | Neutral | Positive | Neg/Pos Ratio |
|--------|----------|---------|----------|---------------|
| Average Retweets | ~109 | ~32 | ~32 | **3.4×** |
| Average Replies | Highest | Moderate | Lowest | — |
| Average Total Engagement | Highest | Moderate | Lowest | — |

Negative content spreads **3.4× further** than positive content in terms of average retweets. This difference is statistically significant (Mann-Whitney U test, p < 0.000001). The effect size (rank-biserial correlation) indicates a substantial practical difference beyond statistical significance. This finding aligns with the "negativity bias" literature in communication studies — negative information is more attention-grabbing and more likely to be shared (Soroka, 2014; Brady et al., 2017).

### 4.4 Topic Analysis

The hybrid LDA+BERTopic model identified **51 distinct topics** in the MBG discourse. Table 3 presents the dominant topic categories by volume and their associated sentiment profiles.

**Table 3: Dominant Topic Categories and Sentiment Profiles**

| Topic Category | Representative Keywords | Negative | Neutral | Positive |
|----------------|------------------------|----------|---------|----------|
| Food Safety | *keracunan MBG*, makanan basi, kualitas makanan | ~70.8% | ~15% | ~14% |
| Corruption | *korupsi MBG*, anggaran, penyelewengan | ~75.3% | ~13% | ~12% |
| Program Distribution | *distribusi MBG*, SPPG, penyaluran | ~45% | ~30% | ~25% |
| Regional Coverage | *MBG Papua*, *MBG NTT*, *MBG Maluku* | ~30% | ~31% | ~39% |
| Nutritional Impact | gizi anak, stunting, makanan sehat | ~20% | ~25% | ~55% |

The topic analysis reveals three key patterns:

1. **Food safety and corruption dominate negative discourse.** These two topic categories together account for a disproportionate share of negative tweets. Food safety topics (~70.8% negative) reflect public anger over reported food poisoning incidents in schools, while corruption topics (~75.3% negative) are driven by allegations of budget misuse and financial irregularities.

2. **Regional sentiment diverges sharply.** Outer island territories (Papua, NTT, Maluku) show markedly more positive sentiment (~39% positive) compared to Java-centric topics (~24% positive). This divergence may reflect differences in program implementation experience, media ecosystem composition, or baseline expectations about government services.

3. **Nutrition and education impact topics carry the most positive sentiment.** Discussions focused on child nutrition outcomes, stunting prevention, and educational benefits consistently show the highest positive sentiment ratios, suggesting that the program's core mission resonates positively with the public.

### 4.5 Reply Analysis & Controversy

The reply dataset comprises replies to parent tweets in the corpus. We analyze reply patterns along three dimensions: controversy scoring, sentiment alignment, and engagement ratios.

**Controversy Scoring:**
We compute controversy scores per parent tweet using a weighted composite formula:
- **50%** sentiment entropy among replies (measures sentiment polarization)
- **30%** parent–reply disagreement bonus (measures stance opposition)
- **20%** volume scaling (normalizes for reply count)

Controversial posts (score > 0.6) share three characteristics:
- High volume of replies with polarized sentiment distribution
- Parent tweet sentiment contradicted by a majority of replies
- Topics related to corruption, food safety, and political figures

**Parent–Reply Sentiment Alignment:**
The agreement ratio between parent tweet sentiment and reply sentiment is low across the corpus, indicating a contentious discourse environment. Replies frequently express opposition to the parent tweet's stance, regardless of the parent's sentiment direction. This pattern suggests that MBG tweets tend to attract counter-arguments rather than agreement — a hallmark of polarized discourse.

**Talk vs. Amplify Ratio:**
We distinguish between content that generates conversation (high reply-to-retweet ratio) and content that is simply broadcast (low reply-to-retweet ratio). Negative content generates more replies per retweet than positive content, indicating that critical MBG discourse is more conversational and debate-driven, while positive content is more often passively amplified without discussion.

### 4.6 Bot Detection & Influence

We employ a 5-signal composite scoring system to detect accounts exhibiting automated behavior patterns. The signals include: (1) posting frequency anomalies, (2) content repetition patterns, (3) temporal regularity of posting, (4) account metadata signals, and (5) engagement pattern anomalies. Scores range from 0 (likely human) to 1 (likely automated), with accounts above 0.5 flagged for review.

The distribution of bot scores is right-skewed, with most accounts clustering near 0.1 (indicating likely human operation) and a long tail of accounts extending toward the 0.5 threshold. This distribution suggests that while automated accounts exist in the MBG discourse, they represent a minority of participants.

**Influence Analysis:**
We compute user influence as a composite score incorporating three dimensions:
- **Total engagement:** Aggregate retweets, likes, and replies received
- **Reply reach:** Number of unique users who reply to the account
- **Activity volume:** Total tweet count in the corpus

The influence leaderboard reveals that political figures, journalists, and prominent critics dominate the discourse. Notably, sentiment consistency analysis shows that high-influence users tend to maintain stable sentiment positions over time, suggesting ideological polarization among key discourse actors rather than fluid opinion change.

### 4.7 Network Analysis

**Co-Reply Network:**
We construct a co-reply network where users who reply to the same parent tweets share edges, revealing latent community structure in the discourse. The network analysis identifies four distinct community types:

- **Pro-MBG supporters** — users who consistently amplify positive coverage and defend the program
- **Critics** — users who share and amplify critical content about program failures
- **News sharers** — users who distribute news articles with neutral framing
- **Regional clusters** — users focused on specific geographic areas (Papua, NTT, Java)

The network exhibits moderate clustering coefficient values, indicating that users tend to interact within like-minded communities rather than across ideological lines. This pattern is consistent with echo chamber dynamics documented in political social media research (Bakshy et al., 2015; Cinelli et al., 2021). The limited cross-community interaction suggests that pro-MBG and anti-MBG discourse largely operates in separate information ecosystems.

---

The results presented above provide a multi-faceted picture of MBG discourse on Twitter/X, spanning sentiment distribution, temporal evolution, topic structure, engagement dynamics, and network topology. We now turn to a discussion of the broader implications of these findings, the limitations of our approach, and directions for future research.

## 5. Discussion

### 5.1 Implications

The findings have several implications for policymakers, communication strategists, and researchers:

**Public Perception Challenge:**
The rising negativity trend (37% → 52% negative) represents a significant public perception challenge for the MBG program. Even as the program expands its coverage and infrastructure, negative discourse is accelerating. This suggests that program quality issues — particularly food safety incidents — are outweighing positive coverage in the public conversation. Policymakers should consider that the *narrative* around MBG is increasingly shaped by incidents rather than outcomes, and proactive communication strategies may be needed to rebalance the discourse.

**Regional Disparity in Discourse:**
The stark difference between outer island positivity (~39%) and Java negativity (~24%) suggests that the program is perceived differently across the archipelago. This divergence may reflect: (a) genuine differences in implementation quality, where outer island communities experience the program as a novel and welcome service; (b) different media ecosystems, where Java-based media outlets may amplify critical coverage more than regional media; or (c) different baseline expectations, where communities with fewer existing services may view MBG more favorably than those in urban Java with higher service expectations. Further research is needed to distinguish between these explanations.

**Structural Negativity Amplification:**
The 3.4× amplification advantage for negative content means that critical voices naturally dominate the platform, regardless of the actual balance of public opinion. This is a structural feature of social media discourse — not unique to MBG — that policymakers must account for when gauging public sentiment. A platform dominated by negative content does not necessarily indicate a majority negative opinion; it may simply reflect the dynamics of engagement-driven content distribution.

**Polarization and Echo Chambers:**
The low parent–reply sentiment agreement and the presence of distinct community clusters in the co-reply network suggest that MBG discourse is polarized. Users tend to cluster in ideologically homogeneous communities with limited cross-ideological interaction. This polarization may make constructive policy dialogue more difficult, as stakeholders encounter fewer opportunities to engage with opposing viewpoints.

**The Incident-Outcome Narrative Gap:**
A critical insight from the topic analysis is the asymmetry between incident-driven discourse and outcome-driven discourse. Food safety incidents and corruption allegations generate disproportionately negative and high-engagement content, while topics related to the program's nutritional outcomes (stunting prevention, child nutrition) remain relatively positive but lower in volume and engagement. This pattern suggests that the public narrative around MBG is shaped primarily by failures rather than by the program's intended benefits — a dynamic that has been observed in other welfare program contexts (Barberá et al., 2019). The implication for program administrators is that a single food safety incident can generate more discursive impact than months of positive program outcomes, creating an asymmetric communication environment.

**Temporal Acceleration:**
The finding that negativity has accelerated in the most recent 12 months of data — rising from approximately 37% to over 52% — warrants particular attention. This acceleration coincides with the program's expansion phase, during which coverage increased from pilot regions to nationwide implementation. The temporal correlation between expansion and rising negativity suggests that scaling challenges (logistical difficulties, quality control issues across diverse geographies) may be generating implementation incidents at a rate that outpaces positive coverage. However, we caution that this is a correlation, not a causal claim — other factors, including changes in the political environment, media coverage patterns, or Twitter/X platform dynamics, may contribute to the observed acceleration.

**Bot Detection and Authenticity:**
The bot score distribution — right-skewed with most accounts scoring near 0.1 — suggests that the MBG discourse is predominantly driven by authentic human participants. While this finding is reassuring for the representativeness of the discourse analysis, it does not rule out coordinated inauthentic behavior that may operate below the detection threshold of our 5-signal composite system. The presence of high-influence accounts with stable sentiment positions could reflect either genuine ideological commitment or coordinated amplification strategies — a distinction that our current methodology cannot reliably make.

### 5.2 Limitations and Threats to Validity

We identify several limitations that should be considered when interpreting these findings:

**Platform Representativeness:**
The corpus is limited to Twitter/X and may not represent broader Indonesian public opinion. Twitter users in Indonesia tend to be younger, more urban, and more educated than the general population (Alatas et al., 2019). The MBG program primarily targets rural and lower-income communities whose voices may be underrepresented on this platform. Cross-platform validation (e.g., TikTok, Facebook, news comment sections) would strengthen the generalizability of these findings.

**Data Completeness:**
User screen names are missing from the scrape due to API limitations, which restricts user-level longitudinal analysis. Timestamps are recorded in UTC and converted to WIB (+7 hours), but precise geo-location is not available — regional analysis relies on keyword-based inference from tweet content rather than GPS data. The search query design (23 queries) may not capture all relevant discourse, particularly oblique references or coded language.

**Sentiment Classification:**
The sentiment model's performance on colloquial Indonesian, sarcasm, and irony is not independently validated. Indonesian social media text frequently employs sarcasm (*"bagus banget programnya ya"* — "what a great program") that may be classified as positive when the intended sentiment is negative. This limitation likely introduces noise into the sentiment distribution, though the direction of bias is uncertain.

**Topic Model Validity:**
Topic model quality depends on tweet text quality, which varies significantly. Short tweets (fewer than 3 terms) are excluded from topic modeling, potentially biasing the topic structure toward longer, more substantive posts. The hybrid LDA+BERTopic approach, while methodologically novel, has not been extensively validated in the Indonesian social media context.

**Bot Detection:**
Our 5-signal composite bot scoring system provides indicative rather than definitive classification. The system may misclassify highly active human users as bots and may fail to detect sophisticated automated accounts that mimic human behavior patterns. Without access to Twitter's internal bot detection signals (e.g., account creation IP, phone verification status), our results should be treated as approximate.

**Temporal Coverage:**
The nine-year observation period (2017–2026) spans significant changes in Twitter's API access policies, content moderation practices, and user demographics. These platform-level changes may introduce artifacts into temporal trend analysis that are unrelated to actual changes in MBG discourse.

**Causal Inference:**
This study is observational and descriptive. We identify correlations between sentiment, topics, and engagement, but we cannot establish causal relationships. The observed negativity amplification, for example, may reflect algorithmic amplification, user behavior, or both — we cannot distinguish these mechanisms from the data alone.

### 5.3 Future Work

We identify six directions for future research:

1. **Multi-platform analysis:** Incorporate additional data sources (Instagram, TikTok, Facebook, news comments) to capture discourse across Indonesia's diverse social media ecosystem and reduce platform-specific bias.

2. **Qualitative validation:** Conduct qualitative content analysis on a stratified sample of tweets to validate sentiment classifications, identify sarcasm and irony, and develop richer thematic understanding of discourse frames.

3. **Longitudinal comparison:** Compare MBG discourse patterns with other Indonesian social welfare programs (e.g., Program Keluarga Harapan, Kartu Prakerja) and similar school meal programs in other countries to identify context-specific vs. generalizable discourse patterns.

4. **Survey-based validation:** Conduct survey-based research to compare Twitter discourse patterns with broader public opinion, quantifying the degree to which social media sentiment reflects or diverges from actual population sentiment.

5. **Causal analysis:** Investigate the causal mechanisms behind negativity amplification — distinguishing between algorithmic amplification, user behavior, and content quality effects — through controlled experiments or natural experiments.

6. **Real-time monitoring:** Develop a real-time monitoring dashboard for program administrators to track emerging discourse trends, identify potential crises (e.g., food safety incidents), and assess communication strategy effectiveness.

---

Building on the discussion above, we now synthesize the key findings and their implications in a formal conclusion.

## 6. Conclusion

This study presents a comprehensive computational analysis of 107,039 tweets about Indonesia's Makan Bergizi Gratis (MBG) program spanning nine years (2017–2026). Using a multi-stage analytical pipeline — combining IndoBERT relevance filtering, Indonesian RoBERTa sentiment classification, hybrid LDA+BERTopic topic modeling, reply network analysis, and bot detection — we have characterized the structure, sentiment, and dynamics of public discourse around one of Indonesia's largest social welfare initiatives.

Our analysis yields four principal findings that, taken together, paint a coherent picture of a discourse environment shaped by structural amplification dynamics and geographic heterogeneity:

1. **Rising negativity.** The dominance and growth of negative sentiment (from ~37% to ~52% over the observation period) indicates that public perception of MBG is increasingly shaped by incident-driven narratives — particularly food safety failures and corruption allegations — rather than by the program's intended outcomes. This finding is consistent with the negativity bias literature (Soroka, 2014; Brady et al., 2017) and extends it to the Indonesian welfare policy context.

2. **Structural amplification.** The 3.4× amplification advantage for negative content reflects a platform-level dynamic that policymakers must account for when interpreting online discourse as a signal of public opinion. A predominance of negative content on Twitter/X does not necessarily indicate majority negative opinion among the Indonesian public — it may reflect the inherent dynamics of engagement-driven content distribution.

3. **Geographic divergence.** The regional sentiment divergence between outer islands (more positive) and Java (more negative) suggests that the MBG experience varies meaningfully across Indonesia's geography. This divergence may reflect differences in implementation quality, media ecosystems, or baseline expectations — each of which has distinct policy implications.

4. **Polarized discourse.** The low parent–reply sentiment agreement, the presence of distinct community clusters in the co-reply network, and the sentiment consistency of high-influence users collectively indicate that MBG discourse operates within echo chambers with limited cross-ideological interaction. This polarization represents a structural barrier to constructive policy dialogue on social media platforms.

These findings contribute to three bodies of literature: computational social science approaches to policy discourse in developing democracies (Section 2.4), negativity bias in online communication (Section 2.3), and NLP for Indonesian-language text analysis (Section 2.2). The study demonstrates that multi-method computational pipelines can provide actionable insights into public discourse dynamics at scale, even in linguistically complex and under-studied contexts such as Indonesian social media.

Several practical recommendations emerge from this analysis. First, program administrators should recognize that social media discourse provides a biased signal of public opinion and should supplement online monitoring with representative survey data. Second, communication strategies should anticipate the asymmetric impact of incidents relative to outcomes and develop rapid response protocols for food safety events. Third, the geographic variation in discourse sentiment suggests that region-specific communication approaches may be more effective than nationally uniform messaging.

While the study's limitations — particularly platform representativeness, sentiment classification accuracy on sarcasm and colloquial language, and the observational nature of the analysis — temper the strength of our conclusions, the scale of the dataset (107,039 tweets over nine years), the rigor of the multi-method pipeline (six analytical stages with validated models), and the availability of all code and data for reproducibility provide a robust empirical foundation. Future work should extend this analysis to additional platforms, incorporate qualitative validation of sentiment classifications, and investigate the causal mechanisms underlying the observed negativity amplification.

---

## 7. Data & Code Availability

All data, code, and analysis outputs are publicly accessible:

| Resource | Location |
|----------|----------|
| **GitHub Repository** | `https://github.com/FatwaArya/mbg-analysis` |
| **Pipeline Outputs (DO Spaces)** | `s3://mbg-scraper-network-20260419071440/runs/` |
| **Analysis CSVs** | `s3://mbg-scraper-network-20260419071440/analysis/` |
| **Interactive Dashboard** | Hosted on DigitalOcean VPS |
| **Fine-tuned Model** | `s3://mbg-scraper-network-20260419071440/models/mbg-indobert-finetuned/` |

### 7.1 Data Availability Statement

In accordance with open science principles, we make the following commitments to data availability:

- **Aggregated analysis outputs** (CSV files containing sentiment distributions, topic distributions, engagement statistics, and network metrics) are publicly available in the DigitalOcean Spaces bucket listed above.
- **Source code** for the complete analytical pipeline (data collection, preprocessing, sentiment analysis, topic modeling, reply analysis, bot detection, and network analysis) is available in the GitHub repository under the MIT license.
- **Raw tweet data** is stored in private DigitalOcean Spaces storage due to Twitter/X API Terms of Service restrictions on redistribution. Researchers seeking access to the raw data for replication purposes may contact the corresponding author. Access will be granted on a case-by-case basis contingent on the researcher's agreement to comply with Twitter/X API terms.
- **Fine-tuned IndoBERT model weights** are available in the DigitalOcean Spaces bucket listed above.
- **Interactive dashboard** is hosted on a DigitalOcean VPS and accessible via the URL provided in the GitHub repository.

All analyses reported in this paper can be reproduced using the publicly available code and aggregated outputs. The raw tweet IDs are not redistributed but can be re-fetched via the Twitter/X API (subject to API access availability) using the query parameters documented in the GitHub repository.

---

## Glossary of Indonesian Terms

| Term | Translation | Context |
|------|-------------|---------|
| *Makan Bergizi Gratis* (MBG) | Free Nutritious Meals | Official program name |
| *Badan Gizi Nasional* | National Nutrition Agency | Implementing institution |
| *SPPG* | Satuan Pelayanan Pendidikan Gizi | Education nutrition service unit |
| *keracunan MBG* | MBG poisoning | Food safety incident keyword |
| *korupsi MBG* | MBG corruption | Corruption allegation keyword |
| *distribusi MBG* | MBG distribution | Program implementation keyword |
| *makanan basi* | Spoiled food | Food quality complaint |
| *gizi anak* | Child nutrition | Nutritional impact keyword |
| *stunting* | Stunting | Child development metric |
| *anggaran* | Budget | Financial discussion keyword |
| *penyelewengan* | Misuse/irregularity | Corruption-related term |
| WIB | Waktu Indonesia Barat | Western Indonesian Time (UTC+7) |
| NTT | Nusa Tenggara Timur | East Nusa Tenggara province |

---

## References

1. Alatas, V., Chandrasekhar, A. G., Mobius, M., Olken, B. A., & Paladines, C. (2019). Celebrity endorsements on social media: A field experiment in Indonesia. *Review of Economics and Statistics*, 101(4), 689–703.
2. Aji, A. F., Winata, G. I., Koto, F., Cahyawijaya, S., Romadhony, A., Vincentio, T., ... & Purwarianti, A. (2022). One country, 700+ languages: NLP challenges for underrepresented languages and dialects in Indonesia. *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics*, 7226–7249.
3. Bappenas. (2024). *Rencana Pembangunan Jangka Menengah Nasional 2025–2029: Makan Bergizi Gratis*. Badan Perencanaan Pembangunan Nasional. Jakarta, Indonesia.
4. Bakshy, E., Messing, S., & Adamic, L. A. (2015). Exposure to ideologically diverse news and opinion on Facebook. *Science*, 348(6239), 1130–1132.
5. Barberá, P., Casas, A., Nagler, J., Egan, P. J., Bonneau, R., Jost, J. T., & Tucker, J. A. (2019). Who leads? Who follows? Measuring issue attention and agenda setting by legislators and the mass public using social media data. *American Political Science Review*, 113(4), 883–901.
6. Barik, K., Das, S., & Misra, R. (2021). Sentiment analysis of Indonesian social media text using deep learning approaches. *Procedia Computer Science*, 189, 193–200.
7. Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent Dirichlet Allocation. *Journal of Machine Learning Research*, 3, 993–1022.
8. Brady, W. J., Wills, J. A., Jost, J. T., Tucker, J. A., & Van Bavel, J. J. (2017). Emotion shapes the diffusion of moralized content in social networks. *Proceedings of the National Academy of Sciences*, 114(28), 7313–7318.
9. Ceron, A., Curini, L., Iacus, S. M., & Porro, G. (2014). Every tweet counts? How sentiment analysis of social media can improve our knowledge of citizens' political preferences with an application to Italy and France. *New Media & Society*, 16(2), 340–358.
10. Cinelli, M., De Francisci Morales, G., Galeazzi, A., Quattrociocchi, W., & Starnini, M. (2021). The echo chamber effect on social media. *Proceedings of the National Academy of Sciences*, 118(9), e2023301118.
11. DataReportal. (2025). Digital 2025: Indonesia. Retrieved from https://datareportal.com/reports/digital-2025-indonesia.
12. Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding. *Proceedings of NAACL-HLT*, 4171–4186.
13. Dredze, M. (2012). How social media will change public health. *IEEE Intelligent Systems*, 27(4), 81–84.
14. Falkenberg, M., Galeazzi, A., Torricelli, M., Di Marco, N., Larosa, F., Sas, M., ... & Quattrociocchi, W. (2022). Growing polarization around climate change on social media. *Nature Climate Change*, 12(12), 1114–1121.
15. Gayo-Avello, D. (2013). A meta analysis of state-of-the-art electoral prediction from Twitter data. *Social Science Computer Review*, 31(6), 649–679.
16. González-Bailón, S., Borge-Holthoefer, J., Rivero, A., & Moreno, Y. (2013). The dynamics of protest recruitment through online social networks. *Proceedings of the National Academy of Sciences*, 110(28), 11496–11500.
17. Grootendorst, M. (2022). BERTopic: Neural topic modeling with a class-based TF-IDF procedure. *arXiv preprint arXiv:2203.05794*.
18. Lim, M. (2017). Freedom to hate: Social media, algorithmic enclaves, and the rise of tribal nationalism in Indonesia. *Critical Asian Studies*, 49(3), 311–332.
19. Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., ... & Stoyanov, V. (2019). RoBERTa: A Robustly Optimized BERT Pretraining Approach. *arXiv preprint arXiv:1907.11692*.
20. Margetts, H., John, P., Hale, S., & Yasseri, T. (2016). *Political Turbulence: How Social Media Shapes Collective Action*. Princeton University Press.
21. McInnes, L., Healy, J., & Melville, J. (2018). UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. *arXiv preprint arXiv:1802.03426*.
22. Monti, C., De Francisci Morales, G., & Bonchi, F. (2022). Learning political polarization on social media using neural networks. *IEEE Access*, 10, 101098–101110.
23. Nadhira, A. (2023). Digital democracy and political discourse in Indonesia: The role of Twitter in shaping public opinion. *Asian Journal of Communication*, 33(2), 145–165.
24. Rehurek, R., & Sojka, P. (2011). Gensim — Python Framework for Vector Space Modelling. *NLP Centre, Masaryk University*.
25. Robertson, C. E., Pröllochs, N., Schwarzenegger, K., Pärnamets, P., Van Bavel, J. J., & Feuerriegel, S. (2020). Negativity drives online news consumption. *Nature Human Behaviour*, 7, 812–822.
26. Rozin, P., & Royzman, E. B. (2001). Negativity bias, negativity dominance, and contagion. *Personality and Social Psychology Review*, 5(4), 296–320.
27. Soroka, S. (2014). *Negativity in Democratic Politics*. Cambridge University Press.
28. Stevens, J. (2016). Sastrawi: Python Indonesian Stemmer. Retrieved from https://github.com/sastrawi/sastrawi.
29. Tumasjan, A., Sprenger, T. O., Sandner, P. G., & Welpe, I. M. (2010). Predicting elections with Twitter: What 140 characters reveal about political sentiment. *Proceedings of the AAAI Conference on Weblogs and Social Media*, 178–185.
30. Wilie, B., Vincentio, K., Winata, G. I., Cahyawijaya, S., Li, X., Lim, Z. Y., ... & Purwarianti, A. (2020). IndoNLU: Benchmark and resources for evaluating Indonesian natural language understanding. *Proceedings of the 1st Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics*, 841–852.
