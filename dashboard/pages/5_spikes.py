import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Spikes · MBG", page_icon="⚡", layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

st.title("⚡ Temporal Spike Analysis")
st.caption("When did discourse spike, and what drove it?")
st.markdown("---")

@st.cache_data
def load():
    for path in [f"{DATA}/processed/tweets_with_sentiment.csv",
                 f"{DATA}/processed/tweets_relevant_tagged.csv"]:
        try:
            return pd.read_csv(path, parse_dates=["date"])
        except Exception:
            continue
    return None

df = load()
if df is None:
    st.warning("No data available.")
    st.stop()

# ── Compute spikes ────────────────────────────────────────────────────────────
daily = df.groupby("date").agg(
    tweet_count=("id", "count"),
    total_engagement=("engagement_total", "sum"),
).reset_index()
daily["rolling_mean"] = daily["tweet_count"].rolling(7, min_periods=1).mean()
daily["rolling_std"]  = daily["tweet_count"].rolling(7, min_periods=1).std().fillna(1)
daily["z_score"]      = (daily["tweet_count"] - daily["rolling_mean"]) / daily["rolling_std"]
daily["is_spike"]     = daily["z_score"] > 2.0
spikes = daily[daily["is_spike"]]

# ── Metrics ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric("Spike Days Detected", len(spikes), "z-score > 2")
if len(spikes):
    peak = spikes.loc[spikes["tweet_count"].idxmax()]
    c2.metric("Peak Spike Date", str(peak["date"].date()))
    c3.metric("Peak Volume", f"{int(peak['tweet_count']):,} tweets")

st.markdown("---")

# ── Volume chart with spike markers ──────────────────────────────────────────
st.markdown("#### Daily Volume with Spike Detection")
fig = go.Figure()
fig.add_trace(go.Scatter(x=daily["date"], y=daily["tweet_count"],
                         name="Daily tweets", line=dict(color="#3498db")))
fig.add_trace(go.Scatter(x=daily["date"], y=daily["rolling_mean"],
                         name="7-day avg", line=dict(color="#bdc3c7", dash="dash")))
fig.add_trace(go.Scatter(x=spikes["date"], y=spikes["tweet_count"],
                         mode="markers", name="Spike",
                         marker=dict(color="#e74c3c", size=12, symbol="star")))
fig.update_layout(hovermode="x unified", yaxis_title="Tweets", margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Spike day table ───────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Spike Days")
    st.dataframe(spikes[["date","tweet_count","z_score","total_engagement"]]
                 .sort_values("tweet_count", ascending=False)
                 .assign(z_score=lambda d: d["z_score"].round(2))
                 .reset_index(drop=True),
                 use_container_width=True, hide_index=True)

with col2:
    if "sentiment_normalized" in df.columns and len(spikes):
        st.markdown("#### Sentiment on Spike vs Normal Days")
        df["is_spike_day"] = df["date"].isin(spikes["date"].values)
        spike_sent  = df[df["is_spike_day"]]["sentiment_normalized"].value_counts(normalize=True)*100
        normal_sent = df[~df["is_spike_day"]]["sentiment_normalized"].value_counts(normalize=True)*100
        compare = pd.DataFrame({"Spike days %": spike_sent, "Normal days %": normal_sent}).round(1)
        fig2 = px.bar(compare.reset_index().melt(id_vars="sentiment_normalized"),
                      x="sentiment_normalized", y="value", color="variable",
                      barmode="group",
                      labels={"sentiment_normalized":"Sentiment","value":"%"})
        fig2.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig2, use_container_width=True)

# ── Top posts on spike days ───────────────────────────────────────────────────
if len(spikes):
    st.markdown("---")
    st.markdown("#### Top Posts on Spike Days")
    spike_posts = df[df["date"].isin(spikes["date"].values)].nlargest(20, "engagement_total")
    cols = ["text","date","engagement_total","retweet_count","reply_count"]
    cols = [c for c in cols if c in spike_posts.columns]
    st.dataframe(spike_posts[cols], use_container_width=True, hide_index=True)
