import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_with_fallback

st.set_page_config(page_title="Engagement & Virality  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

st.title("Engagement & Virality")
st.caption("What content spreads, when discourse explodes, and which topics drive interaction")
st.markdown("---")

@st.cache_data
def load():
    df, _, _ = load_with_fallback("tweets_with_sentiment")
    if df is None:
        return None
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= "2025-01-01"]
    df["hour_wib"] = (df["hour"] + 7) % 24
    df["talk_amplify"] = df["reply_count"] / (df["retweet_count"] + 1)
    return df

df = load()
if df is None:
    st.error("Failed to load data")
    st.stop()

total = len(df)
avg_eng = df[["favorite_count", "retweet_count", "reply_count"]].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Tweets", f"{total:,}")
c2.metric("Avg Likes", f"{avg_eng['favorite_count']:.0f}")
c3.metric("Avg Retweets", f"{avg_eng['retweet_count']:.0f}")
c4.metric("Avg Replies", f"{avg_eng['reply_count']:.0f}")

st.markdown("---")

st.subheader("Engagement by Sentiment")

col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Avg Engagement Metrics")
    eng = df.groupby("sentiment_normalized").agg(
        avg_likes=("favorite_count", "mean"),
        avg_retweets=("retweet_count", "mean"),
        avg_replies=("reply_count", "mean"),
    ).reset_index()
    fig1 = px.bar(eng.melt(id_vars="sentiment_normalized"),
                  x="sentiment_normalized", y="value", color="variable", barmode="group",
                  color_discrete_map={"avg_likes": "#f39c12", "avg_retweets": "#3498db", "avg_replies": "#9b59b6"},
                  labels={"sentiment_normalized": "Sentiment", "value": "Avg count", "variable": ""})
    fig1.update_layout(height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("#### Talk vs Amplify Ratio")
    st.caption("High = more debate. Low = passive sharing.")
    ta = df.groupby("sentiment_normalized")["talk_amplify"].mean().reset_index()
    fig2 = px.bar(ta, x="sentiment_normalized", y="talk_amplify",
                  color="sentiment_normalized", color_discrete_map=COLORS,
                  labels={"sentiment_normalized": "Sentiment", "talk_amplify": "Reply / (RT+1)"})
    fig2.update_layout(showlegend=False, height=300, margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

st.subheader("Engagement Distribution (Log Scale)")

col3, col4 = st.columns(2)
with col3:
    fig3 = px.histogram(df, x="favorite_count", nbins=50, log_x=True,
                        color_discrete_sequence=["#f39c12"],
                        labels={"favorite_count": "Likes (log)", "count": "Tweets"})
    fig3.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    fig4 = px.histogram(df, x="retweet_count", nbins=50, log_x=True,
                        color_discrete_sequence=["#3498db"],
                        labels={"retweet_count": "Retweets (log)", "count": "Tweets"})
    fig4.update_layout(height=300, margin=dict(t=10, b=10), showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

st.subheader("Temporal Spike Detection")

daily = df.groupby("date").agg(
    count=("id", "count"),
    neg_pct=("sentiment_normalized", lambda x: (x == "negative").mean() * 100),
    avg_engagement=("engagement_total", "mean")
).reset_index()
daily["rolling_7d"] = daily["count"].rolling(7, min_periods=1).mean()
daily["std_7d"] = daily["count"].rolling(7, min_periods=1).std()
daily["z_score"] = (daily["count"] - daily["rolling_7d"]) / daily["std_7d"].clip(lower=1)
daily["is_spike"] = daily["z_score"] > 2

spikes = daily[daily["is_spike"]]

col5, col6 = st.columns([3, 1])
with col5:
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(x=daily["date"], y=daily["count"],
                          name="Daily", marker_color="rgba(52,152,219,0.4)"))
    fig5.add_trace(go.Scatter(x=daily["date"], y=daily["rolling_7d"],
                              name="7-day avg", line=dict(color="#3498db", width=2)))
    if len(spikes) > 0:
        fig5.add_trace(go.Scatter(x=spikes["date"], y=spikes["count"],
                                  name="Spike", mode="markers",
                                  marker=dict(color="#e74c3c", size=10, symbol="x")))
    fig5.update_layout(hovermode="x unified", yaxis_title="Tweets per day", height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown(f"**Detected Spikes:** {len(spikes)}")
    if len(spikes) > 0:
        for _, spike in spikes.nlargest(10, "z_score").iterrows():
            st.markdown(f"**{spike['date'].strftime('%b %d')}**  {int(spike['count']):,} tweets (z={spike['z_score']:.1f})")

st.markdown("---")

st.subheader("Spike Sentiment Analysis")

if len(spikes) > 0:
    spike_dates = spikes["date"].tolist()
    spike_tweets = df[df["date"].isin(spike_dates)]
    normal_tweets = df[~df["date"].isin(spike_dates)]

    col7, col8 = st.columns(2)
    with col7:
        st.markdown("#### Spike Days vs Normal Days")
        spike_sent = spike_tweets["sentiment_normalized"].value_counts(normalize=True) * 100
        normal_sent = normal_tweets["sentiment_normalized"].value_counts(normalize=True) * 100
        comp = pd.DataFrame({"Spike Days": spike_sent, "Normal Days": normal_sent}).fillna(0)
        fig6 = px.bar(comp.reset_index().melt(id_vars="sentiment_normalized"),
                      x="sentiment_normalized", y="value", color="variable",
                      barmode="group", color_discrete_map={"Spike Days": "#e74c3c", "Normal Days": "#3498db"},
                      labels={"sentiment_normalized": "Sentiment", "value": "%", "variable": ""})
        fig6.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig6, use_container_width=True)

    with col8:
        st.markdown("#### Spike Engagement vs Normal")
        spike_eng = spike_tweets[["favorite_count", "retweet_count", "reply_count"]].mean()
        normal_eng = normal_tweets[["favorite_count", "retweet_count", "reply_count"]].mean()
        eng_comp = pd.DataFrame({"Spike Days": spike_eng, "Normal Days": normal_eng})
        fig7 = px.bar(eng_comp.reset_index().melt(id_vars="index"),
                      x="index", y="value", color="variable", barmode="group",
                      color_discrete_map={"Spike Days": "#e74c3c", "Normal Days": "#3498db"},
                      labels={"index": "Metric", "value": "Avg", "variable": ""})
        fig7.update_layout(height=300, margin=dict(t=10, b=10))
        st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

st.subheader("Top Viral Posts")

tab_neg, tab_pos, tab_neu = st.tabs(["Most Viral  Negative", "Most Viral  Positive", "Most Viral  Neutral"])
cols_show = ["text", "sentiment_score", "engagement_total", "favorite_count", "retweet_count", "reply_count", "date"]
for tab, sent in [(tab_neg, "negative"), (tab_pos, "positive"), (tab_neu, "neutral")]:
    with tab:
        st.dataframe(df[df["sentiment_normalized"] == sent].nlargest(20, "engagement_total")[cols_show],
                     use_container_width=True, hide_index=True)
