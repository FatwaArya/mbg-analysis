import streamlit as st
import pandas as pd

st.title("Tweet Explorer")

@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/tweets_with_topics.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

c1, c2, c3 = st.columns(3)
with c1:
    sent_filter = st.multiselect("Sentiment",
                                  ["positive", "negative", "neutral"],
                                  default=["positive", "negative", "neutral"])
with c2:
    lang_filter = st.multiselect("Language",
                                  df["detected_lang"].unique().tolist(), default=["id"])
with c3:
    date_range = st.date_input("Date range", [df["date"].min(), df["date"].max()])

filtered = df[
    (df["sentiment_normalized"].isin(sent_filter)) &
    (df["detected_lang"].isin(lang_filter)) &
    (df["date"] >= pd.Timestamp(date_range[0])) &
    (df["date"] <= pd.Timestamp(date_range[1]))
]

st.caption(f"Showing {len(filtered):,} tweets")
st.dataframe(filtered[["text", "sentiment_normalized", "topic_id",
                        "engagement_total", "date", "detected_lang"]]
             .sort_values("engagement_total", ascending=False), use_container_width=True)
