import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_reply_dataset, load_with_fallback, filter_topics

st.set_page_config(page_title="Topic x Reply  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("Topic x Reply Analysis")
st.caption("How do replies react to different topics? Which topics generate the most debate?")
st.markdown("---")

reply_topic_dist = load_reply_dataset("reply_topic_distribution")
topic_controversy = load_reply_dataset("topic_controversy_ranking")
topic_sent_shift = load_reply_dataset("topic_sentiment_shift")
topic_reply_ratio = load_reply_dataset("topic_reply_ratio")
topic_info = load_with_fallback("topic_info")[0]
topic_info_filtered = filter_topics(topic_info) if topic_info is not None else None

if reply_topic_dist is None:
    st.error("Topic reply data not available.")
    st.stop()

# Merge topic names
if topic_info_filtered is not None:
    topic_name_map = dict(zip(topic_info_filtered["Topic"], topic_info_filtered["Name"].str[:50]))
else:
    topic_name_map = {}

st.markdown("---")

#  1. Topic x Reply Sentiment Matrix
st.markdown("### Reply Sentiment by Parent Topic")
st.caption("How replies feel about each parent topic")

if reply_topic_dist is not None and len(reply_topic_dist) > 0:
    reply_topic_dist["topic_name"] = reply_topic_dist["topic_id"].map(
        lambda x: f"Topic {int(x)}: {topic_name_map.get(x, '')}" if pd.notna(x) else f"Topic {int(x)}"
    )

    pivot = reply_topic_dist.pivot_table(
        index="topic_name", columns="sentiment_normalized", values="reply_count", fill_value=0
    ).reset_index()
    pivot["total"] = pivot["negative"] + pivot["neutral"] + pivot["positive"]
    pivot = pivot.sort_values("total", ascending=False)

    pivot_pct = pivot.set_index("topic_name")[["negative","neutral","positive"]]
    pivot_pct = pivot_pct.div(pivot_pct.sum(axis=1), axis=0) * 100

    fig = px.imshow(pivot_pct.T, color_continuous_scale="RdYlGn_r",
                    aspect="auto", labels=dict(x="Topic", y="Sentiment", color="%"))
    fig.update_layout(height=400, margin=dict(t=10,b=80), xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  2. Topic Controversy Ranking
st.markdown("### Topic Controversy Ranking")
st.caption("Topics ranked by how polarized their replies are")

if topic_controversy is not None and len(topic_controversy) > 0:
    topic_controversy["topic_label"] = topic_controversy["topic_id"].apply(
        lambda x: f"Topic {int(x)}: {topic_name_map.get(x, '')}" if pd.notna(x) else f"Topic {int(x)}"
    )
    topic_controversy = topic_controversy.sort_values("avg_controversy", ascending=False)

    col_tc1, col_tc2 = st.columns(2)
    with col_tc1:
        fig = px.bar(topic_controversy.head(15), x="topic_label", y="avg_controversy",
                     color="avg_controversy", color_continuous_scale="Reds",
                     labels={"topic_label":"Topic","avg_controversy":"Avg Controversy"})
        fig.update_layout(xaxis_tickangle=-45, height=350, margin=dict(t=10,b=80), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_tc2:
        st.dataframe(topic_controversy[["topic_label", "avg_controversy", "median_controversy", "highly_controversial", "parent_count"]],
                     use_container_width=True, hide_index=True,
                     column_config={"topic_label": "Topic", "avg_controversy": "Avg", "median_controversy": "Median",
                                   "highly_controversial": "High (>0.4)", "parent_count": "Parents"})

st.markdown("---")

#  3. Reply Volume by Topic
st.markdown("### Reply Volume by Topic")
st.caption("Which parent topics generate the most replies?")

if topic_reply_ratio is not None and len(topic_reply_ratio) > 0:
    topic_reply_ratio["topic_label"] = topic_reply_ratio["topic_id"].apply(
        lambda x: f"Topic {int(x)}: {topic_name_map.get(x, '')}" if pd.notna(x) else f"Topic {int(x)}"
    )
    topic_reply_ratio = topic_reply_ratio.sort_values("total_replies", ascending=False)

    col_tr1, col_tr2 = st.columns(2)
    with col_tr1:
        fig = px.bar(topic_reply_ratio.head(15), x="topic_label", y="total_replies",
                     color="total_replies", color_continuous_scale="Blues",
                     labels={"topic_label":"Topic","total_replies":"Total Replies"})
        fig.update_layout(xaxis_tickangle=-45, height=350, margin=dict(t=10,b=80), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_tr2:
        fig = px.scatter(topic_reply_ratio, x="parent_count", y="avg_replies_per_parent",
                         size="total_replies", color="total_replies",
                         color_continuous_scale="Viridis", hover_name="topic_label",
                         labels={"parent_count":"Parent Posts","avg_replies_per_parent":"Avg Replies/Parent",
                                "total_replies":"Total Replies"})
        fig.update_layout(height=350, margin=dict(t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

#  4. Topic Sentiment Shift
st.markdown("### Topic Sentiment Shift (Parent  Reply)")
st.caption("How sentiment changes from parent to reply for each topic")

if topic_sent_shift is not None and len(topic_sent_shift) > 0:
    topic_sent_shift["topic_label"] = topic_sent_shift["topic_id"].apply(
        lambda x: f"Topic {int(x)}: {topic_name_map.get(x, '')}" if pd.notna(x) else f"Topic {int(x)}"
    )

    pivot_shift = topic_sent_shift.pivot_table(
        index="topic_label", columns="shift_direction", values="count", fill_value=0
    ).reset_index()
    pivot_shift["total"] = pivot_shift.drop(columns=["topic_label"]).sum(axis=1)
    pivot_shift = pivot_shift.sort_values("total", ascending=False)

    shift_cols = [c for c in pivot_shift.columns if c not in ["topic_label", "total"]]
    pivot_pct = pivot_shift.set_index("topic_label")[shift_cols]
    pivot_pct = pivot_pct.div(pivot_pct.sum(axis=1), axis=0) * 100

    fig = px.bar(pivot_pct.reset_index().melt(id_vars="topic_label"),
                 x="topic_label", y="value", color="shift_direction", barmode="stack",
                 labels={"topic_label":"Topic","value":"%","shift_direction":"Shift"},
                 color_discrete_sequence=px.colors.qualitative.Set3)
    fig.update_layout(xaxis_tickangle=-45, height=400, margin=dict(t=10,b=80))
    st.plotly_chart(fig, use_container_width=True)
