import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Influence Analysis  MBG", page_icon=None, layout="wide")
require_auth()

st.title("Influence & Sentiment Consistency")
st.caption("User influence scores, sentiment patterns, and amplification metrics")
st.markdown("---")

influence = load_reply_dataset("user_influence_scores")
sentiment_cons = load_reply_dataset("sentiment_consistency")

if influence is None:
    st.error("Influence data not available. Run r11_influence_analysis.py first.")
    st.stop()

#  KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Users Analyzed", f"{len(influence):,}")
c2.metric("Top Influencer", influence.iloc[0]["user"] if len(influence) > 0 else "N/A")
c3.metric("Top Influence Score", f"{influence['influence_score'].max():.2f}" if len(influence) > 0 else "N/A")
c4.metric("Avg Engagement", f"{influence['avg_engagement'].mean():.1f}")

st.markdown("---")

#  1. Influence Leaderboard
st.subheader("Influence Leaderboard")
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

#  2. Influence Distribution
st.subheader("Influence Score Distribution")
fig_hist = px.histogram(
    influence[influence["influence_score"] > 0], x="influence_score", nbins=50,
    labels={"influence_score": "Influence Score", "count": "Users"},
    color_discrete_sequence=["#e67e22"], log_y=True
)
fig_hist.update_layout(bargap=0.05, showlegend=False)
st.plotly_chart(fig_hist, use_container_width=True)

#  3. Engagement vs Tweet Count
st.subheader("Total Engagement vs Tweet Count")
fig_scatter = px.scatter(
    influence[influence["tweet_count"] > 1],
    x="tweet_count", y="total_engagement",
    color="influence_score", color_continuous_scale="Viridis",
    labels={"tweet_count": "Number of Replies", "total_engagement": "Total Engagement"},
    log_x=True, log_y=True
)
fig_scatter.update_layout(showlegend=False)
st.plotly_chart(fig_scatter, use_container_width=True)

#  4. Sentiment Consistency
if sentiment_cons is not None:
    st.subheader("Sentiment Consistency Analysis")
    col1, col2 = st.columns(2)

    with col1:
        fig_dom = px.pie(
            sentiment_cons, names="dominant_sentiment",
            labels={"dominant_sentiment": "Dominant Sentiment"},
            color="dominant_sentiment",
            color_discrete_map={"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}
        )
        st.plotly_chart(fig_dom, use_container_width=True)

    with col2:
        fig_cons = px.histogram(
            sentiment_cons, x="consistency", nbins=50,
            labels={"consistency": "Consistency Score (1 = Always Same Sentiment)", "count": "Users"},
            color_discrete_sequence=["#9b59b6"]
        )
        fig_cons.update_layout(bargap=0.05, showlegend=False)
        st.plotly_chart(fig_cons, use_container_width=True)

    #  5. Consistency Heatmap
    st.subheader("Sentiment Distribution Heatmap (Top 50 Users)")
    top_users = sentiment_cons.nlargest(50, "tweet_count")
    heatmap_data = top_users[["user", "neg_count", "neu_count", "pos_count"]].set_index("user")
    heatmap_data = heatmap_data.div(heatmap_data.sum(axis=1), axis=0)

    fig_heatmap = px.imshow(
        heatmap_data.T,
        labels=dict(x="User", y="Sentiment", color="Proportion"),
        color_continuous_scale="RdYlGn_r",
        aspect="auto"
    )
    fig_heatmap.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    #  6. Most Consistent Users
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
    else:
        st.info("No users with consistency >= 0.9")

#  7. Amplification Analysis
st.subheader("Amplification: Favorites vs Tweets")
fig_amp = px.scatter(
    influence[influence["tweet_count"] > 1],
    x="tweet_count", y="total_favs",
    color="avg_engagement", color_continuous_scale="Plasma",
    labels={"tweet_count": "Number of Replies", "total_favs": "Total Favorites Received"},
    log_x=True, log_y=True
)
fig_amp.update_layout(showlegend=False)
st.plotly_chart(fig_amp, use_container_width=True)
