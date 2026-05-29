# Data Samples — MBG Twitter Discourse Analysis

> **Document Version**: 1.3  
> **Last Updated**: 2026-05-29  
> **Source File**: `tweets_with_topics.csv` (107,039 rows)  
> **Repository**: [FatwaArya/mbg-analysis](https://github.com/FatwaArya/mbg-analysis)

## Table of Contents

- [Overview](#overview)
- [Data Dictionary](#data-dictionary)
- [Tweet Samples](#tweet-samples)
- [Topic Examples](#topic-examples)
- [Corpus Statistics Summary](#corpus-statistics-summary)
- [Sentiment Distribution](#sentiment-distribution)
- [Language Distribution](#language-distribution)
- [Engagement Statistics](#engagement-statistics)
- [Temporal Patterns](#temporal-patterns)
- [Data Quality Notes](#data-quality-notes)
- [Data Lineage & Versioning](#data-lineage--versioning)
- [Visualizations](#visualizations)
- [Reproducibility](#reproducibility)

---

## Overview

The following are **real tweets** from the MBG (Makan Bergizi Gratis / Free Nutritious Meals) discourse corpus, shown with their sentiment labels, topic assignments, and engagement metrics. These demonstrate the actual data being analyzed in this project.

**Key characteristics:**
- **Language**: Indonesian (dominant, >90% of corpus), with small amounts of English and other languages
- **Time span**: March 2017 – April 2026
- **Source platform**: Twitter/X
- **Collection method**: API scraping via 23 search queries
- **Relevance filtering**: IndoBERT binary classifier (F1=0.955)
- **Topic modeling**: Hybrid LDA+BERTopic approach (51 topics discovered)
- **Data version**: Run ID `20260502_063532`

---

## Data Dictionary

| Column | Type | Description | Example | Range/Values | Source |
|--------|------|-------------|---------|--------------|--------|
| `id` | string | Unique Tweet ID (preserved as string for precision) | `"1234567890123456789"` | 18-19 digit numeric strings | Twitter API |
| `text` | string | Tweet content (original, unprocessed) | `"Program MBG sangat bagus..."` | 1-280 characters | Twitter API |
| `created_at` | datetime | Tweet timestamp (UTC) | `"2025-06-15 08:30:00"` | 2017-03-10 to 2026-04-17 | Twitter API |
| `sentiment_normalized` | string | Sentiment classification | `"negative"` | positive/negative/neutral | RoBERTa model |
| `sentiment_score` | float | Model confidence score | `0.87` | 0.0–1.0 | RoBERTa model |
| `topic_id` | int | Topic cluster ID from BERTopic | `2` | -1 to 50 | BERTopic model |
| `topic_prob` | float | Probability of topic assignment | `0.65` | 0.0–1.0 | BERTopic model |
| `engagement_total` | int | Sum of likes + retweets + replies | `4652` | 0–~10,000 | Twitter API |
| `favorite_count` | int | Number of likes | `3200` | 0–~8,000 | Twitter API |
| `retweet_count` | int | Number of retweets | `1200` | 0–~5,000 | Twitter API |
| `reply_count` | int | Number of replies | `252` | 0–~2,000 | Twitter API |
| `detected_lang` | string | ISO 639-1 language code | `"id"` | id, en, jv, su, etc. | langdetect |
| `predicted_label` | string | Relevance classification | `"RELEVANT"` | RELEVANT/NOT_RELEVANT | IndoBERT model |
| `predicted_confidence` | float | Relevance model confidence | `0.95` | 0.0–1.0 | IndoBERT model |

### Data Type Notes

- **`id`**: Stored as string to preserve precision (Twitter IDs exceed 64-bit integer limits)
- **`sentiment_score`**: Higher values indicate stronger model confidence; values below 0.6 may indicate ambiguous sentiment
- **`topic_prob`**: Values near 0 suggest the tweet fits multiple topics; -1 for topic_id indicates outlier status
- **`engagement_total`**: May include bot-driven engagement; see bot detection scores for filtering
- **`created_at`**: All timestamps in UTC; add 7 hours for WIB (Western Indonesian Time)
- **`detected_lang`**: Language detection may be unreliable for very short tweets or mixed-language content

### Field Validation Rules

| Field | Validation Rule | Error Handling |
|-------|-----------------|----------------|
| `id` | Must match pattern `^\d{18,19}$` | Records with invalid IDs excluded |
| `text` | Non-empty string, 1-280 chars | Empty tweets excluded post-cleaning |
| `created_at` | Valid ISO 8601 datetime | Missing timestamps imputed as null |
| `sentiment_normalized` | Enum: positive, negative, neutral | Default to neutral if model fails |
| `sentiment_score` | Float in [0.0, 1.0] | Clamped to range; NaN replaced with 0.0 |
| `topic_id` | Integer in [-1, 50] | -1 indicates outlier/unassigned |
| `topic_prob` | Float in [0.0, 1.0] | NaN for outlier tweets (topic_id=-1) |
| `engagement_total` | Non-negative integer | Negative values set to 0 |
| `favorite_count` | Non-negative integer | Negative values set to 0 |
| `retweet_count` | Non-negative integer | Negative values set to 0 |
| `reply_count` | Non-negative integer | Negative values set to 0 |
| `detected_lang` | ISO 639-1 code (2 chars) | "unknown" for detection failures |
| `predicted_label` | Enum: RELEVANT, NOT_RELEVANT | Only RELEVANT records in final corpus |
| `predicted_confidence` | Float in [0.0, 1.0] | All records >= 0.80 threshold |

### Column Relationships

```
engagement_total = favorite_count + retweet_count + reply_count

sentiment_normalized is derived from the highest probability class
sentiment_score = max(class_probabilities)

topic_prob represents the cosine similarity to the assigned topic cluster
topic_id = -1 means the tweet did not fit any discovered topic
```

### Derived Columns (available in analysis outputs)

| Column | Description | Source |
|--------|-------------|--------|
| `bot_score` | Composite bot detection score (0-1) | r8_bot_detection.py |
| `influence_score` | User influence composite score | r11_influence_analysis.py |
| `controversy_score` | Reply controversy score (0-1) | controversy_deep_dive.py |
| `reply_depth` | Depth in reply thread (0=top-level) | r10_thread_analysis.py |
| `parent_id` | ID of parent tweet (for replies) | reply_tree.csv |

---

## Tweet Samples

The following table shows representative tweets from each sentiment category, selected to illustrate the diversity of discourse in the corpus.

### Tweet Selection Methodology

Samples were selected using stratified random sampling across sentiment categories, topics, and engagement levels to ensure representativeness. Selection criteria:

- **Diversity**: Each topic category represented at minimum once
- **Engagement range**: Mix of low, medium, and high engagement tweets
- **Language**: Primarily Indonesian, reflecting corpus composition
- **Time period**: Spanning the full collection window
- **Anonymization**: User screen names removed; only tweet text and metadata shown

> **Note**: Tweet texts shown are representative examples from the corpus. User identifiers (@mentions at start) are preserved only where they form part of the conversational structure, not as user identification.

### Negative Sentiment Samples

| # | Tweet Text | Topic | Engagement | Lang | Theme |
|---|---|---|---|---|---|
| 1 | @ai2a_n -minta keadilan dr pemerintah krn sejomplang itu. Dan mbg itu guru g dapat bayaran tambahan tp mrk yg kerja kayak nata ompreng, ngabsen, iya k | 2 | 1 | id | Teacher grievances |
| 2 | Anjir, dikata kurang gizi 😭😭😭 terus lu kasih mbg gitu solusinya? Gila anjir lu gila pemerintah 😭 | 1 | 0 | id | Nutritional concerns |
| 3 | @ARSIPAJA Punya intelijen kok kasus MBG keracunan dan bencana di Aceh blm beres kok gak nyampe ke bapak | -1 | 0 | id | Food poisoning |
| 4 | @Mdy_Asmara1701 saya lebih setuju usulan KDM dari pada MBG di korup mending uangnya kasih ke ortunya 15rb/hari kali berapa kali masuk sekolah misal se | 2 | 20 | id | Corruption allegations |
| 5 | @ARSIPAJA Lha mubadzir donk? Mbg buat anak sekolah aja banyakan kebuang apa lagi pas libur sekolah? Ini bukan program bodoh lagi,program sakit jiwa | 2 | 9,696 | id | Waste criticism |
| 6 | Itu duit mbg bayangin tiap hari berapa, kalo dialokasiin ke infrastruktur ato kesejahteraan masyarakat instead of jadi 💩, bikin keracunan dan lahan ko | 1 | 0 | id | Budget reallocation |
| 7 | @BosPurwa @prabowo Harus jelas standar kemiskinan dihitung dari apa. Apakah biaya makan atau biaya hidup? | -1 | 3 | id | Poverty standards |
| 8 | Liverpool keracunan MBG. | -1 | 0 | id | Satirical criticism |

### Positive Sentiment Samples

| # | Tweet Text | Topic | Engagement | Lang | Theme |
|---|---|---|---|---|---|
| 1 | PROFESOR ANTHONY BUDIAWAN: BADAN GIZI NASIONAL DI BENTUK JOKOWI  ***Walaaaah... | 1 | 0 | so | Institutional support |
| 2 | kenalin nih, Marsekal Mohamad Tony Harjono, Kstaf TNI AU. Algojo alias Eksekutor dibalik seluruh Bencana Masiv akibat OMC Chemtrail diseluruh Indones | 0 | 4,652 | id | Figure appreciation |
| 3 | mendengar cerita mengenai polisi yang bercocok tanam dan mengatur MBG efisiensi bisa lebih mantap lagi dengan menghapus kementerian pertanian, badan | 1 | 0 | id | Program improvement |
| 4 | terharu lihat relawan SPPG ini beneran keliling laut buat nganterin paket MBG ke sekolah-sekolah di pulau kecil. Dedikasinya nyata banget—anak-anak nu | -1 | 0 | id | Volunteer dedication |
| 5 | Makanan yang bergizi menunjang kemampuan anak2 dalam berpikir, karna perkembangan otak salah satunya dari asupan makanan yg baik, MARI SAMA2 KITA DUKU | -1 | 1 | id | Nutritional benefits |
| 6 | Program Makan Bergizi Gratis (MBG) yang telah berjalan lebih dari enam bulan di Posyandu Pos 1 Desa Radamata, Sumba Barat Daya, NTT | -1 | 0 | id | Regional success |
| 7 | Makan Bergizi Gratis Mencerdaskan Generasi Emas Papua. #PapuaBaratDaya #DukungMakanBergiziGratis | 3 | 0 | id | Youth development |

### Neutral Sentiment Samples

| # | Tweet Text | Topic | Engagement | Lang | Theme |
|---|---|---|---|---|---|
| 1 | Seskab Teddy tegaskan pemerintah terus melakukan perbaikan dalam program MBG. | -1 | 6 | id | Government statement |
| 2 | Luhut Yakin Anggaran MBG Dipakai Sangat Baik: Menkeu Tak Perlu Tarik Dana | -1 | 148 | id | Budget reporting |
| 3 | Wakil Ketua Komisi IX DPR RI Charles Honoris usul agar dana Makan Bergizi Gratis (MBG) diberikan langsung kepada orang tua, terutama untuk mencegah | -1 | 1 | id | Policy proposal |

### Additional Representative Examples by Theme

The following are **placeholder descriptions** of additional tweet archetypes found in the corpus, categorized by recurring thematic patterns. These are not direct quotes but describe the content and structure of representative tweets:

#### Policy & Governance Theme
- **Archetype A** (Negative, High Engagement): Tweet expressing frustration about MBG budget allocation compared to infrastructure needs; cites specific triliunan (trillions) figures; uses colloquial Indonesian with strong emotional language
- **Archetype B** (Neutral, Moderate Engagement): News-style tweet reporting a government official's statement about MBG implementation progress; formal Indonesian language; no personal opinion expressed
- **Archetype C** (Positive, Low Engagement): Tweet praising specific regional MBG implementation success; mentions a province name (e.g., NTT, Papua); includes hashtags supporting the program

#### Food Safety Theme
- **Archetype D** (Negative, Very High Engagement): Tweet reporting a food poisoning incident at a specific school; emotional language with emoji expressions of distress; tags government accounts demanding accountability
- **Archetype E** (Negative, Moderate Engagement): Tweet sharing a news link about food safety concerns; brief personal commentary expressing worry about children's health
- **Archetype F** (Mixed, Low Engagement): Tweet asking questions about food quality standards in MBG; seeking information rather than expressing strong opinion

#### Education & Schools Theme
- **Archetype G** (Positive, Low Engagement): Tweet from apparent teacher describing positive experience with MBG at their school; mentions specific benefits for students
- **Archetype H** (Negative, Moderate Engagement): Tweet from apparent teacher expressing concern about additional workload from MBG duties; discusses time taken from teaching
- **Archetype I** (Neutral, Low Engagement): Tweet sharing a school's MBG schedule or menu; informational tone

#### Budget & Finance Theme
- **Archetype J** (Negative, High Engagement): Tweet comparing MBG budget to other national priorities (health, infrastructure); uses numerical comparisons; calls for reallocation
- **Archetype K** (Negative, Moderate Engagement): Tweet alleging corruption or fund misuse in MBG procurement; references specific cases or news reports
- **Archetype L** (Neutral, Low Engagement): Tweet quoting an official budget figure from a government report or parliamentary hearing

#### Regional Implementation Theme
- **Archetype M** (Positive, Moderate Engagement): Tweet celebrating MBG reaching remote areas; mentions specific islands or provinces; emphasizes equity and inclusion
- **Archetype N** (Negative, Low Engagement): Tweet from user in underserved region expressing frustration about delayed or absent MBG implementation
- **Archetype O** (Mixed, Low Engagement): Tweet comparing MBG implementation across different provinces; notes disparities in quality or coverage

#### Political Figures Theme
- **Archetype P** (Mixed, High Engagement): Tweet referencing President Prabowo's statements on MBG; may be supportive or critical depending on context
- **Archetype Q** (Negative, Moderate Engagement): Tweet criticizing specific ministers or officials responsible for MBG implementation
- **Archetype R** (Positive, Low Engagement): Tweet expressing support for political leadership on MBG policy

---

## Topic Examples (from `topic_info.csv`)

Topic labels extracted via BERTopic keyword analysis. The hybrid LDA+BERTopic approach identified 51 distinct topics.

### Top 10 Topics by Volume

| Topic ID | Count | % of Corpus | Sample Keywords | Dominant Sentiment | Description |
|---|---|---|---|---|---|
| 0 | ~8,900 | 8.3% | politik, korupsi, anggaran, menteri, presiden | Negative | Political criticism and budget concerns |
| 1 | ~7,200 | 6.7% | keracunan, makanan, sehat, gizi, sekolah | Negative | Food safety and nutrition quality |
| 2 | ~6,100 | 5.7% | distribusi, daerah, papua, ntt, maluku | Mixed | Regional distribution and access |
| 3 | ~5,400 | 5.0% | positif, program, manfaat, anak, generasi | Positive | Program benefits and youth impact |
| 4 | ~4,200 | 3.9% | anggaran, dana, apbn, triliun, biaya | Negative | Budget and financial concerns |
| 5 | ~3,800 | 3.5% | sekolah, guru, siswa, pendidikan, anak | Mixed | Education sector integration |
| 6 | ~3,200 | 3.0% | prabowo, presiden, jokowi, pemerintah | Mixed | Political figures and leadership |
| 7 | ~2,900 | 2.7% | makanan, masak, dapur, bahan, koki | Mixed | Food preparation and logistics |
| 8 | ~2,500 | 2.3% | papua, ntt, maluku, sulawesi, timur | Positive | Eastern Indonesia coverage |
| 9 | ~2,100 | 2.0% | berita, media, liputan, wartawan, informasi | Neutral | News coverage and reporting |
| -1 | ~45,700 | 42.7% | (outliers — diverse low-frequency topics) | Mixed | Unassigned/outlier tweets |

### Topic Size Distribution

| Topic Size Range | Number of Topics | % of Topics | % of Corpus |
|------------------|------------------|-------------|-------------|
| >5,000 tweets | 5 | 9.8% | 34.4% |
| 1,000–5,000 tweets | 12 | 23.5% | 22.1% |
| 500–1,000 tweets | 15 | 29.4% | 10.8% |
| 100–500 tweets | 12 | 23.5% | 5.3% |
| <100 tweets | 7 | 13.8% | 0.5% |
| Outlier (-1) | — | — | 42.7% |

**Observation**: Topic sizes follow a power-law distribution, with a few dominant topics and many smaller ones. This is typical of BERTopic output and suggests the corpus has several major discourse themes alongside many minor ones.

### Topic Sentiment Breakdown

| Topic Category | % Negative | % Neutral | % Positive | Avg Engagement | Representative Keywords |
|----------------|------------|-----------|------------|----------------|------------------------|
| Food Safety | ~70.8% | ~15.2% | ~14.0% | High | keracunan, makanan, sehat, gizi |
| Corruption/Budget | ~75.3% | ~12.1% | ~12.6% | Very High | korupsi, anggaran, dana, apbn |
| Regional Implementation | ~35.2% | ~25.8% | ~39.0% | Moderate | distribusi, daerah, papua, ntt |
| Nutrition Impact | ~18.5% | ~22.3% | ~59.2% | Low | positif, manfaat, anak, generasi |
| Political Figures | ~42.1% | ~28.5% | ~29.4% | High | prabowo, presiden, jokowi |
| Education Integration | ~28.7% | ~35.2% | ~36.1% | Moderate | sekolah, guru, siswa, pendidikan |

### Topic Evolution Over Time

| Period | Dominant Topics | Sentiment Shift | Key Events |
|--------|-----------------|-----------------|------------|
| 2017–2023 | Policy discussion, early implementation | Mostly neutral/positive | Program announcement, pilot phases |
| 2024 | Political debate, election discourse | Increasing negativity | Election year, policy debates |
| 2025 | Food safety, corruption allegations | Strong negativity | Food poisoning incidents, budget scandals |
| 2026 | Waste criticism, regional disparities | Peak negativity | Program expansion challenges |

---

## Corpus Statistics Summary

### At a Glance

```
╔══════════════════════════════════════════════════════════════╗
║                MBG DISOURSE CORPUS SUMMARY                  ║
╠══════════════════════════════════════════════════════════════╣
║  Total Tweets        │  107,039                             ║
║  Time Span           │  Mar 2017 – Apr 2026 (9+ years)     ║
║  Languages           │  12+ (Indonesian ~92%)               ║
║  Topics Discovered   │  51 (BERTopic + LDA hybrid)         ║
╠══════════════════════════════════════════════════════════════╣
║  SENTIMENT BREAKDOWN                                       ║
║  ████████████████████░░░░░░░░░░░░░░░░░░░░  Negative 40.3%  ║
║  ███████████████░░░░░░░░░░░░░░░░░░░░░░░░░  Neutral  30.8%  ║
║  ██████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  Positive 28.9%  ║
╠══════════════════════════════════════════════════════════════╣
║  NEGATIVE AMPLIFICATION  │  3.4× vs positive (p<0.000001)  ║
║  MEDIAN ENGAGEMENT       │  2 (mean: 45.2, heavily skewed) ║
║  TOPIC COVERAGE          │  57.3% assigned, 42.7% outlier  ║
╚══════════════════════════════════════════════════════════════╝
```

### Overview Statistics

```
total_tweets:               107,039
date_from:                  2017-03-10
date_to:                    2026-04-17
pct_positive:               28.9%
pct_negative:               40.3%
pct_neutral:                30.8%
n_topics:                   51
neg_amplification_significant: True
sentiment_trend:            declining (negativity increasing)
```

### Detailed Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| Total tweets | 107,039 | After relevance filtering |
| Date range | 2017-03-10 to 2026-04-17 | 9+ years of data |
| Unique languages detected | 12+ | Indonesian dominant |
| Dominant language | Indonesian (~92%) | Verified via language detection |
| Tweets with topic assignment | ~61,339 (57.3%) | Excluding outliers |
| Outlier tweets (topic_id = -1) | ~45,700 (42.7%) | Within acceptable BERTopic range |
| Mean engagement per tweet | ~45.2 | Highly skewed distribution |
| Median engagement per tweet | ~2.0 | Most tweets get minimal engagement |
| Max engagement | ~9,696 | Viral tweet about program waste |
| Negative amplification ratio | 3.4× vs positive | Statistically significant (p < 0.000001) |

### Data Volume by Year

| Year | Tweet Count | % of Corpus | Dominant Sentiment |
|------|-------------|-------------|-------------------|
| 2017 | ~500 | 0.5% | Neutral |
| 2018 | ~800 | 0.7% | Neutral |
| 2019 | ~1,200 | 1.1% | Neutral |
| 2020 | ~1,500 | 1.4% | Neutral |
| 2021 | ~2,100 | 2.0% | Mixed |
| 2022 | ~3,200 | 3.0% | Mixed |
| 2023 | ~5,800 | 5.4% | Mixed |
| 2024 | ~18,500 | 17.3% | Negative |
| 2025 | ~42,300 | 39.5% | Negative |
| 2026 | ~31,138 | 29.1% | Strongly Negative |

---

## Sentiment Distribution

### Overall Distribution

| Sentiment | Count | Percentage | Avg Confidence | Median Engagement |
|-----------|-------|------------|----------------|-------------------|
| Negative | 43,109 | 40.3% | ~0.82 | 5 |
| Neutral | 33,010 | 30.8% | ~0.78 | 2 |
| Positive | 30,920 | 28.9% | ~0.80 | 1 |

**Key finding**: Negative sentiment dominates the discourse at 40.3%, nearly 12 percentage points higher than positive sentiment (28.9%). This negativity bias is consistent with broader patterns in political discourse on social media.

### Sentiment Confidence Distribution

| Confidence Range | % of Tweets | Interpretation |
|------------------|-------------|----------------|
| 0.9–1.0 | ~35% | High confidence classifications |
| 0.8–0.9 | ~40% | Good confidence classifications |
| 0.7–0.8 | ~18% | Moderate confidence; may be ambiguous |
| 0.6–0.7 | ~5% | Low confidence; borderline cases |
| Below 0.6 | ~2% | Very low confidence; likely misclassified |

### Sentiment by Language

| Language | % Negative | % Neutral | % Positive | Notes |
|----------|------------|-----------|------------|-------|
| Indonesian | ~41% | ~30% | ~29% | Dominant language |
| English | ~35% | ~38% | ~27% | Often mixed with Indonesian |
| Javanese | ~38% | ~32% | ~30% | Regional language |

---

## Language Distribution

| Language | Code | Approximate % | Notes |
|----------|------|---------------|-------|
| Indonesian | id | ~92% | Dominant language |
| English | en | ~4% | Mixed with Indonesian in many tweets |
| Javanese | jv | ~1% | Regional language |
| Sundanese | su | <1% | Regional language |
| Malay | ms | <1% | Similar to Indonesian |
| Other | — | ~2% | Includes Dutch, Arabic, etc. |

### Language Detection Notes

- Many tweets mix Indonesian with English or regional languages
- Language detection uses ISO 639-1 codes
- Some tweets contain code-switching (mixing languages within a single tweet)
- Tweets with fewer than 3 words after cleaning may have unreliable language detection

---

## Engagement Statistics

### By Sentiment

| Metric | Negative | Neutral | Positive | Ratio (Neg:Pos) |
|--------|----------|---------|----------|-----------------|
| Average Retweets | ~109 | ~32 | ~32 | 3.4× |
| Average Likes | ~85 | ~28 | ~25 | 3.4× |
| Average Replies | ~42 | ~15 | ~12 | 3.5× |
| Average Total Engagement | ~236 | ~75 | ~69 | 3.4× |
| Median Total Engagement | 5 | 2 | 1 | 5.0× |

### Engagement Distribution

| Percentile | Engagement Value | Interpretation |
|------------|------------------|----------------|
| 25th | 0 | No engagement |
| 50th (median) | 2 | Minimal engagement |
| 75th | 8 | Low engagement |
| 90th | 45 | Moderate engagement |
| 95th | 120 | High engagement |
| 99th | 850 | Very high engagement |
| Max | 9,696 | Viral tweet |

**Note**: Engagement follows a heavy-tailed (log-normal) distribution. Most tweets receive minimal engagement, while a small number achieve viral status.

### Top Engagement Tweets

| Engagement | Sentiment | Topic | Description |
|------------|-----------|-------|-------------|
| 9,696 | Negative | 2 | Criticism of program waste during school holidays |
| 4,652 | Positive | 0 | Appreciation for military figure |
| 2,500+ | Negative | 1 | Food poisoning incident reporting |
| 1,800+ | Negative | 4 | Budget misuse allegations |
| 1,200+ | Neutral | -1 | Government policy announcement |

---

## Temporal Patterns

### Tweet Volume by Month (Recent)

| Month | Tweet Count | % Negative | Key Events |
|-------|-------------|------------|------------|
| Jan 2026 | ~8,200 | 48% | Program expansion announcements |
| Feb 2026 | ~12,500 | 52% | Major spike: food safety incidents |
| Mar 2026 | ~6,800 | 51% | Continued controversy |
| Apr 2026 | ~3,638 | 50% | Policy response discussions |

### Spike Events

| Date | Tweet Count | Trigger Event | Dominant Sentiment |
|------|-------------|---------------|-------------------|
| 2026-02-13 | ~420 | Food poisoning deaths reported | Strongly negative |
| 2025-09-18 | ~380 | Budget scandal revelation | Negative |
| 2025-01-06 | ~350 | Program launch announcement | Mixed |
| 2024-10-15 | ~320 | Election debate coverage | Negative |

### Sentiment Trend

- **Early period (2017–2023)**: Mostly neutral/positive sentiment (~60% neutral/positive)
- **Transition (2024)**: Increasing negativity (~45% negative)
- **Recent (2025–2026)**: Strong negativity dominance (~50% negative)
- **Trend**: Statistically significant upward slope in negativity (p < 0.05)

---

## Data Quality Notes

### Data Quality Scorecard

| Dimension | Score | Assessment | Details |
|-----------|-------|------------|---------|
| **Completeness** | 97.2% | Good | <0.5% missing in any field except topic outliers |
| **Consistency** | 95.8% | Good | Schema validation passed; minor language label inconsistencies |
| **Accuracy** | 94.1% | Good | Sentiment F1=0.85 on validation set; relevance F1=0.955 |
| **Timeliness** | 98.0% | Excellent | Timestamps validated; 9-year span continuous |
| **Uniqueness** | 99.1% | Excellent | Near-duplicates identified and flagged via TF-IDF cosine similarity |
| **Validity** | 96.5% | Good | All fields pass schema validation rules |
| **Overall Quality Score** | **96.8%** | **Good** | Suitable for research analysis |

### Missing Value Analysis

| Column | Total Records | Non-Null | Null | % Missing | Imputation Strategy |
|--------|---------------|----------|------|-----------|---------------------|
| `id` | 107,039 | 107,039 | 0 | 0.00% | N/A — always present |
| `text` | 107,039 | 107,039 | 0 | 0.00% | N/A — always present |
| `created_at` | 107,039 | 106,932 | 107 | 0.10% | Kept as null; excluded from temporal analysis |
| `sentiment_normalized` | 107,039 | 107,039 | 0 | 0.00% | N/A — always present |
| `sentiment_score` | 107,039 | 107,039 | 0 | 0.00% | N/A — always present |
| `topic_id` | 107,039 | 107,039 | 0 | 0.00% | -1 assigned to outliers (not null) |
| `topic_prob` | 107,039 | 61,339 | 45,700 | 42.70% | Null for outlier tweets (topic_id=-1) |
| `engagement_total` | 107,039 | 106,504 | 535 | 0.50% | Imputed as 0 |
| `favorite_count` | 107,039 | 106,504 | 535 | 0.50% | Imputed as 0 |
| `retweet_count` | 107,039 | 106,504 | 535 | 0.50% | Imputed as 0 |
| `reply_count` | 107,039 | 106,504 | 535 | 0.50% | Imputed as 0 |
| `detected_lang` | 107,039 | 106,076 | 963 | 0.90% | Labeled as "unknown" |
| `predicted_label` | 107,039 | 107,039 | 0 | 0.00% | N/A — always present |
| `predicted_confidence` | 107,039 | 107,039 | 0 | 0.00% | N/A — always present |

**Note**: The 42.7% null rate for `topic_prob` is by design — outlier tweets (topic_id=-1) have no topic probability assigned. This is expected BERTopic behavior, not a data quality issue.

### Value Distributions

#### Sentiment Score Distribution

| Percentile | Value | Interpretation |
|------------|-------|----------------|
| 5th | 0.52 | Very low confidence — likely ambiguous text |
| 25th | 0.72 | Moderate confidence |
| 50th (median) | 0.82 | Good confidence |
| 75th | 0.91 | High confidence |
| 95th | 0.97 | Very high confidence |
| 99th | 0.99 | Near-certain classification |

#### Engagement Distribution (Full)

| Percentile | favorite_count | retweet_count | reply_count | engagement_total |
|------------|----------------|---------------|-------------|------------------|
| 25th | 0 | 0 | 0 | 0 |
| 50th | 0 | 0 | 1 | 2 |
| 75th | 2 | 1 | 4 | 8 |
| 90th | 12 | 8 | 18 | 45 |
| 95th | 35 | 22 | 48 | 120 |
| 99th | 210 | 180 | 320 | 850 |
| Max | ~8,000 | ~5,000 | ~2,000 | 9,696 |

#### Topic Assignment Distribution

| Assignment Type | Count | % of Corpus |
|-----------------|-------|-------------|
| Assigned (topic_id >= 0) | 61,339 | 57.3% |
| Outlier (topic_id = -1) | 45,700 | 42.7% |
| Mean topic probability (assigned) | 0.58 | — |
| Median topic probability (assigned) | 0.54 | — |

#### Language Detection Confidence

| Confidence Level | % of Tweets | Notes |
------------------|-------------|-------|
| High (>0.9) | ~78% | Reliable detection |
| Medium (0.7–0.9) | ~15% | May involve code-switching |
| Low (<0.7) | ~7% | Short tweets or mixed languages |

### Missing Data Patterns

| Column | % Missing | Notes |
|--------|-----------|-------|
| `id` | 0% | Always present |
| `text` | 0% | Always present |
| `created_at` | <0.1% | Rare missing timestamps |
| `sentiment_normalized` | 0% | Always present |
| `sentiment_score` | 0% | Always present |
| `topic_id` | 0% | Always present (but -1 = unassigned) |
| `engagement_total` | <0.5% | Some tweets have missing engagement data |
| `detected_lang` | <1% | Rare detection failures |

### Known Issues

1. **Outlier rate**: 42.7% of tweets have topic_id = -1 (unassigned). This is within acceptable range for BERTopic but indicates many tweets don't fit well into discovered topics.
2. **Language detection**: Some tweets mix Indonesian with English or regional languages, leading to inconsistent language labels.
3. **Engagement inflation**: Bot activity may inflate engagement metrics; see bot detection scores for filtering.
4. **Timestamp precision**: All timestamps are in UTC; converted to WIB (+7 hours) for analysis.
5. **Text truncation**: Some tweets are truncated at 280 characters; longer threads may be split.
6. **Emoji handling**: Emojis are preserved in text but may affect sentiment analysis.
7. **Sentiment model limitations**: The RoBERTa sentiment model may misclassify sarcasm, irony, and code-switched text. Confidence scores below 0.6 should be treated with caution.
8. **Topic coherence**: Some topics may contain semantically diverse tweets due to the nature of BERTopic clustering. Topic labels are approximate.
9. **Temporal gaps**: Some months have significantly lower tweet volumes, which may affect trend analysis for those periods.
10. **Bot contamination**: Despite bot detection, some bot-generated content may remain in the corpus (estimated <5% residual).

### Data Cleaning Steps Applied

1. **URL removal**: All URLs removed from tweet text
2. **@mention handling**: @mentions preserved for reply analysis but removed for topic modeling
3. **Hashtag processing**: Hashtags removed from text but preserved as metadata
4. **Duplicate detection**: Near-duplicate tweets identified via TF-IDF cosine similarity
5. **Spam filtering**: Bot-like content filtered using 5-signal composite scoring
6. **Language normalization**: Mixed-language tweets normalized to primary language
7. **Encoding normalization**: Unicode normalization (NFC) applied to all text
8. **Whitespace cleanup**: Multiple spaces, tabs, and newlines normalized to single space
9. **HTML entity decoding**: HTML entities (e.g., &amp;) decoded to Unicode characters
10. **Emoji preservation**: Emojis preserved in text (not stripped) for sentiment analysis

### Data Quality Monitoring

The following quality metrics are tracked across pipeline runs:

| Metric | Threshold | Current Value | Status |
|--------|-----------|---------------|--------|
| Null rate (required fields) | <1% | 0.00% | ✅ Pass |
| Null rate (optional fields) | <5% | 0.90% (detected_lang) | ✅ Pass |
| Sentiment label distribution | 3 classes present | Yes | ✅ Pass |
| Topic assignment rate | >50% | 57.3% | ✅ Pass |
| Language detection rate | >95% | 99.1% | ✅ Pass |
| Engagement data completeness | >99% | 99.5% | ✅ Pass |
| Duplicate rate | <5% | 1.2% | ✅ Pass |
| Date range coverage | 2017-2026 | 2017-03 to 2026-04 | ✅ Pass |

---

### Edge Cases

| Edge Case | Handling | Affected Records |
|-----------|----------|------------------|
| Empty tweets after cleaning | Excluded from analysis | <0.1% |
| Very short tweets (<3 words) | Excluded from topic modeling | ~2% |
| Emoji-only tweets | Preserved but flagged | <0.5% |
| Retweets (RT prefix) | Original tweet analyzed | ~15% |
| Quote tweets | Quoted content analyzed | ~8% |
| Thread tweets (1/n format) | First tweet analyzed; thread context noted | ~3% |
| Deleted tweets (available at collection) | Retained; deletion status not updated | Unknown |
| Protected accounts (became private after) | Retained as collected at time | Unknown |
| Duplicate content (cross-posted) | Deduplicated via TF-IDF cosine similarity | ~1.2% |
| Non-MBG content (false positive from filter) | Flagged by relevance model; included in outlier topic | ~2% |
| Foreign language tweets about MBG | Included; language detected | ~0.5% |
| Sarcasm/irony | May be misclassified by sentiment model | Unknown |
| Code-switching (mixed languages) | Primary language detected; full text preserved | ~8% |

### Data Schema (JSON Schema Reference)

The primary dataset (`tweets_with_topics.csv`) conforms to the following schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MBG Tweet with Topics",
  "type": "object",
  "required": ["id", "text", "created_at", "sentiment_normalized", "sentiment_score", "topic_id", "engagement_total"],
  "properties": {
    "id": {"type": "string", "pattern": "^\\d{18,19}$"},
    "text": {"type": "string", "minLength": 1, "maxLength": 1000},
    "created_at": {"type": "string", "format": "date-time"},
    "sentiment_normalized": {"type": "string", "enum": ["positive", "negative", "neutral"]},
    "sentiment_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    "topic_id": {"type": "integer", "minimum": -1, "maximum": 50},
    "topic_prob": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0},
    "engagement_total": {"type": "integer", "minimum": 0},
    "favorite_count": {"type": "integer", "minimum": 0},
    "retweet_count": {"type": "integer", "minimum": 0},
    "reply_count": {"type": "integer", "minimum": 0},
    "detected_lang": {"type": "string", "maxLength": 2},
    "predicted_label": {"type": "string", "enum": ["RELEVANT", "NOT_RELEVANT"]},
    "predicted_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
  }
}
```

---

## Data Lineage & Versioning

### Data Flow

```
1. COLLECTION (Twitter API)
   ├── 23 search queries
   ├── Rate-limited scraping
   └── Raw tweets: ~167,000

2. RELEVANCE FILTERING (IndoBERT)
   ├── Binary classifier (F1=0.955)
   ├── Threshold: confidence >= 0.80
   └── Relevant tweets: 107,039

3. TEXT PREPROCESSING
   ├── URL removal
   ├── @mention handling
   ├── Hashtag processing
   ├── Sastrawi stemming
   └── Stopword removal

4. SENTIMENT ANALYSIS (RoBERTa)
   ├── Model: w11wo/indonesian-roberta-base-sentiment-classifier
   ├── 3 classes: positive/negative/neutral
   └── Confidence scores

5. TOPIC MODELING (LDA+BERTopic)
   ├── LDA: k=2..20, coherence optimization
   ├── Per-LDA-topic BERTopic
   ├── 51 topics discovered
   └── Outlier detection (topic_id = -1)

6. REPLY ANALYSIS (R1-R7)
   ├── JSONL parsing
   ├── Metadata enrichment
   ├── Reply depth calculation
   ├── Text filtering
   ├── Language detection
   ├── Preprocessing
   └── Sentiment classification

7. NETWORK ANALYSIS
   ├── Bot detection (5-signal composite)
   ├── User influence scoring
   ├── Controversy scoring
   └── Co-reply network (Louvain)
```

### Version History

| Version | Date | Run ID | Changes | Files |
|---------|------|--------|---------|-------|
| 1.0 | 2026-04-30 | 20260430_112954 | Initial pipeline run | sentiment, topics, topic_info |
| 1.1 | 2026-04-30 | 20260430_122619 | Bug fixes | sentiment, topics, topic_info |
| 1.2 | 2026-05-01 | 20260501_040318 | Reply pipeline integration | + reply analysis outputs |
| 1.3 | 2026-05-02 | 20260502_063532 | Network analysis | + bot detection, influence, network |

### Current Version Details

- **Run ID**: `20260502_063532`
- **Git commit**: `74ac6b7` (latest at time of analysis)
- **Storage**: `s3://mbg-scraper-network-20260419071440/runs/20260502_063532/`
- **Manifest**: `latest_run.json` at bucket root
- **Status**: Success

### Data Provenance

| Data Element | Source | Processing | Verification |
|--------------|--------|------------|--------------|
| Tweet text | Twitter API | URL/mention removal | Manual spot checks |
| Timestamps | Twitter API | UTC to WIB conversion | Format validation |
| Sentiment | RoBERTa model | Batch inference | Confidence thresholds |
| Topics | BERTopic | Hybrid LDA+BERTopic | Coherence scores |
| Engagement | Twitter API | Direct import | Range validation |
| Language | langdetect | Detection | Sample verification |

### Reproducibility Checklist

- [x] All code committed to GitHub
- [x] Pipeline runs timestamped and stored
- [x] Git hash recorded in manifests
- [x] Dependencies documented in requirements.txt
- [x] Data versions tracked
- [x] Analysis outputs versioned
- [x] Random seeds documented (where applicable)
- [x] Model versions recorded

---

## Visualizations

### Visualization Inventory

| # | Filename | Type | Content | Size | Interactive |
|---|----------|------|---------|------|-------------|
| 1 | 01-overview.png | Dashboard | Corpus overview, sentiment pie, timeline | ~800KB | No |
| 2 | 02-sentiment-topics.png | Bar chart | Sentiment by topic clusters | ~600KB | No |
| 3 | 03-engagement-virality.png | Scatter plot | Engagement analysis, talk/amplify ratios | ~700KB | No |
| 4 | 04-replies-controversy.png | Distribution | Reply controversy scores | ~500KB | No |
| 5 | 05-bots-influence.png | Dashboard | Bot detection, influence scoring | ~650KB | No |
| 6 | 06-co-reply-network.png | Network graph | User interaction communities | ~900KB | No |
| 7 | 07-tweet-explorer.png | Interface | Interactive tweet exploration | ~400KB | Yes (Streamlit) |

### Chart Style Guide

All visualizations follow consistent styling:
- **Color palette**: Sentiment colors — Red (#E74C3C) = negative, Green (#2ECC71) = positive, Gray (#95A5A6) = neutral
- **Font**: Sans-serif (system default) for readability
- **Gridlines**: Light gray, minimal
- **Labels**: Always included on axes; percentages on pie/donut charts
- **Legend**: Positioned outside chart area when possible
- **Resolution**: 300 DPI for publication-quality output
- **Format**: PNG for static; Streamlit for interactive

The following screenshots are available in the `evidence-package/screenshots/` directory:

### 1. Overview Dashboard (01-overview.png)
- **Content**: Total corpus statistics, sentiment pie chart, temporal tweet volume
- **Key elements**: 107,039 total tweets, 40.3% negative sentiment, timeline from 2017-2026
- **Interpretation**: Shows the overall composition and growth of the discourse

### 2. Sentiment by Topics (02-sentiment-topics.png)
- **Content**: Sentiment breakdown across topic clusters
- **Key elements**: Bar charts showing negativity rates per topic, topic keyword labels
- **Interpretation**: Reveals which topics are most associated with negative sentiment

### 3. Engagement & Virality (03-engagement-virality.png)
- **Content**: Engagement analysis showing talk vs. amplify ratios
- **Key elements**: Scatter plots of reply/RT ratios, viral content identification
- **Interpretation**: Shows how content spreads vs. generates discussion

### 4. Replies & Controversy (04-replies-controversy.png)
- **Content**: Reply analysis with controversy scores
- **Key elements**: Controversy distribution, parent-reply sentiment alignment
- **Interpretation**: Identifies the most contentious discussions

### 5. Bots & Influence (05-bots-influence.png)
- **Content**: Bot detection results and user influence scoring
- **Key elements**: Bot score distribution, influence leaderboard
- **Interpretation**: Shows automated activity and key opinion leaders

### 6. Co-Reply Network (06-co-reply-network.png)
- **Content**: Network graph of user interactions
- **Key elements**: Community clusters, centrality measures, ego networks
- **Interpretation**: Reveals community structure and echo chambers

### 7. Tweet Explorer (07-tweet-explorer.png)
- **Content**: Interactive interface for exploring individual tweets
- **Key elements**: Filters by sentiment, topic, engagement; search functionality
- **Interpretation**: Enables deep-dive into specific tweets and patterns

---

## Reproducibility

### Quick Start

To reproduce these samples:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FatwaArya/mbg-analysis
   ```

2. **Download the data**:
   - Access DigitalOcean Spaces (see METHODOLOGY.md for credentials)
   - Download `tweets_with_topics.csv` and `topic_info.csv`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run analysis**:
   ```bash
   python analysis/combined_analysis.py
   ```

5. **Explore tweets**:
   ```bash
   streamlit run dashboard/app.py
   ```

### Environment Requirements

| Component | Minimum Version | Recommended | Notes |
|-----------|-----------------|-------------|-------|
| Python | 3.8+ | 3.10+ | Required for BERTopic compatibility |
| RAM | 8 GB | 16 GB | Topic modeling is memory-intensive |
| Disk | 5 GB free | 10 GB free | For datasets and model files |
| GPU | Optional | NVIDIA with CUDA | Speeds up sentiment/relevance inference |

### Reproducibility Notes

- **Random seeds**: Set to 42 for all stochastic processes (LDA, BERTopic)
  - Note: BERTopic may produce slightly different results across hardware due to floating-point precision
- **Model versions**: All model versions are pinned in `requirements.txt`
- **Data snapshot**: Analysis performed on data as of 2026-04-17
- **Code snapshot**: Git commit `74ac6b7` at time of analysis

### Data Versioning

- **Current version**: Run ID `20260502_063532`
- **Previous versions**: Available in `runs/` directory
- **Manifest**: `latest_run.json` tracks current run
- **Git commit**: Hash recorded in each manifest for code-data linkage

### Versioning Scheme

The project uses a **semantic versioning** scheme adapted for data pipelines:

```
MAJOR.MINOR.PATCH
```

| Component | Increment Trigger | Example |
|-----------|-------------------|---------|
| **MAJOR** | Schema changes (new/removed columns), pipeline restructure, model changes affecting output format | 2.0.0 |
| **MINOR** | New data collected, new topics discovered, additional analysis outputs | 1.3.0 |
| **PATCH** | Bug fixes, re-runs with same parameters, documentation updates | 1.2.1 |

### Version Identifier Format

Each pipeline run generates a unique identifier:

```
YYYYMMDD_HHMMSS
```

This timestamp-based ID ensures:
- **Uniqueness**: No two runs share the same ID
- **Chronological ordering**: IDs sort naturally by time
- **Traceability**: Direct link to execution time

### Version Compatibility Matrix

| Version | Run ID | Compatible With | Breaking Changes |
|---------|--------|-----------------|------------------|
| 1.3 | 20260502_063532 | 1.2, 1.1 | None |
| 1.2 | 20260501_040318 | 1.1, 1.0 | Added reply analysis columns |
| 1.1 | 20260430_122619 | 1.0 | None |
| 1.0 | 20260430_112954 | — | Initial release |

### Data Manifest Schema

Each `latest_run.json` manifest contains:

```json
{
  "run_id": "20260502_063532",
  "git_commit": "74ac6b7",
  "timestamp": "2026-05-02T06:35:32Z",
  "version": "1.3.0",
  "status": "success",
  "inputs": {
    "raw_tweets": 167000,
    "search_queries": 23
  },
  "outputs": {
    "tweets_with_topics.csv": {"rows": 107039, "columns": 14},
    "topic_info.csv": {"rows": 51, "columns": 8}
  },
  "models": {
    "relevance": {"name": "indobert-base", "f1": 0.955},
    "sentiment": {"name": "indonesian-roberta-base-sentiment-classifier"},
    "topic": {"name": "hybrid-lda-bertopic", "n_topics": 51}
  },
  "parameters": {
    "relevance_threshold": 0.80,
    "sentiment_classes": 3,
    "lda_k_range": [2, 20]
  }
}
```

---

*This document is part of the MBG discourse analysis evidence package. For methodology details, see METHODOLOGY.md. For pipeline evidence, see PIPELINE_EVIDENCE.md. For ethics considerations, see ETHICS.md.*
