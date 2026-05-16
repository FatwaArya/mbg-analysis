import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset

st.set_page_config(page_title="Replies  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("Reply Analysis")
st.caption("How replies react to parent posts  sentiment shift, controversy, and debate depth")
st.markdown("---")

replies = load_reply_dataset("replies_with_sentiment")
tree = load_reply_dataset("reply_tree")
controversy = load_reply_dataset("reply_controversy_scores")
sentiment_shift = load_reply_dataset("reply_sentiment_shift")
depth_sent = load_reply_dataset("reply_depth_sentiment")
talk_amplify = load_reply_dataset("reply_talk_amplify")
most_replied = load_reply_dataset("reply_most_replied_parents")
sentiment_trend = load_reply_dataset("reply_sentiment_trend")
hourly_pattern = load_reply_dataset("reply_hourly_pattern")
weekly_pattern = load_reply_dataset("reply_weekly_pattern")
sentiment_matrix = load_reply_dataset("reply_vs_parent_sentiment_matrix")
engagement_comparison = load_reply_dataset("engagement_parent_vs_reply")
reply_daily_vol = load_reply_dataset("reply_daily_volume")

if replies is None:
    st.error("Reply data not available. Run the reply pipeline first.")
    st.stop()

total = len(replies)
dist = replies["sentiment_normalized"].value_counts()

#  KPIs
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Replies", f"{total:,}")
c2.metric("Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,}")
c3.metric("Neutral",  f"{dist.get('neutral',0)/total*100:.1f}%",  f"{dist.get('neutral',0):,}")
c4.metric("Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,}")
c5.metric("Unique Parents", f"{replies['parent_id'].nunique():,}")

st.markdown("---")

#  1. Sentiment Shift Sankey
st.markdown("### Sentiment Shift: Parent  Reply")
st.caption("Flow from parent post sentiment to reply sentiment")

if sentiment_matrix is not None and len(sentiment_matrix) > 0:
    labels = ["negative", "neutral", "positive"]
    label_colors = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

    source_indices = []
    target_indices = []
    values = []

    for _, row in sentiment_matrix.iterrows():
        src = labels.index(row["parent_sentiment"])
        tgt = labels.index(row["reply_sentiment"]) + 3
        source_indices.append(src)
        target_indices.append(tgt)
        values.append(int(row["count"]))

    all_labels = labels + [f"reply: {l}" for l in labels]
    node_colors = [label_colors[l] for l in labels] + [label_colors[l] for l in labels]

    fig_sankey = go.Figure(data=[go.Sankey(
        node=dict(pad=15, thickness=20, line=dict(color="black", width=0.5),
                  label=all_labels, color=node_colors),
        link=dict(source=source_indices, target=target_indices, value=values)
    )])
    fig_sankey.update_layout(title_text="Parent Sentiment  Reply Sentiment Flow",
                             font_size=12, height=350, margin=dict(t=40,b=10))
    st.plotly_chart(fig_sankey, use_container_width=True)
elif sentiment_shift is not None and len(sentiment_shift) > 0:
    fig = px.bar(sentiment_shift, x="sentiment_shift", y="count", color="depth",
                 barmode="group", color_discrete_map={1: "#3498db", 2: "#e67e22"},
                 labels={"sentiment_shift":"Shift","count":"Replies"})
    fig.update_layout(xaxis_tickangle=-30, height=320, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  2. Reply Sentiment Over Time
st.markdown("### Reply Sentiment Trend (Daily)")
st.caption("7-day rolling average to smooth noise")

if sentiment_trend is not None and len(sentiment_trend) > 0:
    sentiment_trend["date"] = pd.to_datetime(sentiment_trend["date"])
    sentiment_trend = sentiment_trend.sort_values("date")
    sentiment_trend["neg_7d"] = sentiment_trend["neg_pct"].rolling(7, min_periods=1).mean()
    sentiment_trend["neu_7d"] = sentiment_trend["neu_pct"].rolling(7, min_periods=1).mean()
    sentiment_trend["pos_7d"] = sentiment_trend["pos_pct"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sentiment_trend["date"], y=sentiment_trend["neg_7d"],
                             name="Negative", line=dict(color="#e74c3c", width=2)))
    fig.add_trace(go.Scatter(x=sentiment_trend["date"], y=sentiment_trend["neu_7d"],
                             name="Neutral", line=dict(color="#95a5a6", width=2)))
    fig.add_trace(go.Scatter(x=sentiment_trend["date"], y=sentiment_trend["pos_7d"],
                             name="Positive", line=dict(color="#2ecc71", width=2)))
    fig.add_hline(y=50, line_dash="dot", line_color="red", annotation_text="50% threshold")
    fig.update_layout(hovermode="x unified", yaxis_title="% of replies (7-day avg)",
                      height=320, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  3. Engagement: Parent vs Reply
st.markdown("### Engagement: Parent vs Reply by Sentiment")
st.caption("Negative posts get more engagement across both parents and replies")

if engagement_comparison is not None and len(engagement_comparison) > 0:
    eng_melt = engagement_comparison.melt(
        id_vars=["sentiment_normalized", "type"],
        value_vars=["avg_favorites", "avg_retweets", "avg_replies"],
        var_name="metric", value_name="avg_count"
    )
    eng_melt["metric"] = eng_melt["metric"].str.replace("avg_", "").str.title()

    fig = px.bar(eng_melt, x="sentiment_normalized", y="avg_count",
                 color="type", barmode="group", facet_col="metric",
                 color_discrete_map={"parent": "#3498db", "reply": "#e67e22"},
                 labels={"sentiment_normalized":"Sentiment","avg_count":"Avg Count","type":""},
                 facet_col_wrap=3)
    fig.update_layout(height=350, margin=dict(t=10,b=10), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  4. Reply Volume Trend
st.markdown("### Reply Volume Over Time")

if reply_daily_vol is not None and len(reply_daily_vol) > 0:
    reply_daily_vol["date"] = pd.to_datetime(reply_daily_vol["date"])
    reply_daily_vol = reply_daily_vol.sort_values("date")
    reply_daily_vol["rolling_7d"] = reply_daily_vol["reply_count"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Bar(x=reply_daily_vol["date"], y=reply_daily_vol["reply_count"],
                         name="Daily", marker_color="rgba(52,152,219,0.4)"))
    fig.add_trace(go.Scatter(x=reply_daily_vol["date"], y=reply_daily_vol["rolling_7d"],
                             name="7-day avg", line=dict(color="#3498db", width=2)))
    fig.update_layout(hovermode="x unified", yaxis_title="Replies per day",
                      height=320, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  5. Hourly + Weekly Patterns
col_h, col_w = st.columns(2)
with col_h:
    st.markdown("#### Reply Hourly Pattern (WIB)")
    if hourly_pattern is not None and len(hourly_pattern) > 0:
        fig = px.bar(hourly_pattern, x="hour_wib", y="reply_count",
                     color="reply_count", color_continuous_scale="Reds",
                     labels={"hour_wib":"Hour (WIB)","reply_count":"Replies"})
        fig.update_layout(height=280, margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

with col_w:
    st.markdown("#### Reply Day-of-Week Pattern")
    if weekly_pattern is not None and len(weekly_pattern) > 0:
        dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        weekly_pattern["dayofweek"] = pd.Categorical(weekly_pattern["dayofweek"], categories=dow_order, ordered=True)
        weekly_pattern = weekly_pattern.sort_values("dayofweek")
        fig = px.bar(weekly_pattern, x="dayofweek", y="reply_count",
                     color="reply_count", color_continuous_scale="Blues",
                     labels={"dayofweek":"Day","reply_count":"Replies"})
        fig.update_layout(height=280, margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  6. Controversy Distribution
st.markdown("### Controversy Score Distribution")
st.caption("High controversy = parent attracts both positive AND negative replies")

if controversy is not None and len(controversy) > 0:
    fig = px.histogram(controversy, x="controversy_score", nbins=50,
                       color_discrete_sequence=["#3498db"],
                       labels={"controversy_score":"Controversy Score","count":"Parent Posts"})
    fig.update_layout(height=300, margin=dict(t=10,b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Avg Controversy", f"{controversy['controversy_score'].mean():.3f}")
    col_c2.metric("Median", f"{controversy['controversy_score'].median():.3f}")
    col_c3.metric("Max", f"{controversy['controversy_score'].max():.3f}")

st.markdown("---")

#  7. Depth vs Sentiment
st.markdown("### Reply Depth vs Sentiment")
st.caption("Depth-1 = direct reply to parent. Depth-2 = reply to another reply.")

if depth_sent is not None and len(depth_sent) > 0:
    depth_sent["depth_label"] = depth_sent["depth"].map({0:"unknown", 1:"depth-1 ( parent)", 2:"depth-2 ( reply)"})
    fig = px.bar(depth_sent, x="depth_label", y="count", color="sentiment_normalized",
                 color_discrete_map=COLORS, barmode="group",
                 labels={"depth_label":"Depth","count":"Replies","sentiment_normalized":""})
    fig.update_layout(height=320, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  8. Most Replied Parents
st.markdown("### Top 20 Most Replied Parent Posts")

if most_replied is not None and len(most_replied) > 0:
    st.dataframe(most_replied.head(20), use_container_width=True, hide_index=True)
