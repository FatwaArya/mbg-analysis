import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Topic Analysis")

@st.cache_data
def load_all():
    ti = pd.read_csv("data/processed/topic_info.csv")
    df = pd.read_csv("data/processed/tweets_with_topics.csv")
    df["date"] = pd.to_datetime(df["date"])
    tt = pd.read_csv("data/analysis/topic_over_time.csv", index_col=0, parse_dates=True)
    return ti, df, tt

try:
    topic_info, df, topic_time = load_all()
    valid = topic_info[topic_info["Topic"] != -1]

    st.subheader("Discovered Topics")
    st.dataframe(valid[["Topic", "Count", "Name"]].head(20), use_container_width=True)

    st.subheader("Topic Prevalence Over Time")
    top8 = valid.nlargest(8, "Count")["Topic"].astype(str).tolist()
    cols = [c for c in top8 if c in topic_time.columns]
    if cols:
        st.plotly_chart(px.line(topic_time[cols]), use_container_width=True)

    st.subheader("Topic Sentiment Breakdown")
    try:
        ts = pd.read_csv("data/analysis/topic_sentiment_breakdown.csv", index_col=0)
        st.plotly_chart(px.bar(ts, barmode="stack", color_discrete_map={
            "positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}),
            use_container_width=True)
    except Exception:
        st.info("Topic sentiment not yet available.")

    st.subheader("Browse by Topic")
    sel = st.selectbox("Topic", valid["Topic"].tolist(),
                       format_func=lambda x: f"Topic {x} - {valid[valid['Topic'] == x]['Name'].values[0]}")
    st.dataframe(df[df["topic_id"] == sel][["text", "engagement_total", "date",
                                             "sentiment_normalized"]]
                 .sort_values("engagement_total", ascending=False).head(20),
                 use_container_width=True)
except Exception as e:
    st.warning(f"Run topic modeling first. ({e})")
