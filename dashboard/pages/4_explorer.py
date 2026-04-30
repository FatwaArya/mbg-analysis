import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Explorer · MBG", page_icon="🔍", layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("🔍 Tweet Explorer")
st.caption("Filter, search, and browse all 107,375 tweets in the corpus")
st.markdown("---")

@st.cache_data
def load():
    for p in [f"{DATA}/processed/tweets_with_topics.csv",
              f"{DATA}/processed/tweets_with_sentiment.csv"]:
        try:
            return pd.read_csv(p, parse_dates=["date"])
        except Exception:
            continue
    return None

df = load()
if df is None:
    st.warning("No data available.")
    st.stop()

# ── Filters ───────────────────────────────────────────────────────────────────
col1,col2,col3,col4,col5 = st.columns(5)
with col1:
    sent_opts = sorted(df["sentiment_normalized"].unique().tolist())
    sent_filter = st.multiselect("Sentiment", sent_opts, default=sent_opts)
with col2:
    lang_opts = sorted(df["detected_lang"].unique().tolist())
    lang_filter = st.multiselect("Language", lang_opts, default=["id"])
with col3:
    min_eng = st.number_input("Min engagement", min_value=0, value=0, step=100)
with col4:
    topic_opts = ["All"]
    if "topic_id" in df.columns:
        try:
            ti = pd.read_csv(f"{DATA}/processed/topic_info.csv")
            valid_t = ti[ti["Topic"] != -1]
            topic_opts += [f"{r['Topic']} — {r['Name'][:35]}" for _, r in valid_t.nlargest(20,"Count").iterrows()]
        except Exception:
            pass
    topic_filter = st.selectbox("Topic", topic_opts)
with col5:
    keyword = st.text_input("Keyword search", placeholder="e.g. keracunan")

dates = st.date_input("Date range", [df["date"].min(), df["date"].max()])

# ── Apply ─────────────────────────────────────────────────────────────────────
mask = (df["sentiment_normalized"].isin(sent_filter) &
        df["detected_lang"].isin(lang_filter) &
        (df["engagement_total"] >= min_eng))
if topic_filter != "All" and "topic_id" in df.columns:
    tid = int(topic_filter.split(" — ")[0])
    mask &= df["topic_id"] == tid
if keyword:
    mask &= df["text"].str.contains(keyword, case=False, na=False)
if len(dates) == 2:
    mask &= (df["date"] >= pd.Timestamp(dates[0])) & (df["date"] <= pd.Timestamp(dates[1]))

filtered = df[mask].sort_values("engagement_total", ascending=False)

# ── Summary of filtered set ───────────────────────────────────────────────────
st.markdown(f"**{len(filtered):,} tweets** match your filters")
if len(filtered):
    c1,c2,c3,c4 = st.columns(4)
    dist = filtered["sentiment_normalized"].value_counts(normalize=True)*100
    c1.metric("😠 Negative", f"{dist.get('negative',0):.1f}%")
    c2.metric("😐 Neutral",  f"{dist.get('neutral',0):.1f}%")
    c3.metric("😊 Positive", f"{dist.get('positive',0):.1f}%")
    c4.metric("Avg Engagement", f"{filtered['engagement_total'].mean():.0f}")

    # Mini sentiment chart for filtered set
    if len(filtered) > 10:
        daily_f = filtered.groupby(["date","sentiment_normalized"]).size().unstack(fill_value=0)
        daily_pct = daily_f.div(daily_f.sum(axis=1),axis=0)*100
        fig = px.area(daily_pct.reset_index().melt(id_vars="date"),
                      x="date", y="value", color="sentiment_normalized",
                      color_discrete_map=COLORS,
                      labels={"value":"%","sentiment_normalized":""},
                      height=200)
        fig.update_layout(margin=dict(t=5,b=5), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

show_cols = ["text","sentiment_normalized","sentiment_score","engagement_total",
             "favorite_count","retweet_count","reply_count","date","detected_lang","query_raw"]
show_cols = [c for c in show_cols if c in filtered.columns]
st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)
