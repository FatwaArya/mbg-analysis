import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Bots & Influence  MBG", page_icon=None, layout="wide")
require_auth()

st.title("Bot Detection & Influence")
st.caption("Automated accounts, key actors, sentiment consistency, and amplification patterns")
st.markdown("---")

bot_scores = load_reply_dataset("user_bot_scores")
flagged = load_reply_dataset("flagged_bots")
influence = load_reply_dataset("user_influence_scores")
sentiment_cons = load_reply_dataset("sentiment_consistency")

if bot_scores is None or influence is None:
    st.error("Bot/influence data not available. Run analysis scripts first.")
    st.stop()

total_users = len(bot_scores)
total_flagged = len(flagged) if flagged is not None else 0
avg_score = bot_scores["bot_score"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Users Analyzed", f"{total_users:,}")
c2.metric("Flagged as Bots", f"{total_flagged:,}", f"{total_flagged/total_users*100:.1f}%")
c3.metric("Avg Bot Score", f"{avg_score:.3f}")
c4.metric("Threshold", "0.500")

st.markdown("---")

st.subheader("Bot Score Distribution")

col1, col2 = st.columns(2)
with col1:
    fig_hist = px.histogram(
        bot_scores, x="bot_score", nbins=50,
        labels={"bot_score": "Bot Score", "count": "Number of Users"},
        color_discrete_sequence=["#3498db"]
    )
    fig_hist.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold (0.5)")
    fig_hist.update_layout(bargap=0.05, showlegend=False, height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    fig_scatter = px.scatter(
        bot_scores[bot_scores["tweet_count"] > 1],
        x="tweet_count", y="bot_score",
        color="is_bot", color_discrete_map={True: "#e74c3c", False: "#3498db"},
        labels={"tweet_count": "Number of Replies", "bot_score": "Bot Score"},
        log_x=True
    )
    fig_scatter.update_layout(height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

st.subheader("Signal Breakdown")

signal_cols = ["username_score", "temporal_score", "content_score", "engagement_score", "intensity_score"]
signal_labels = ["Username Anomaly", "Temporal Pattern", "Content Diversity", "Engagement Ratio", "Activity Intensity"]

for col, label in zip(signal_cols, signal_labels):
    fig = px.histogram(
        bot_scores, x=col, nbins=30,
        labels={col: label, "count": "Users"},
        color_discrete_sequence=["#2ecc71"]
    )
    fig.update_layout(bargap=0.05, showlegend=False, height=200, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("Flagged Bot Accounts")

if flagged is not None and len(flagged) > 0:
    st.dataframe(
        flagged[["user_screen_name", "bot_score", "tweet_count", "avg_fav", "tweets_per_day",
                  "username_score", "temporal_score", "content_score", "engagement_score", "intensity_score"]].head(100),
        use_container_width=True,
        column_config={
            "user_screen_name": st.column_config.TextColumn("Username"),
            "bot_score": st.column_config.NumberColumn("Bot Score", format="%.4f"),
            "tweet_count": st.column_config.NumberColumn("Tweets"),
            "avg_fav": st.column_config.NumberColumn("Avg Favorites", format="%.2f"),
            "tweets_per_day": st.column_config.NumberColumn("Tweets/Day", format="%.2f"),
            "username_score": st.column_config.NumberColumn("Username", format="%.3f"),
            "temporal_score": st.column_config.NumberColumn("Temporal", format="%.3f"),
            "content_score": st.column_config.NumberColumn("Content", format="%.3f"),
            "engagement_score": st.column_config.NumberColumn("Engagement", format="%.3f"),
            "intensity_score": st.column_config.NumberColumn("Intensity", format="%.3f"),
        }
    )

st.markdown("---")

st.subheader("Influence Leaderboard")

c1i, c2i, c3i = st.columns(3)
c1i.metric("Top Influencer", influence.iloc[0]["user"] if len(influence) > 0 else "N/A")
c2i.metric("Top Score", f"{influence['influence_score'].max():.2f}" if len(influence) > 0 else "N/A")
c3i.metric("Avg Engagement", f"{influence['avg_engagement'].mean():.1f}")

st.dataframe(
    influence[["user", "influence_score", "total_engagement", "total_favs", "total_rts",
                "total_replies_received", "tweet_count", "reply_reach", "avg_engagement"]].head(50),
    use_container_width=True,
    column_config={
        "user": "Username",
        "influence_score": st.column_config.NumberColumn("Score", format="%.2f"),
        "total_engagement": "Total Engagement",
        "total_favs": "Favorites",
        "total_rts": "Retweets",
        "total_replies_received": "Replies Received",
        "tweet_count": "Tweets",
        "reply_reach": "Reply Reach",
        "avg_engagement": st.column_config.NumberColumn("Avg Engagement", format="%.2f"),
    }
)

st.markdown("---")

st.subheader("Influence vs Activity")

fig_inf = px.scatter(
    influence[influence["tweet_count"] > 1],
    x="tweet_count", y="total_engagement",
    color="influence_score", color_continuous_scale="Viridis",
    labels={"tweet_count": "Number of Replies", "total_engagement": "Total Engagement"},
    log_x=True, log_y=True
)
fig_inf.update_layout(height=400, margin=dict(t=10, b=10), showlegend=False)
st.plotly_chart(fig_inf, use_container_width=True)

st.markdown("---")

st.subheader("Sentiment Consistency")

if sentiment_cons is not None:
    col1c, col2c = st.columns(2)
    with col1c:
        fig_dom = px.pie(
            sentiment_cons, names="dominant_sentiment",
            labels={"dominant_sentiment": "Dominant Sentiment"},
            color="dominant_sentiment",
            color_discrete_map={"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}
        )
        st.plotly_chart(fig_dom, use_container_width=True)

    with col2c:
        fig_cons = px.histogram(
            sentiment_cons, x="consistency", nbins=50,
            labels={"consistency": "Consistency (1 = always same sentiment)", "count": "Users"},
            color_discrete_sequence=["#9b59b6"]
        )
        fig_cons.update_layout(bargap=0.05, showlegend=False, height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig_cons, use_container_width=True)

    st.subheader("Most Consistent Users (Single Sentiment)")
    consistent = sentiment_cons[sentiment_cons["consistency"] >= 0.9].sort_values("tweet_count", ascending=False)
    if len(consistent) > 0:
        st.dataframe(
            consistent[["user", "dominant_sentiment", "consistency", "dominant_pct", "tweet_count"]].head(30),
            use_container_width=True,
            column_config={
                "user": "Username",
                "dominant_sentiment": "Dominant",
                "consistency": st.column_config.NumberColumn("Consistency", format="%.3f"),
                "dominant_pct": st.column_config.NumberColumn("Dominant %", format="%.1f"),
                "tweet_count": "Tweets",
            }
        )

st.markdown("---")

st.subheader("Amplification: Favorites vs Tweets")

fig_amp = px.scatter(
    influence[influence["tweet_count"] > 1],
    x="tweet_count", y="total_favs",
    color="avg_engagement", color_continuous_scale="Plasma",
    labels={"tweet_count": "Number of Replies", "total_favs": "Total Favorites Received"},
    log_x=True, log_y=True
)
fig_amp.update_layout(height=400, margin=dict(t=10, b=10), showlegend=False)
st.plotly_chart(fig_amp, use_container_width=True)
