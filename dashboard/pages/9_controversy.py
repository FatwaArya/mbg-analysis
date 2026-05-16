import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset, load_with_fallback, filter_topics

st.set_page_config(page_title="Controversy  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("Controversy Analysis")
st.caption("Which parent posts spark the most polarized debate?")
st.markdown("---")

controversy = load_reply_dataset("reply_controversy_scores")
cont_by_topic = load_reply_dataset("controversy_by_topic")
cont_over_time = load_reply_dataset("controversy_over_time")
top_controversial = load_reply_dataset("top_controversial_parents")
cont_vs_eng = load_reply_dataset("controversy_vs_engagement")
topic_info = load_with_fallback("topic_info")[0]

if controversy is None:
    st.error("Controversy data not available.")
    st.stop()

#  KPIs
c1,c2,c3,c4 = st.columns(4)
c1.metric("Parent Posts Analyzed", f"{len(controversy):,}")
c2.metric("Avg Controversy", f"{controversy['controversy_score'].mean():.3f}")
c3.metric("Highly Controversial (>0.4)", f"{(controversy['controversy_score']>0.4).sum():,}")
c4.metric("Max Controversy", f"{controversy['controversy_score'].max():.3f}")

st.markdown("---")

#  1. Controversy Distribution
st.markdown("### Controversy Score Distribution")
st.caption("0 = unanimous sentiment, 1 = perfectly split positive/negative")

fig = px.histogram(controversy, x="controversy_score", nbins=50,
                   color_discrete_sequence=["#3498db"],
                   labels={"controversy_score":"Controversy Score","count":"Parent Posts"})
fig.add_vline(x=controversy["controversy_score"].median(), line_dash="dash", line_color="red",
              annotation_text=f"Median: {controversy['controversy_score'].median():.3f}")
fig.update_layout(height=320, margin=dict(t=10,b=10), showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  2. Controversy Over Time
st.markdown("### Controversy Trend Over Time")
st.caption("7-day rolling average of controversy scores")

if cont_over_time is not None and len(cont_over_time) > 0:
    cont_over_time["date"] = pd.to_datetime(cont_over_time["date"])
    cont_over_time = cont_over_time.sort_values("date")
    cont_over_time["avg_controversy_7d"] = cont_over_time["avg_controversy"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cont_over_time["date"], y=cont_over_time["avg_controversy"],
                             name="Daily", line=dict(color="rgba(52,152,219,0.3)", width=1)))
    fig.add_trace(go.Scatter(x=cont_over_time["date"], y=cont_over_time["avg_controversy_7d"],
                             name="7-day avg", line=dict(color="#3498db", width=2)))
    fig.update_layout(hovermode="x unified", yaxis_title="Avg Controversy Score",
                      height=320, margin=dict(t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  3. Controversy by Topic
st.markdown("### Controversy by Topic")
st.caption("Which topics generate the most polarized replies?")

if cont_by_topic is not None and len(cont_by_topic) > 0:
    if topic_info is not None:
        cont_by_topic = cont_by_topic.merge(
            topic_info[["Topic", "Name"]].rename(columns={"Topic": "topic_id"}),
            on="topic_id", how="left"
        )
        cont_by_topic["topic_label"] = cont_by_topic.apply(
            lambda r: f"Topic {int(r['topic_id'])}: {r['Name'][:40]}" if pd.notna(r.get("Name")) else f"Topic {int(r['topic_id'])}",
            axis=1
        )
    else:
        cont_by_topic["topic_label"] = cont_by_topic["topic_id"].apply(lambda x: f"Topic {int(x)}")

    cont_by_topic = cont_by_topic.sort_values("avg_controversy", ascending=False)

    fig = px.bar(cont_by_topic.head(20), x="topic_label", y="avg_controversy",
                 color="avg_controversy", color_continuous_scale="Reds",
                 labels={"topic_label":"Topic","avg_controversy":"Avg Controversy"})
    fig.update_layout(xaxis_tickangle=-45, height=400, margin=dict(t=10,b=80), coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  4. Controversy vs Engagement
st.markdown("### Controversy vs Engagement")
st.caption("Does controversy drive more engagement?")

if cont_vs_eng is not None and len(cont_vs_eng) > 0:
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        fig = px.bar(cont_vs_eng, x="controversy_bin", y="avg_engagement",
                     color="avg_engagement", color_continuous_scale="Blues",
                     labels={"controversy_bin":"Controversy Range","avg_engagement":"Avg Engagement"})
        fig.update_layout(height=300, margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_e2:
        fig = px.bar(cont_vs_eng, x="controversy_bin", y="avg_replies",
                     color="avg_replies", color_continuous_scale="Oranges",
                     labels={"controversy_bin":"Controversy Range","avg_replies":"Avg Replies"})
        fig.update_layout(height=300, margin=dict(t=10,b=10), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  5. Top Controversial Parents
st.markdown("### Top 50 Most Controversial Parent Posts")

if top_controversial is not None and len(top_controversial) > 0:
    display_cols = ["parent_id", "controversy_score", "reply_count"]
    if "topic_id" in top_controversial.columns:
        display_cols.insert(2, "topic_id")
    if "date" in top_controversial.columns:
        display_cols.append("date")
    if "text" in top_controversial.columns:
        display_cols.append("text")

    st.dataframe(top_controversial.head(50)[display_cols], use_container_width=True, hide_index=True,
                 column_config={"text": st.column_config.TextColumn("Text", width="large")})
