import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.title("Temporal Spike Analysis")

@st.cache_data
def load_data():
    daily = pd.read_csv("/opt/mbg/data/analysis/daily_volume_spikes.csv", parse_dates=["date"])
    top   = pd.read_csv("/opt/mbg/data/analysis/top_posts_spike_days.csv", parse_dates=["date"])
    return daily, top

try:
    daily, top_spike = load_data()
    spikes = daily[daily["is_spike"]]

    # ── Volume + spike markers ────────────────────────────────────────────────
    st.subheader("Daily Tweet Volume with Spike Detection")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["tweet_count"],
                             name="Daily tweets", line=dict(color="#3498db")))
    fig.add_trace(go.Scatter(x=daily["date"], y=daily["rolling_mean"],
                             name="7-day avg", line=dict(color="#95a5a6", dash="dash")))
    fig.add_trace(go.Scatter(x=spikes["date"], y=spikes["tweet_count"],
                             mode="markers", name="Spike",
                             marker=dict(color="#e74c3c", size=10, symbol="star")))
    fig.update_layout(hovermode="x unified", yaxis_title="Tweets")
    st.plotly_chart(fig, use_container_width=True)

    # ── Spike stats ───────────────────────────────────────────────────────────
    st.subheader(f"Spike Days ({len(spikes)} detected, z-score > 2)")
    st.dataframe(
        spikes[["date", "tweet_count", "z_score", "total_engagement", "total_retweets"]]
        .sort_values("tweet_count", ascending=False)
        .assign(z_score=lambda d: d["z_score"].round(2))
        .reset_index(drop=True),
        use_container_width=True
    )

    # ── Engagement on spike vs normal ─────────────────────────────────────────
    st.subheader("Spike vs Normal Day Engagement")
    try:
        eng = pd.read_csv("/opt/mbg/data/analysis/spike_vs_normal_engagement.csv", index_col=0)
        st.dataframe(eng, use_container_width=True)
    except Exception:
        pass

    # ── Sentiment comparison ──────────────────────────────────────────────────
    st.subheader("Sentiment: Spike vs Normal Days")
    try:
        sent = pd.read_csv("/opt/mbg/data/analysis/spike_sentiment_comparison.csv", index_col=0)
        COLORS = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"}
        fig2 = px.bar(sent.reset_index().rename(columns={"index": "sentiment"}),
                      x="sentiment", y=["spike_%", "normal_%"], barmode="group",
                      color_discrete_map={"spike_%": "#e74c3c", "normal_%": "#3498db"})
        st.plotly_chart(fig2, use_container_width=True)
    except Exception:
        st.info("Run sentiment analysis first to see this chart.")

    # ── Top posts on spike days ───────────────────────────────────────────────
    st.subheader("Top Posts on Spike Days")
    st.dataframe(top_spike[["text", "date", "engagement_total", "retweet_count", "reply_count"]]
                 .sort_values("engagement_total", ascending=False),
                 use_container_width=True)

except Exception as e:
    st.warning(f"Run temporal_spike_analysis.py first. ({e})")
