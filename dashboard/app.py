import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from auth import require_auth

st.set_page_config(page_title="MBG Discourse Analysis", page_icon="🍱", layout="wide")
require_auth()

DATA = "/opt/mbg/data"

@st.cache_data
def load():
    return pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date","created_at"])

@st.cache_data
def load_paper_stats():
    return pd.read_csv(f"{DATA}/analysis/paper_statistics_summary.csv").iloc[0]

df = load()
total = len(df)
dist = df["sentiment_normalized"].value_counts()
neg_pct = dist.get("negative",0)/total*100
pos_pct = dist.get("positive",0)/total*100
neu_pct = dist.get("neutral",0)/total*100

st.title("🍱 MBG Program — Public Discourse Analysis")
st.caption("Makan Bergizi Gratis · Twitter/X · 107,375 tweets · 2017–2026 · Research Dashboard")
st.markdown("---")

# ── Top KPIs ──────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Total Tweets", f"{total:,}")
c2.metric("😠 Negative", f"{neg_pct:.1f}%", f"{dist.get('negative',0):,} tweets")
c3.metric("😐 Neutral",  f"{neu_pct:.1f}%", f"{dist.get('neutral',0):,} tweets")
c4.metric("😊 Positive", f"{pos_pct:.1f}%", f"{dist.get('positive',0):,} tweets")
c5.metric("Unique Users", f"{df['user_id'].nunique():,}")
c6.metric("Date Range", f"{df['date'].min().strftime('%b %Y')} – {df['date'].max().strftime('%b %Y')}")

st.markdown("---")

# ── Sentiment trend (monthly) ─────────────────────────────────────────────────
st.markdown("### 📈 Sentiment Trend Over Time")
st.caption("Negativity has been rising sharply since mid-2025 — from 37% to over 52%")

monthly = df.groupby([df["date"].dt.to_period("M"), "sentiment_normalized"]).size().unstack(fill_value=0)
monthly_pct = monthly.div(monthly.sum(axis=1), axis=0) * 100
monthly_pct.index = monthly_pct.index.to_timestamp()

COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}
fig = go.Figure()
for s, color in COLORS.items():
    if s in monthly_pct.columns:
        fig.add_trace(go.Scatter(x=monthly_pct.index, y=monthly_pct[s],
            name=s.capitalize(), line=dict(color=color, width=2.5),
            fill="tozeroy", fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
            hovertemplate="%{y:.1f}%"))
fig.update_layout(hovermode="x unified", yaxis_title="% of monthly tweets",
                  legend_title="Sentiment", height=320, margin=dict(t=10,b=10))
st.plotly_chart(fig, use_container_width=True)

# ── Volume + key insight boxes ────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Monthly Tweet Volume")
    vol = df.groupby(df["date"].dt.to_period("M")).size().reset_index()
    vol.columns = ["month","count"]
    vol["month"] = vol["month"].dt.to_timestamp()
    fig2 = px.bar(vol, x="month", y="count", color_discrete_sequence=["#3498db"])
    fig2.update_layout(height=280, margin=dict(t=10,b=10), yaxis_title="Tweets")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.markdown("### 🔑 Key Research Findings")
    st.error("**Negativity is accelerating** — 37% negative at start → 53% in early 2026. A 16-point shift.")
    st.warning("**Negative tweets spread 3.4× further** — avg 109 retweets vs 32 for positive (p<0.000001).")
    st.success("**Outer islands are more positive** — Papua/NTT/Maluku show 39% positive vs Java's 24%.")
    st.info("**Morning discourse** — Peak posting at 6am WIB. People react to school meal news at day start.")

st.markdown("---")
st.markdown("### 🗺️ Navigate the Dashboard")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.info("**📅 Temporal**\nVolume trends, hourly patterns, negativity acceleration")
c2.info("**📊 Sentiment**\nDistribution, engagement, topic breakdown")
c3.info("**⚡ Spikes**\nAnomaly days, spike events, what drove them")
c4.info("**💬 Engagement**\nVirality, query effectiveness, regional gaps")
c5.info("**🗂 Topics**\nBERTopic clusters, theme evolution")
c6.info("**🔬 Analysis**\nAll research findings, hypotheses confirmed")
