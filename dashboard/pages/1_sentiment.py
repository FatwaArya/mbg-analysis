import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.title("Sentiment Analysis")
COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}

@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/tweets_with_sentiment.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

st.subheader("Overall Distribution")
dist = df["sentiment_normalized"].value_counts()
st.plotly_chart(px.pie(values=dist.values, names=dist.index,
                       color=dist.index, color_discrete_map=COLORS), use_container_width=True)

st.subheader("Sentiment Trend Over Time")
try:
    st_time = pd.read_csv("data/analysis/sentiment_over_time.csv", index_col=0, parse_dates=True)
    fig2 = go.Figure()
    for col, color in COLORS.items():
        if col in st_time.columns:
            fig2.add_trace(go.Scatter(x=st_time.index, y=st_time[col],
                                      name=col.capitalize(), line=dict(color=color)))
    fig2.update_layout(yaxis_title="% of tweets", hovermode="x unified")
    st.plotly_chart(fig2, use_container_width=True)
except Exception:
    st.warning("Run sentiment analysis first.")

st.subheader("Sentiment vs Engagement")
eng = df.groupby("sentiment_normalized")["engagement_total"].mean().reset_index()
st.plotly_chart(px.bar(eng, x="sentiment_normalized", y="engagement_total",
                       color="sentiment_normalized", color_discrete_map=COLORS), use_container_width=True)

st.subheader("Filter Tweets")
lang = st.selectbox("Language", ["All", "id", "en"])
filtered = df if lang == "All" else df[df["detected_lang"] == lang]
st.dataframe(filtered[["text", "sentiment_normalized", "sentiment_score",
                        "engagement_total", "date"]]
             .sort_values("engagement_total", ascending=False).head(50),
             use_container_width=True)
