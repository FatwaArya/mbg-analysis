import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Thread Analysis  MBG", page_icon=None, layout="wide")
require_auth()

st.title("Thread & Conversation Analysis")
st.caption("Reply depth patterns, conversation starters, and engagement by thread level")
st.markdown("---")

depth_stats = load_reply_dataset("thread_depth_stats")
parent_conv = load_reply_dataset("parent_conversation_stats")

if depth_stats is None:
    st.error("Thread analysis data not available. Run r10_thread_analysis.py first.")
    st.stop()

#  KPIs
total_parents = len(parent_conv) if parent_conv is not None else 0
max_depth = int(depth_stats["depth"].max())
avg_replies = depth_stats["reply_count"].sum() / len(depth_stats) if len(depth_stats) > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Parent Posts", f"{total_parents:,}")
c2.metric("Max Thread Depth", f"{max_depth}")
c3.metric("Avg Replies/Parent", f"{avg_replies:.1f}")
c4.metric("Depth Levels", f"{len(depth_stats)}")

st.markdown("---")

#  1. Depth Distribution
st.subheader("Reply Volume by Depth")
fig_depth = px.bar(
    depth_stats, x="depth", y="reply_count",
    labels={"depth": "Depth Level", "reply_count": "Number of Replies"},
    color="reply_count", color_continuous_scale="Blues"
)
fig_depth.update_layout(showlegend=False)
st.plotly_chart(fig_depth, use_container_width=True)

#  2. Engagement by Depth
st.subheader("Engagement Metrics by Depth")
col1, col2 = st.columns(2)
with col1:
    fig_fav = px.line(
        depth_stats, x="depth", y="avg_favorites",
        markers=True, labels={"depth": "Depth Level", "avg_favorites": "Avg Favorites"},
        color_discrete_sequence=["#e74c3c"]
    )
    st.plotly_chart(fig_fav, use_container_width=True)

with col2:
    fig_rt = px.line(
        depth_stats, x="depth", y="avg_retweets",
        markers=True, labels={"depth": "Depth Level", "avg_retweets": "Avg Retweets"},
        color_discrete_sequence=["#3498db"]
    )
    st.plotly_chart(fig_rt, use_container_width=True)

#  3. Sentiment by Depth
st.subheader("Sentiment Distribution by Depth")
fig_sent = px.bar(
    depth_stats.melt(id_vars=["depth"], value_vars=["neg_pct", "neu_pct", "pos_pct"],
                     var_name="sentiment", value_name="percentage"),
    x="depth", y="percentage", color="sentiment",
    labels={"depth": "Depth Level", "percentage": "Percentage (%)", "sentiment": "Sentiment"},
    color_discrete_map={"neg_pct": "#e74c3c", "neu_pct": "#95a5a6", "pos_pct": "#2ecc71"},
    barmode="group"
)
st.plotly_chart(fig_sent, use_container_width=True)

#  4. Top Conversation Starters
st.subheader("Top Conversation Starters (Most Replied Parents)")
if parent_conv is not None and len(parent_conv) > 0:
    st.dataframe(
        parent_conv[["parent_id", "reply_count", "unique_users", "max_depth",
                      "conversation_span_hours", "neg_pct", "neu_pct", "pos_pct",
                      "sentiment_diversity"]].head(50),
        use_container_width=True,
        column_config={
            "parent_id": "Parent ID",
            "reply_count": "Replies",
            "unique_users": "Unique Users",
            "max_depth": "Max Depth",
            "conversation_span_hours": st.column_config.NumberColumn("Span (hrs)", format="%.1f"),
            "neg_pct": st.column_config.NumberColumn("Neg %", format="%.1f"),
            "neu_pct": st.column_config.NumberColumn("Neu %", format="%.1f"),
            "pos_pct": st.column_config.NumberColumn("Pos %", format="%.1f"),
            "sentiment_diversity": "Sentiment Diversity",
        }
    )

#  5. Reply Count Distribution
if parent_conv is not None and len(parent_conv) > 0:
    st.subheader("Reply Count Distribution (Log Scale)")
    fig_hist = px.histogram(
        parent_conv, x="reply_count", nbins=50,
        labels={"reply_count": "Replies per Parent", "count": "Number of Parents"},
        color_discrete_sequence=["#9b59b6"], log_y=True
    )
    fig_hist.update_layout(bargap=0.05, showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)
