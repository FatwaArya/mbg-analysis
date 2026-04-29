# MBG Analysis Plan — Post Topic Modeling

> **Status:** Waiting for BERTopic to finish (~02:45 WIB)
> **Data:** 107,375 tweets · sentiment labeled · topics pending

---

## Step 1 — Download & Verify Topic Output

```bash
# Check files exist on VPS
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  "ls -lh /opt/mbg/data/output/"

# Download to local
scp -i ~/.ssh/mbg_scraper_do_ed25519 \
  root@206.189.157.179:/opt/mbg/data/output/tweets_with_topics.csv \
  root@206.189.157.179:/opt/mbg/data/output/topic_info.csv \
  data/processed/
```

**Acceptance criteria before proceeding:**
- `topic_info.csv` has 10–50 topics (if <5 → min_topic_size too large; if >100 → too fragmented)
- Outlier tweets (topic_id = -1) < 30% of corpus
- Topic names are readable Indonesian keywords

---

## Step 2 — Run Local Analysis Scripts (in order)

```bash
cd /Users/fatwa/Documents/coding/mbg-analyst/analysis
source venv/bin/activate

python3 analysis/statistical_analysis.py    # baseline stats
python3 analysis/sentiment_analysis.py      # sentiment breakdowns
python3 analysis/topic_analysis.py          # topic overview
python3 analysis/combined_analysis.py       # cross-analysis
python3 analysis/temporal_spike_analysis.py # spike detection
```

All outputs → `data/analysis/*.csv`

---

## Step 3 — Core Analysis: Topic × Sentiment × Time

This is the main research contribution. Three questions:

### 3a. Which topics are most negative?
- Cross `topic_id` × `sentiment_normalized`
- Rank topics by negativity %
- Expected: food poisoning, corruption, distribution failure = most negative

### 3b. How did topic dominance change over time?
- Monthly share of each top-10 topic
- Look for: which topics grew, which faded
- Key hypothesis: "food safety" topic grew after Aug–Sep 2025 incidents

### 3c. Which topics drive amplification?
- Average retweet count per topic
- Separate: topics that get debated (high reply/RT ratio) vs spread (high RT, low reply)

**Script to create:** `analysis/topic_sentiment_combined.py`

---

## Step 4 — Narrative Framing Analysis

Use the `reason` column from `tweets_final_annotated.csv` (Claude's annotation reasons).

- Cluster the reasons into framing categories:
  - **Operational criticism** (food quality, distribution, logistics)
  - **Political criticism** (corruption, gimmick, pencitraan)
  - **Positive support** (program expansion, nutrition impact)
  - **Neutral reporting** (news, statistics)
- Cross framing category with sentiment and engagement

**Script to create:** `analysis/framing_analysis.py`

---

## Step 5 — Temporal Deep Dive

Build on the spike analysis already in the dashboard:

| Date | Event to investigate |
|------|---------------------|
| Feb 13, 2026 | Biggest spike (420 tweets) — what happened? |
| Sep 18, 2025 | Second spike — food poisoning deaths reported? |
| Jan 6, 2025 | Third spike — program launch announcement? |

- Pull top 20 tweets from each spike day
- Read them manually to identify the triggering event
- Annotate spike days with event labels for the paper

---

## Step 6 — Update Dashboard with Topic Pages

Once `tweets_with_topics.csv` is downloaded:

1. Upload to VPS: `scp ... root@206.189.157.179:/opt/mbg/data/processed/`
2. The existing `2_topics.py` page will auto-populate
3. Add topic filter to `4_explorer.py`
4. Add topic breakdown to `1_sentiment.py` (sentiment per topic bar chart)

---

## Step 7 — Paper Statistics Summary

Pull from `data/analysis/paper_statistics_summary.csv` after running all scripts:

| Statistic | Where it comes from |
|-----------|-------------------|
| Total tweets in corpus | `combined_analysis.py` |
| Date range | `combined_analysis.py` |
| % positive / negative / neutral | `sentiment_analysis.py` |
| Number of topics discovered | `topic_analysis.py` |
| Top 3 topics by volume | `topic_analysis.py` |
| Negativity trend slope + p-value | `temporal_spike_analysis.py` |
| Negative amplification p-value | `combined_analysis.py` |
| Regional sentiment gap | `engagement analysis` |

---

## Priority Order

```
HIGH (do first, core findings)
  ├── Step 1: Download topic output
  ├── Step 2: Run all analysis scripts
  └── Step 3: Topic × Sentiment × Time

MEDIUM (strengthens the paper)
  ├── Step 4: Framing analysis
  └── Step 5: Spike event identification

LOW (polish)
  ├── Step 6: Dashboard topic pages
  └── Step 7: Paper statistics table
```

---

## Expected Key Findings (Hypotheses to Test)

1. **Food safety topics** will be the most negative AND most amplified
2. **Political/corruption topics** will have highest engagement per tweet
3. **Outer island topics** will cluster around "distribution" and "access" themes
4. **Negativity surge** in Feb–Mar 2026 will be traceable to specific topic(s) growing
5. **Positive topics** (nutrition outcomes, expansion) will have low amplification — good news doesn't spread

If hypotheses 1–3 are confirmed, that's a complete, publishable discourse analysis.
