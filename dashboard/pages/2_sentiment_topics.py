import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_with_fallback, load_reply_dataset, filter_topics

st.set_page_config(page_title="Sentiment & Topics  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

st.title("Sentiment & Topics")
st.caption("What themes drive sentiment, how replies react, and which topics spark debate")
st.markdown("---")

@st.cache_data
def load_corpus():
    df, _, _ = load_with_fallback("tweets_with_sentiment")
    if df is None:
        return None
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= "2025-01-01"]
    return df

@st.cache_data
def load_topics():
    try:
        ti, _, _ = load_with_fallback("topic_info")
        ti = filter_topics(ti)
        df, _, _ = load_with_fallback("tweets_with_topics")
        if df is not None:
            df["date"] = pd.to_datetime(df["date"])
            df = df[df["date"] >= "2025-01-01"]
        return ti, df
    except:
        return None, None

df = load_corpus()
topic_info, df_topics = load_topics()

reply_topic_dist = load_reply_dataset("reply_topic_distribution")
topic_controversy = load_reply_dataset("topic_controversy_ranking")
topic_sent_shift = load_reply_dataset("topic_sentiment_shift")
sentiment_matrix = load_reply_dataset("reply_vs_parent_sentiment_matrix")
talk_amplify = load_reply_dataset("reply_talk_amplify")

if df is None:
    st.error("Failed to load data")
    st.stop()

total = len(df)
dist = df["sentiment_normalized"].value_counts()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tweets", f"{total:,}")
c2.metric("Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,}")
c3.metric("Neutral", f"{dist.get('neutral',0)/total*100:.1f}%", f"{dist.get('neutral',0):,}")
c4.metric("Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,}")

st.markdown("---")

st.subheader("Sentiment Distribution & Trend")

col1, col2 = st.columns([1, 2])
with col1:
    fig = px.pie(values=dist.values, names=dist.index,
                 color=dist.index, color_discrete_map=COLORS, hole=0.5)
    fig.update_traces(textinfo="percent+label", textfont_size=14)
    fig.update_layout(showlegend=False, margin=dict(t=10, b=10), height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    monthly = df.groupby([df["date"].dt.to_period("M"), "sentiment_normalized"]).size().unstack(fill_value=0)
    mp = monthly.div(monthly.sum(axis=1), axis=0) * 100
    mp.index = mp.index.to_timestamp()
    fig2 = go.Figure()
    for s, color in COLORS.items():
        if s in mp.columns:
            fig2.add_trace(go.Scatter(x=mp.index, y=mp[s], name=s.capitalize(),
                line=dict(color=color, width=2.5), hovertemplate="%{y:.1f}%"))
    fig2.add_hline(y=50, line_dash="dot", line_color="red", annotation_text="50% threshold")
    fig2.update_layout(hovermode="x unified", yaxis_title="% of tweets", height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.subheader("Sentiment by Topic")

if topic_info is not None and df_topics is not None and "sentiment_normalized" in df_topics.columns:
    valid = topic_info[topic_info["Topic"] != -1]
    top15 = valid.nlargest(15, "Count")["Topic"].tolist()
    id_to_name = dict(zip(valid["Topic"], valid["Name"].str[:40]))

    ts = df_topics[df_topics["topic_id"].isin(top15)].groupby(["topic_id", "sentiment_normalized"]).size().unstack(fill_value=0)
    ts_pct = ts.div(ts.sum(axis=1), axis=0) * 100
    ts_pct.index = [id_to_name.get(i, str(i)) for i in ts_pct.index]
    ts_pct = ts_pct.sort_values("negative", ascending=False)

    fig3 = px.bar(ts_pct.reset_index().melt(id_vars="topic_id"),
                  x="topic_id", y="value", color="sentiment_normalized",
                  color_discrete_map=COLORS, barmode="stack",
                  labels={"topic_id": "Topic", "value": "%", "sentiment_normalized": ""})
    fig3.update_layout(height=380, margin=dict(t=10, b=10), xaxis=dict(tickangle=-35))
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Topic Volume Ranking")
    st.dataframe(valid[["Topic", "Count", "Name"]].sort_values("Count", ascending=False).head(20),
                 use_container_width=True, hide_index=True)

st.markdown("---")

st.subheader("Parent  Reply Sentiment Flow")

if sentiment_matrix is not None and len(sentiment_matrix) > 0:
    labels = ["negative", "neutral", "positive"]
    label_colors = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}
    source_indices, target_indices, values = [], [], []
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
                             font_size=12, height=350, margin=dict(t=40, b=10))
    st.plotly_chart(fig_sankey, use_container_width=True)

st.markdown("---")

st.subheader("Topic  Reply Heatmap")

if reply_topic_dist is not None and len(reply_topic_dist) > 0:
    if topic_info is not None:
        valid = topic_info[topic_info["Topic"] != -1]
        id_to_name = dict(zip(valid["Topic"], valid["Name"].str[:30]))
        reply_topic_dist["topic_name"] = reply_topic_dist["topic_id"].map(id_to_name).fillna(reply_topic_dist["topic_id"].astype(str))
    else:
        reply_topic_dist["topic_name"] = reply_topic_dist["topic_id"].astype(str)

    heatmap_data = reply_topic_dist.pivot_table(
        index="topic_name", columns="sentiment_normalized", values="count", fill_value=0
    )
    fig_heat = px.imshow(heatmap_data, color_continuous_scale="RdYlGn_r",
                         labels=dict(x="Sentiment", y="Topic", color="Count"), aspect="auto")
    fig_heat.update_layout(height=400, margin=dict(t=10, b=10))
    st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

st.subheader("Talk vs Amplify by Sentiment")

if talk_amplify is not None and len(talk_amplify) > 0:
    fig_ta = px.bar(talk_amplify, x="sentiment_normalized", y="talk_amplify_ratio",
                    color="sentiment_normalized", color_discrete_map=COLORS,
                    labels={"sentiment_normalized": "Sentiment", "talk_amplify_ratio": "Reply / (RT+1)"})
    fig_ta.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig_ta, use_container_width=True)

st.markdown("---")

st.subheader("Model Confidence by Sentiment")
st.caption("Higher confidence = more reliable labels")

fig_conf = px.box(df, x="sentiment_normalized", y="sentiment_score",
                  color="sentiment_normalized", color_discrete_map=COLORS,
                  labels={"sentiment_normalized": "Sentiment", "sentiment_score": "Confidence Score"})
fig_conf.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
st.plotly_chart(fig_conf, use_container_width=True)
