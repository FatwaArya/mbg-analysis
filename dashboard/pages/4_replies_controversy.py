import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset, load_with_fallback, filter_topics

st.set_page_config(page_title="Replies & Controversy  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

st.title("Replies & Controversy")
st.caption("How people debate, what sparks polarization, and conversation depth patterns")
st.markdown("---")

replies = load_reply_dataset("replies_with_sentiment")
controversy = load_reply_dataset("reply_controversy_scores")
cont_by_topic = load_reply_dataset("controversy_by_topic")
cont_over_time = load_reply_dataset("controversy_over_time")
top_controversial = load_reply_dataset("top_controversial_parents")
cont_vs_eng = load_reply_dataset("controversy_vs_engagement")
sentiment_trend = load_reply_dataset("reply_sentiment_trend")
hourly_pattern = load_reply_dataset("reply_hourly_pattern")
weekly_pattern = load_reply_dataset("reply_weekly_pattern")
sentiment_matrix = load_reply_dataset("reply_vs_parent_sentiment_matrix")
engagement_comparison = load_reply_dataset("engagement_parent_vs_reply")
reply_daily_vol = load_reply_dataset("reply_daily_volume")
depth_stats = load_reply_dataset("thread_depth_stats")
parent_conv = load_reply_dataset("parent_conversation_stats")

topic_info = load_with_fallback("topic_info")[0]
topic_info_filtered = filter_topics(topic_info) if topic_info is not None else None

if replies is None:
    st.error("Reply data not available. Run the reply pipeline first.")
    st.stop()

total = len(replies)
dist = replies["sentiment_normalized"].value_counts()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Replies", f"{total:,}")
c2.metric("Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,}")
c3.metric("Neutral", f"{dist.get('neutral',0)/total*100:.1f}%", f"{dist.get('neutral',0):,}")
c4.metric("Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,}")
c5.metric("Unique Parents", f"{replies['parent_id'].nunique():,}")

st.markdown("---")

st.subheader("Reply Sentiment Trend (7-day Rolling)")

if sentiment_trend is not None and len(sentiment_trend) > 0:
    sentiment_trend["date"] = pd.to_datetime(sentiment_trend["date"])
    sentiment_trend = sentiment_trend.sort_values("date")
    for col in ["neg_pct", "neu_pct", "pos_pct"]:
        sentiment_trend[f"{col}_7d"] = sentiment_trend[col].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sentiment_trend["date"], y=sentiment_trend["neg_pct_7d"],
                             name="Negative", line=dict(color="#e74c3c", width=2)))
    fig.add_trace(go.Scatter(x=sentiment_trend["date"], y=sentiment_trend["neu_pct_7d"],
                             name="Neutral", line=dict(color="#95a5a6", width=2)))
    fig.add_trace(go.Scatter(x=sentiment_trend["date"], y=sentiment_trend["pos_pct_7d"],
                             name="Positive", line=dict(color="#2ecc71", width=2)))
    fig.add_hline(y=50, line_dash="dot", line_color="red", annotation_text="50%")
    fig.update_layout(hovermode="x unified", yaxis_title="% (7-day avg)", height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("Controversy Analysis")

if controversy is not None and len(controversy) > 0:
    col1, col2 = st.columns(2)
    with col1:
        fig_c1 = px.histogram(controversy, x="controversy_score", nbins=50,
                              color_discrete_sequence=["#3498db"],
                              labels={"controversy_score": "Controversy Score", "count": "Parent Posts"})
        fig_c1.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
        st.plotly_chart(fig_c1, use_container_width=True)

    with col2:
        c1m, c2m, c3m = st.columns(3)
        c1m.metric("Avg Controversy", f"{controversy['controversy_score'].mean():.3f}")
        c2m.metric("Median", f"{controversy['controversy_score'].median():.3f}")
        c3m.metric("Max", f"{controversy['controversy_score'].max():.3f}")

st.markdown("---")

st.subheader("Controversy vs Engagement")

if cont_vs_eng is not None and len(cont_vs_eng) > 0:
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        fig_e1 = px.bar(cont_vs_eng, x="controversy_bin", y="avg_favorites",
                        color="avg_favorites", color_continuous_scale="Oranges",
                        labels={"controversy_bin": "Controversy Range", "avg_favorites": "Avg Favorites"})
        fig_e1.update_layout(height=300, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_e1, use_container_width=True)

    with col_e2:
        fig_e2 = px.bar(cont_vs_eng, x="controversy_bin", y="avg_retweets",
                        color="avg_retweets", color_continuous_scale="Blues",
                        labels={"controversy_bin": "Controversy Range", "avg_retweets": "Avg Retweets"})
        fig_e2.update_layout(height=300, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_e2, use_container_width=True)

st.markdown("---")

st.subheader("Controversy Over Time")

if cont_over_time is not None and len(cont_over_time) > 0:
    cont_over_time["date"] = pd.to_datetime(cont_over_time["date"])
    fig_co = px.line(cont_over_time, x="date", y="avg_controversy",
                     labels={"date": "Date", "avg_controversy": "Avg Controversy Score"},
                     color_discrete_sequence=["#e74c3c"])
    fig_co.update_layout(height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig_co, use_container_width=True)

st.markdown("---")

st.subheader("Reply Volume & Patterns")

col_h, col_w = st.columns(2)
with col_h:
    st.markdown("#### Reply Hourly Pattern (WIB)")
    if hourly_pattern is not None and len(hourly_pattern) > 0:
        fig_h = px.bar(hourly_pattern, x="hour_wib", y="reply_count",
                       color="reply_count", color_continuous_scale="Reds",
                       labels={"hour_wib": "Hour (WIB)", "reply_count": "Replies"})
        fig_h.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_h, use_container_width=True)

with col_w:
    st.markdown("#### Reply Day-of-Week Pattern")
    if weekly_pattern is not None and len(weekly_pattern) > 0:
        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekly_pattern["dayofweek"] = pd.Categorical(weekly_pattern["dayofweek"], categories=dow_order, ordered=True)
        weekly_pattern = weekly_pattern.sort_values("dayofweek")
        fig_w = px.bar(weekly_pattern, x="dayofweek", y="reply_count",
                       color="reply_count", color_continuous_scale="Blues",
                       labels={"dayofweek": "Day", "reply_count": "Replies"})
        fig_w.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_w, use_container_width=True)

if reply_daily_vol is not None and len(reply_daily_vol) > 0:
    reply_daily_vol["date"] = pd.to_datetime(reply_daily_vol["date"])
    reply_daily_vol = reply_daily_vol.sort_values("date")
    reply_daily_vol["rolling_7d"] = reply_daily_vol["reply_count"].rolling(7, min_periods=1).mean()

    fig_rv = go.Figure()
    fig_rv.add_trace(go.Bar(x=reply_daily_vol["date"], y=reply_daily_vol["reply_count"],
                            name="Daily", marker_color="rgba(52,152,219,0.4)"))
    fig_rv.add_trace(go.Scatter(x=reply_daily_vol["date"], y=reply_daily_vol["rolling_7d"],
                                name="7-day avg", line=dict(color="#3498db", width=2)))
    fig_rv.update_layout(hovermode="x unified", yaxis_title="Replies per day", height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig_rv, use_container_width=True)

st.markdown("---")

st.subheader("Reply Depth & Engagement")

if depth_stats is not None and len(depth_stats) > 0:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        fig_d1 = px.bar(depth_stats, x="depth", y="reply_count",
                        labels={"depth": "Depth Level", "reply_count": "Replies"},
                        color="reply_count", color_continuous_scale="Blues")
        fig_d1.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False, showlegend=False)
        st.plotly_chart(fig_d1, use_container_width=True)

    with col_d2:
        fig_d2 = px.line(depth_stats, x="depth", y="avg_favorites",
                         markers=True, labels={"depth": "Depth Level", "avg_favorites": "Avg Favorites"},
                         color_discrete_sequence=["#e74c3c"])
        fig_d2.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig_d2, use_container_width=True)

st.markdown("---")

st.subheader("Top Controversial Parent Posts")

if top_controversial is not None and len(top_controversial) > 0:
    st.dataframe(top_controversial.head(30), use_container_width=True, hide_index=True)
