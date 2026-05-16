import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Bot Detection  MBG", page_icon=None, layout="wide")
require_auth()

st.title("Bot Detection Analysis")
st.caption("Multi-signal composite scoring to identify automated or suspicious accounts")
st.markdown("---")

bot_scores = load_reply_dataset("user_bot_scores")
flagged = load_reply_dataset("flagged_bots")

if bot_scores is None:
    st.error("Bot detection data not available. Run r8_bot_detection.py first.")
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

#  1. Bot Score Distribution
st.subheader("Bot Score Distribution")
fig_hist = px.histogram(
    bot_scores, x="bot_score", nbins=50,
    labels={"bot_score": "Bot Score", "count": "Number of Users"},
    color_discrete_sequence=["#3498db"]
)
fig_hist.add_vline(x=0.5, line_dash="dash", line_color="red", annotation_text="Threshold (0.5)")
fig_hist.update_layout(bargap=0.05, showlegend=False)
st.plotly_chart(fig_hist, use_container_width=True)

#  2. Signal Breakdown
st.subheader("Signal Breakdown")
signal_cols = ["username_score", "temporal_score", "content_score", "engagement_score", "intensity_score"]
signal_labels = ["Username Anomaly", "Temporal Pattern", "Content Diversity", "Engagement Ratio", "Activity Intensity"]

for col, label in zip(signal_cols, signal_labels):
    fig = px.histogram(
        bot_scores, x=col, nbins=30,
        labels={col: label, "count": "Users"},
        color_discrete_sequence=["#2ecc71"]
    )
    fig.update_layout(bargap=0.05, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

#  3. Top Flagged Bots Table
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
else:
    st.info("No accounts flagged as bots at the current threshold.")

#  4. Radar Chart for Top Bots
st.subheader("Top Bot Profiles (Radar)")
if flagged is not None and len(flagged) > 0:
    top_bots = flagged.head(5)
    radar_cols = ["username_score", "temporal_score", "content_score", "engagement_score", "intensity_score"]
    radar_labels = ["Username", "Temporal", "Content", "Engagement", "Intensity"]

    fig_radar = go.Figure()
    for _, bot in top_bots.iterrows():
        fig_radar.add_trace(go.Scatterpolar(
            r=[bot[c] for c in radar_cols],
            theta=radar_labels,
            fill="toself",
            name=bot["user_screen_name"]
        ))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True)
    st.plotly_chart(fig_radar, use_container_width=True)

#  5. Activity vs Bot Score
st.subheader("Activity Volume vs Bot Score")
fig_scatter = px.scatter(
    bot_scores[bot_scores["tweet_count"] > 1],
    x="tweet_count", y="bot_score",
    color="is_bot", color_discrete_map={True: "#e74c3c", False: "#3498db"},
    labels={"tweet_count": "Number of Replies", "bot_score": "Bot Score"},
    log_x=True
)
fig_scatter.update_layout(showlegend=True)
st.plotly_chart(fig_scatter, use_container_width=True)
