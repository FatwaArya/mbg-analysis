import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Engagement · MBG", page_icon="💬", layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

st.title("💬 Engagement Patterns")
st.caption("How does the public interact with MBG content?")
st.markdown("---")

@st.cache_data
def load():
    return pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])

df = load()
df["talk_amplify"] = df["reply_count"] / (df["retweet_count"] + 1)

# ── Row 1: volume + hourly ────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Daily Tweet Volume")
    daily = df.groupby("date").size().reset_index(name="count")
    fig = px.area(daily, x="date", y="count", color_discrete_sequence=["#3498db"])
    fig.update_layout(margin=dict(t=10, b=10), yaxis_title="Tweets")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Posting by Hour of Day")
    st.caption("When are people tweeting about MBG?")
    hourly = df.groupby("hour").size().reset_index(name="count")
    fig2 = px.bar(hourly, x="hour", y="count", color="count",
                  color_continuous_scale="Blues")
    fig2.update_layout(margin=dict(t=10, b=10), coloraxis_showscale=False,
                       xaxis_title="Hour (UTC)", yaxis_title="Tweets")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Row 2: talk/amplify + engagement dist ────────────────────────────────────
col3, col4 = st.columns(2)
with col3:
    st.markdown("#### Talk vs Amplify Ratio by Sentiment")
    st.caption("High ratio = more replies than retweets (debate). Low = amplification.")
    ratio = df.groupby("sentiment_normalized")["talk_amplify"].mean().reset_index()
    fig3 = px.bar(ratio, x="sentiment_normalized", y="talk_amplify",
                  color="sentiment_normalized", color_discrete_map=COLORS,
                  labels={"sentiment_normalized": "Sentiment", "talk_amplify": "Reply / (RT+1)"})
    fig3.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Engagement Distribution (log scale)")
    fig4 = px.histogram(df[df["engagement_total"] > 0], x="engagement_total",
                        color="sentiment_normalized", color_discrete_map=COLORS,
                        log_x=True, barmode="overlay", opacity=0.7,
                        labels={"engagement_total": "Total Engagement (log)"})
    fig4.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Top posts ─────────────────────────────────────────────────────────────────
st.markdown("#### 🏆 Top 20 Most Engaging Posts")
top = df.nlargest(20, "engagement_total")[
    ["text", "engagement_total", "favorite_count", "retweet_count",
     "reply_count", "sentiment_normalized", "date"]
]
st.dataframe(top, use_container_width=True, hide_index=True)
