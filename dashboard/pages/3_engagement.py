import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Engagement Patterns")
COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/tweets_with_sentiment.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

c1, c2 = st.columns(2)
with c1:
    st.subheader("Hourly Posting Pattern")
    hourly = df.groupby("hour").size().reset_index(name="count")
    st.plotly_chart(px.bar(hourly, x="hour", y="count"), use_container_width=True)
with c2:
    st.subheader("Daily Volume")
    daily = df.groupby("date").size().reset_index(name="count")
    st.plotly_chart(px.line(daily, x="date", y="count"), use_container_width=True)

st.subheader("Talk vs Amplify by Sentiment")
df["talk_amplify"] = df["reply_count"] / (df["retweet_count"] + 1)
ratio = df.groupby("sentiment_normalized")["talk_amplify"].mean().reset_index()
st.plotly_chart(px.bar(ratio, x="sentiment_normalized", y="talk_amplify",
                       color="sentiment_normalized", color_discrete_map=COLORS), use_container_width=True)

st.subheader("Top 20 Posts")
st.dataframe(df.nlargest(20, "engagement_total")[
    ["text", "engagement_total", "sentiment_normalized",
     "favorite_count", "retweet_count", "reply_count", "date"]],
    use_container_width=True)
