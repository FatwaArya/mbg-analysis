import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_with_fallback, filter_topics

st.set_page_config(page_title="Topics  MBG", page_icon=None, layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

st.title("Topic Analysis")
st.caption("What themes dominate public discourse about MBG?")
st.markdown("---")

@st.cache_data
def load():
    ti, _, _ = load_with_fallback("topic_info")
    ti = filter_topics(ti)
    df, _, _ = load_with_fallback("tweets_with_topics")
    if ti is None or df is None:
        st.error("Failed to load data")
        st.stop()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= "2025-01-01"]
    return ti, df

try:
    topic_info, df = load()
    valid = topic_info[topic_info["Topic"] != -1].copy()

    #  Overview metrics 
    outliers = (df["topic_id"] == -1).sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Topics Discovered", len(valid))
    c2.metric("Tweets Assigned", f"{len(df)-outliers:,}")
    c3.metric("Outlier Tweets", f"{outliers:,}", f"{outliers/len(df)*100:.1f}% unassigned")

    st.markdown("---")

    #  Topic table + bar 
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### Topic Overview")
        st.dataframe(valid[["Topic", "Count", "Name"]].sort_values("Count", ascending=False),
                     use_container_width=True, hide_index=True)
    with col2:
        st.markdown("#### Top 10 by Volume")
        top10 = valid.nlargest(10, "Count")
        fig = px.bar(top10, x="Count", y="Name", orientation="h",
                     color="Count", color_continuous_scale="Blues")
        fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=10, b=10),
                          coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    #  Topic over time 
    st.markdown("#### Topic Prevalence Over Time")
    top8_ids = valid.nlargest(8, "Count")["Topic"].tolist()
    topic_time = (df[df["topic_id"].isin(top8_ids)]
                  .groupby(["date", "topic_id"]).size().unstack(fill_value=0))
    id_to_name = dict(zip(valid["Topic"], valid["Name"]))
    topic_time.columns = [id_to_name.get(c, str(c)) for c in topic_time.columns]
    fig2 = px.line(topic_time.rolling(7).mean(),
                   labels={"value": "Tweets (7-day avg)", "date": "Date"})
    fig2.update_layout(hovermode="x unified", legend_title="Topic")
    st.plotly_chart(fig2, use_container_width=True)

    #  Sentiment per topic 
    if "sentiment_normalized" in df.columns:
        st.markdown("---")
        st.markdown("#### Sentiment Breakdown per Topic")
        ts = (df[df["topic_id"].isin(top8_ids)]
              .groupby(["topic_id", "sentiment_normalized"]).size().unstack(fill_value=0))
        ts_pct = ts.div(ts.sum(axis=1), axis=0) * 100
        ts_pct.index = [id_to_name.get(i, str(i)) for i in ts_pct.index]
        fig3 = px.bar(ts_pct.reset_index().melt(id_vars="topic_id"),
                      x="topic_id", y="value", color="sentiment_normalized",
                      color_discrete_map=COLORS, barmode="stack",
                      labels={"topic_id": "Topic", "value": "%", "sentiment_normalized": "Sentiment"})
        fig3.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    #  Browse by topic 
    st.markdown("---")
    st.markdown("#### Browse Tweets by Topic")
    sel = st.selectbox("Select topic", valid["Topic"].tolist(),
                       format_func=lambda x: f"Topic {x}  {id_to_name.get(x,'')}")
    subset = df[df["topic_id"] == sel].nlargest(20, "engagement_total")
    cols = ["text", "engagement_total", "date"] + (["sentiment_normalized"] if "sentiment_normalized" in df.columns else [])
    st.dataframe(subset[cols], use_container_width=True, hide_index=True)

except Exception as e:
    st.warning(f"Topic data not yet available. Run topic modeling first. ({e})")
