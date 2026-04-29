import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from auth import require_auth

st.set_page_config(page_title="MBG Discourse Analysis", page_icon="🍱", layout="wide")
require_auth()

st.title("🍱 MBG Program — Public Discourse Analysis")
st.caption("Makan Bergizi Gratis · Twitter/X · 2025–2026 · Research Dashboard")
st.markdown("---")

DATA = "/opt/mbg/data"

@st.cache_data
def load_sentiment():
    return pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])

@st.cache_data
def load_summary():
    return pd.read_csv(f"{DATA}/analysis/paper_statistics_summary.csv").iloc[0]

# ── Key metrics ──────────────────────────────────────────────────────────────
try:
    df = load_sentiment()
    dist = df["sentiment_normalized"].value_counts()
    total = len(df)
    date_min = df["date"].min().strftime("%d %b %Y")
    date_max = df["date"].max().strftime("%d %b %Y")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📊 Total Tweets", f"{total:,}")
    c2.metric("😊 Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,} tweets")
    c3.metric("😐 Neutral",  f"{dist.get('neutral',0)/total*100:.1f}%",  f"{dist.get('neutral',0):,} tweets")
    c4.metric("😠 Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,} tweets")
    c5.metric("📅 Period", date_min, f"→ {date_max}")

    st.markdown("---")

    # ── Research context ─────────────────────────────────────────────────────
    st.markdown("### About This Study")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Research Questions**
1. How has public sentiment toward the MBG program evolved over time?
2. What are the dominant themes in public discourse?
3. Which content drives the most engagement and amplification?

**Dataset**
- **Source:** Twitter/X public posts
- **Language:** Indonesian (primary) + English
- **Sentiment Models:** IndoBERT (ID) · RoBERTa (EN)
        """)
    with col2:
        st.markdown("""
**Navigate the Dashboard**

| Page | What you'll find |
|------|-----------------|
| 📊 Sentiment | Trends, distribution, engagement by sentiment |
| 🗂 Topics | BERTopic clusters, theme evolution |
| 💬 Engagement | Virality, hourly patterns, top posts |
| 🔍 Explorer | Filter & browse individual tweets |
| ⚡ Spikes | Anomaly detection, spike-day analysis |
        """)

except Exception as e:
    st.warning(f"Sentiment data not yet available. Run the pipeline first. ({e})")
