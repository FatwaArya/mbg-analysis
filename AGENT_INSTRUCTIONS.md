# MBG Analysis — Agent Instruction Manual

> For any AI agent picking up this codebase. Read this before touching anything.

---

## 1. What This Project Is

Research study on public discourse about Indonesia's **Makan Bergizi Gratis (MBG)** school meal program.
Data source: Twitter/X scraped posts (107k+ tweets, 2017–2026).
Goal: Understand sentiment trends, dominant themes, and engagement patterns.

---

## 2. Infrastructure

| Resource | Details |
|----------|---------|
| VPS | `206.189.157.179` (DigitalOcean, Singapore, 4vCPU 8GB) |
| SSH Key | `~/.ssh/mbg_scraper_do_ed25519` |
| SSH User | `root` |
| VPS Working Dir | `/opt/mbg/` |
| Python Venv (VPS) | `/opt/mbg/venv/bin/activate` |
| Object Storage | DO Spaces `sgp1` — bucket `mbg-scraper-network-20260419071440` |
| Spaces Endpoint | `sgp1.digitaloceanspaces.com` |
| s3cmd config | `~/.s3cfg` (already configured locally and on VPS) |
| Dashboard URL | `http://206.189.157.179:8501` |
| Dashboard Password | `bismillahcair` |
| GitHub Repo | `https://github.com/FatwaArya/mbg-analysis` |

### SSH into VPS
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179
```

### Check VPS is alive
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 -o ConnectTimeout=10 root@206.189.157.179 "echo ok"
```

---

## 3. Directory Structure

```
/opt/mbg/                          ← VPS root
├── venv/                          ← Python virtualenv (all packages installed)
├── data/
│   ├── processed/                 ← Working data files
│   │   ├── tweets_clean.csv           (167k raw tweets)
│   │   ├── tweets_relevant.csv        (post-IndoBERT filter)
│   │   ├── tweets_relevant_tagged.csv (+ language detection)
│   │   ├── tweets_with_sentiment.csv  (+ sentiment labels) ← MAIN FILE
│   │   └── tweets_with_topics.csv     (+ topic clusters)   ← after BERTopic
│   └── output/                    ← Pipeline outputs (also in Spaces)
│       ├── tweets_with_sentiment.csv
│       ├── tweets_with_topics.csv
│       └── topic_info.csv
├── dashboard/                     ← Streamlit app (auto-deployed from GitHub)
├── run_sentiment.py               ← Sentiment inference script
├── run_topics.py                  ← BERTopic script
├── scripts/run_pipeline.sh        ← Orchestrator (sentiment → topics → upload)
├── sentiment.log                  ← Sentiment progress log
└── topics.log                     ← Topic modeling progress log

Local (~/Documents/coding/mbg-analyst/analysis/)
├── data/processed/                ← Download outputs here from Spaces
├── data/analysis/                 ← Generated CSV analysis outputs
├── analysis/                      ← Python analysis scripts
├── dashboard/                     ← Dashboard source (push to deploy)
└── scripts/                       ← Pipeline scripts (mirrored to VPS)
```

---

## 4. Object Storage (DO Spaces)

**Bucket:** `mbg-scraper-network-20260419071440`
**Region:** `sgp1`

### Key paths in Spaces
```
output/tweets_with_sentiment.csv   ← main sentiment output
output/tweets_with_topics.csv      ← main topic output
output/topic_info.csv              ← topic metadata
output/tweets_relevant.csv         ← post-inference corpus
output/tweets_rejected.csv
output/tweets_borderline.csv
processed/tweets_relevant_tagged.csv
models/mbg-indobert-finetuned/     ← fine-tuned IndoBERT model
```

### Download from Spaces (local)
```bash
s3cmd get s3://mbg-scraper-network-20260419071440/output/tweets_with_sentiment.csv data/processed/
s3cmd get s3://mbg-scraper-network-20260419071440/output/tweets_with_topics.csv data/processed/
s3cmd get s3://mbg-scraper-network-20260419071440/output/topic_info.csv data/processed/
```

### Upload to Spaces (from VPS)
```bash
cd /opt/mbg && source venv/bin/activate
venv/bin/s3cmd put data/output/FILE.csv s3://mbg-scraper-network-20260419071440/output/FILE.csv
```

### List Spaces contents
```bash
s3cmd ls s3://mbg-scraper-network-20260419071440/output/
```

---

## 5. Data Files & Columns

### `tweets_with_sentiment.csv` — MAIN WORKING FILE (107,375 rows)
| Column | Description |
|--------|-------------|
| `id` | Tweet ID |
| `text` | Tweet text |
| `date` | Date (parse with `parse_dates=["date"]`) |
| `hour` | Hour in UTC — **add 7 for WIB** |
| `user_id` | User ID (screen_name is missing — known gap) |
| `favorite_count` | Likes |
| `retweet_count` | Retweets |
| `reply_count` | Replies |
| `engagement_total` | likes + RT + replies |
| `query_raw` | Which scrape query captured this tweet |
| `scrape_tab` | `top` or `latest` |
| `lang` | Twitter's language tag (`in` = Indonesian) |
| `detected_lang` | langdetect result (`id`, `en`, etc.) |
| `predicted_label` | IndoBERT relevance (`RELEVANT`) |
| `predicted_confidence` | IndoBERT confidence score |
| `sentiment_label` | Raw model output |
| `sentiment_score` | Model confidence (0–1) |
| `sentiment_normalized` | **Use this** — `positive`, `negative`, `neutral` |

### `tweets_with_topics.csv` — adds topic columns
| Column | Description |
|--------|-------------|
| `topic_id` | BERTopic cluster ID (-1 = outlier) |
| `topic_prob` | Probability of topic assignment |

### `topic_info.csv`
| Column | Description |
|--------|-------------|
| `Topic` | Topic ID |
| `Count` | Number of tweets |
| `Name` | Auto-generated keyword label |

---

## 6. Running the Pipeline

### Check what's running on VPS
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 "screen -ls; ps aux | grep '[r]un_'"
```

### Monitor sentiment progress
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 "grep -oP '\d+/3345' /opt/mbg/sentiment.log | tail -1"
```

### Monitor topic progress
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 "grep -oP 'Batches:\s+\d+%.*?\d+/3345' /opt/mbg/topics.log | tail -1"
```

### Check if outputs exist
```bash
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 "ls -lh /opt/mbg/data/output/"
```

### Restart a crashed job
```bash
# Sentiment
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  "screen -dmS sentiment bash -c 'cd /opt/mbg && source venv/bin/activate && python3 run_sentiment.py >> sentiment.log 2>&1'"

# Topics
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  "screen -dmS topics bash -c 'cd /opt/mbg && source venv/bin/activate && python3 run_topics.py >> topics.log 2>&1'"
```

---

## 7. Running Local Analysis (after downloading data)

```bash
cd /Users/fatwa/Documents/coding/mbg-analyst/analysis
source venv/bin/activate

# Run in this order
python3 analysis/statistical_analysis.py    # needs: tweets_relevant_tagged.csv
python3 analysis/sentiment_analysis.py      # needs: tweets_with_sentiment.csv
python3 analysis/topic_analysis.py          # needs: tweets_with_topics.csv + topic_info.csv
python3 analysis/combined_analysis.py       # needs: tweets_with_topics.csv
python3 analysis/temporal_spike_analysis.py # needs: tweets_with_sentiment.csv
```

Outputs go to `data/analysis/*.csv`

---

## 8. Dashboard

### Run locally
```bash
cd dashboard
../venv/bin/streamlit run app.py --server.port 8501
```

### Deploy to VPS (manual)
```bash
scp -i ~/.ssh/mbg_scraper_do_ed25519 -r dashboard/ root@206.189.157.179:/opt/mbg/
ssh -i ~/.ssh/mbg_scraper_do_ed25519 root@206.189.157.179 \
  "echo 'dashboard_password = \"bismillahcair\"' > /opt/mbg/dashboard/.streamlit/secrets.toml && systemctl restart mbg-dashboard"
```

### Auto-deploy (GitHub Actions)
Any push to `main` that changes `dashboard/` triggers `.github/workflows/deploy.yml` → auto-deploys to VPS.

### Dashboard pages
| Page | File | Data needed |
|------|------|-------------|
| Home | `app.py` | `tweets_with_sentiment.csv` |
| Temporal | `pages/0_temporal.py` | `tweets_with_sentiment.csv` |
| Sentiment | `pages/1_sentiment.py` | `tweets_with_sentiment.csv` |
| Topics | `pages/2_topics.py` | `tweets_with_topics.csv` + `topic_info.csv` |
| Engagement | `pages/3_engagement.py` | `tweets_with_sentiment.csv` |
| Explorer | `pages/4_explorer.py` | `tweets_with_topics.csv` or sentiment |
| Spikes | `pages/5_spikes.py` | `tweets_with_sentiment.csv` |

---

## 9. Key Findings So Far

1. **Negativity is accelerating** — 37% → 53% negative (early → recent period)
2. **Negative tweets spread 3.4× further** — avg 109 RT vs 32 for positive (p<0.000001)
3. **Outer islands more positive** — Papua/NTT/Maluku 39% positive vs Java 24%
4. **Peak posting at 6am WIB** — people react to morning school meal news
5. **Food poisoning query = 70.8% negative** — highest negativity of any topic
6. **Corruption query = 75.3% negative** — second highest
7. **Biggest spike: Feb 13, 2026** (420 tweets, z=2.15) — event TBD
8. **Model confidence** — negative labels most confident (avg 0.89)

---

## 10. Known Data Gaps

| Gap | Impact |
|-----|--------|
| `user_screen_name` 100% missing | Cannot do influencer or bot analysis |
| No reply data yet | Cannot do sentiment contagion or controversy scoring |
| Timestamps in UTC | Always add 7 hours for WIB display |
| Japanese tweet in top 10 | Filter `detected_lang == 'id'` for clean analysis |

---

## 11. GitHub Workflow

```bash
# Standard commit
git add .
git commit -m "description"
git push  # triggers auto-deploy if dashboard/ changed

# Check deploy status
gh run list --limit 3
```

Secrets stored in GitHub (set via `gh secret set`):
- `VPS_HOST` = `206.189.157.179`
- `VPS_USER` = `root`
- `VPS_SSH_KEY` = private key content
- `DASHBOARD_PASSWORD` = `bismillahcair`
