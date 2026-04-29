import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Sentiment · MBG", page_icon="📊", layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

st.title("📊 Sentiment Analysis")
st.caption("How does the public feel about the MBG program?")
st.markdown("---")

@st.cache_data
def load():
    df = pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])
    return df

df = load()
dist = df["sentiment_normalized"].value_counts()
total = len(df)

# ── Row 1: distribution + key insight ────────────────────────────────────────
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("#### Overall Sentiment")
    fig = px.pie(values=dist.values, names=dist.index,
                 color=dist.index, color_discrete_map=COLORS,
                 hole=0.45)
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Sentiment Over Time (daily %)")
    daily = (df.groupby(["date", "sentiment_normalized"])
               .size().unstack(fill_value=0))
    daily_pct = daily.div(daily.sum(axis=1), axis=0) * 100
    fig2 = go.Figure()
    for s, color in COLORS.items():
        if s in daily_pct.columns:
            fig2.add_trace(go.Scatter(
                x=daily_pct.index, y=daily_pct[s].rolling(7).mean(),
                name=s.capitalize(), line=dict(color=color, width=2),
                fill="tonexty" if s == "positive" else None,
                hovertemplate="%{y:.1f}%"
            ))
    fig2.update_layout(
        yaxis_title="% of tweets (7-day avg)",
        hovermode="x unified", legend_title="Sentiment",
        margin=dict(t=10, b=10)
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Row 2: engagement + language breakdown ────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("#### Average Engagement by Sentiment")
    st.caption("Do negative posts get more likes/retweets?")
    eng = df.groupby("sentiment_normalized").agg(
        avg_likes=("favorite_count", "mean"),
        avg_retweets=("retweet_count", "mean"),
        avg_replies=("reply_count", "mean"),
    ).reset_index()
    fig3 = px.bar(eng.melt(id_vars="sentiment_normalized"),
                  x="sentiment_normalized", y="value", color="variable",
                  barmode="group",
                  color_discrete_map={"avg_likes":"#f39c12","avg_retweets":"#3498db","avg_replies":"#9b59b6"},
                  labels={"sentiment_normalized":"Sentiment","value":"Avg count","variable":"Metric"})
    fig3.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Sentiment by Language")
    lang_sent = (df.groupby(["detected_lang", "sentiment_normalized"])
                   .size().unstack(fill_value=0))
    lang_pct = lang_sent.div(lang_sent.sum(axis=1), axis=0) * 100
    top_langs = lang_sent.sum(axis=1).nlargest(8).index
    fig4 = px.bar(lang_pct.loc[top_langs].reset_index().melt(id_vars="detected_lang"),
                  x="detected_lang", y="value", color="sentiment_normalized",
                  color_discrete_map=COLORS, barmode="stack",
                  labels={"detected_lang":"Language","value":"%","sentiment_normalized":"Sentiment"})
    fig4.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Row 3: top posts table ────────────────────────────────────────────────────
st.markdown("#### Top Posts by Sentiment")
tab_neg, tab_pos, tab_neu = st.tabs(["😠 Most Negative", "😊 Most Positive", "😐 Most Neutral"])

cols_show = ["text", "sentiment_score", "engagement_total", "favorite_count", "retweet_count", "date"]

for tab, sent in [(tab_neg, "negative"), (tab_pos, "positive"), (tab_neu, "neutral")]:
    with tab:
        subset = df[df["sentiment_normalized"] == sent].nlargest(20, "engagement_total")
        st.dataframe(subset[cols_show], use_container_width=True, hide_index=True)
