import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from auth import require_auth
from spaces_loader import load_with_fallback, get_connection_status, format_run_info

st.set_page_config(page_title="MBG Discourse Analysis", page_icon=None, layout="wide")
require_auth()

DATA = "/opt/mbg/data"

@st.cache_data
def load():
    df, source, run_info = load_with_fallback("tweets_with_sentiment")
    if df is None:
        st.error("Failed to load data from Spaces or local files")
        st.stop()
    
    st.session_state["data_source"] = source
    st.session_state["run_info"] = run_info
    
    df["date"] = pd.to_datetime(df["date"])
    df["created_at"] = pd.to_datetime(df["created_at"])
    return df[df["date"] >= "2025-01-01"]

@st.cache_data
def load_paper_stats():
    return pd.read_csv(f"{DATA}/analysis/paper_statistics_summary.csv").iloc[0]

df = load()
total = len(df)
dist = df["sentiment_normalized"].value_counts()
neg_pct = dist.get("negative",0)/total*100
pos_pct = dist.get("positive",0)/total*100
neu_pct = dist.get("neutral",0)/total*100

with st.sidebar:
    st.markdown("### Data Source")
    source = st.session_state.get("data_source", "unknown")
    if source == "spaces":
        st.success("DigitalOcean Spaces")
    elif source == "local":
        st.warning("Local Files")
    else:
        st.error("Offline")
    
    run_info = st.session_state.get("run_info")
    if run_info:
        st.markdown("### Run Info")
        st.markdown(format_run_info(run_info))

st.title("MBG Program  Public Discourse Analysis")
st.caption("Makan Bergizi Gratis  Twitter/X  107,375 tweets  20172026  Research Dashboard")
st.markdown("---")

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Total Tweets", f"{total:,}")
c2.metric("Negative", f"{neg_pct:.1f}%", f"{dist.get('negative',0):,} tweets")
c3.metric("Neutral",  f"{neu_pct:.1f}%", f"{dist.get('neutral',0):,} tweets")
c4.metric("Positive", f"{pos_pct:.1f}%", f"{dist.get('positive',0):,} tweets")
c5.metric("Unique Users", f"{df['user_id'].nunique():,}")
c6.metric("Date Range", f"{df['date'].min().strftime('%b %Y')}  {df['date'].max().strftime('%b %Y')}")

st.markdown("---")

st.markdown("### Sentiment Trend Over Time")
st.caption("Negativity has been rising sharply since mid-2025  from 37% to over 52%")

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

st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Monthly Tweet Volume")
    vol = df.groupby(df["date"].dt.to_period("M")).size().reset_index()
    vol.columns = ["month","count"]
    vol["month"] = vol["month"].dt.to_timestamp()
    fig2 = px.bar(vol, x="month", y="count", color_discrete_sequence=["#3498db"])
    fig2.update_layout(height=280, margin=dict(t=10,b=10), yaxis_title="Tweets")
    st.plotly_chart(fig2, use_container_width=True)

with col2:
    st.markdown("### Key Research Findings")
    st.error("**Negativity is accelerating**  37% negative at start  53% in early 2026. A 16-point shift.")
    st.warning("**Negative tweets spread 3.4 further**  avg 109 retweets vs 32 for positive (p<0.000001).")
    st.success("**Outer islands are more positive**  Papua/NTT/Maluku show 39% positive vs Java's 24%.")
    st.info("**Morning discourse**  Peak posting at 6am WIB. People react to school meal news at day start.")

st.markdown("---")
st.markdown("### Dashboard Navigation")

nav_pages = [
    ("1_overview", "Overview", "Volume trends, sentiment analysis, negativity trend, posting patterns, data freshness"),
    ("2_sentiment_topics", "Sentiment & Topics", "Sentiment distribution, topic breakdown, parentreply sentiment flow, topicreply heatmap"),
    ("3_engagement_virality", "Engagement & Virality", "Engagement by sentiment, spike detection, viral posts, talk vs amplify ratio"),
    ("4_replies_controversy", "Replies & Controversy", "Reply sentiment trends, controversy scores, reply depth, hourly/weekly patterns"),
    ("5_bots_influence", "Bots & Influence", "Bot detection scores, flagged accounts, influence leaderboard, sentiment consistency"),
    ("6_co_reply_network", "Co-Reply Network", "Community detection, force-directed graph, ego network explorer, community profiles"),
    ("7_tweet_explorer", "Tweet Explorer", "Search, filter, and browse all tweets in the corpus"),
]

cols = st.columns(3)
for i, (page, title, desc) in enumerate(nav_pages):
    with cols[i % 3]:
        st.markdown(f"**{title}**\n{desc}")
