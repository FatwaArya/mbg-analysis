import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Explorer · MBG", page_icon="🔍", layout="wide")
require_auth()

DATA = "/opt/mbg/data"

st.title("🔍 Tweet Explorer")
st.caption("Filter and browse individual tweets in the corpus.")
st.markdown("---")

@st.cache_data
def load():
    for path in [f"{DATA}/processed/tweets_with_topics.csv",
                 f"{DATA}/processed/tweets_with_sentiment.csv"]:
        try:
            df = pd.read_csv(path, parse_dates=["date"])
            return df
        except Exception:
            continue
    return None

df = load()
if df is None:
    st.warning("No data available yet.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    sentiments = df["sentiment_normalized"].unique().tolist() if "sentiment_normalized" in df.columns else []
    sent_filter = st.multiselect("Sentiment", sentiments, default=sentiments)
with col2:
    langs = sorted(df["detected_lang"].unique().tolist())
    lang_filter = st.multiselect("Language", langs, default=["id"])
with col3:
    min_eng = st.number_input("Min engagement", min_value=0, value=0, step=10)
with col4:
    dates = st.date_input("Date range", [df["date"].min(), df["date"].max()])

# ── Apply filters ─────────────────────────────────────────────────────────────
mask = df["detected_lang"].isin(lang_filter) & (df["engagement_total"] >= min_eng)
if sentiments and sent_filter:
    mask &= df["sentiment_normalized"].isin(sent_filter)
if len(dates) == 2:
    mask &= (df["date"] >= pd.Timestamp(dates[0])) & (df["date"] <= pd.Timestamp(dates[1]))

filtered = df[mask].sort_values("engagement_total", ascending=False)

st.markdown(f"**{len(filtered):,}** tweets match your filters")

show_cols = ["text", "sentiment_normalized", "engagement_total",
             "favorite_count", "retweet_count", "reply_count", "date", "detected_lang"]
show_cols = [c for c in show_cols if c in filtered.columns]
st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)
