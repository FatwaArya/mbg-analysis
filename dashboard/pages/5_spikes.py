import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Spikes · MBG", page_icon="⚡", layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("⚡ Temporal Spike Analysis")
st.caption("When did discourse explode — and what drove it?")
st.markdown("---")

@st.cache_data
def load():
    return pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])

df = load()

# Compute spikes
daily = df.groupby("date").agg(
    tweet_count=("id","count"),
    total_engagement=("engagement_total","sum"),
    avg_engagement=("engagement_total","mean"),
    pct_negative=("sentiment_normalized", lambda x: (x=="negative").mean()*100),
).reset_index()
daily["roll_mean"] = daily["tweet_count"].rolling(7,min_periods=1).mean()
daily["roll_std"]  = daily["tweet_count"].rolling(7,min_periods=1).std().fillna(1)
daily["z_score"]   = (daily["tweet_count"] - daily["roll_mean"]) / daily["roll_std"]
daily["is_spike"]  = daily["z_score"] > 2.0
spikes = daily[daily["is_spike"]].sort_values("tweet_count", ascending=False)

# KPIs
c1,c2,c3,c4 = st.columns(4)
c1.metric("Spike Days Detected", len(spikes))
if len(spikes):
    peak = spikes.iloc[0]
    c2.metric("Peak Day", str(peak["date"].date()))
    c3.metric("Peak Volume", f"{int(peak['tweet_count']):,} tweets")
    c4.metric("Spike Day Neg%", f"{spikes['pct_negative'].mean():.1f}%",
              f"vs {daily['pct_negative'].mean():.1f}% overall")

st.markdown("---")

# ── Main volume chart ─────────────────────────────────────────────────────────
st.markdown("#### Daily Tweet Volume with Spike Detection (z-score > 2)")
fig = go.Figure()
fig.add_trace(go.Scatter(x=daily["date"], y=daily["tweet_count"],
    name="Daily tweets", line=dict(color="#3498db", width=1.5), fill="tozeroy",
    fillcolor="rgba(52,152,219,0.1)"))
fig.add_trace(go.Scatter(x=daily["date"], y=daily["roll_mean"],
    name="7-day avg", line=dict(color="#f39c12", dash="dash", width=2)))
fig.add_trace(go.Scatter(x=spikes["date"], y=spikes["tweet_count"],
    mode="markers", name="⚡ Spike",
    marker=dict(color="#e74c3c", size=14, symbol="star"),
    text=spikes["date"].dt.strftime("%b %d %Y"),
    hovertemplate="<b>%{text}</b><br>%{y} tweets<extra></extra>"))
fig.update_layout(hovermode="x unified", yaxis_title="Tweets per day",
                  height=350, margin=dict(t=10,b=10))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Spike table + sentiment on spike days ─────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Spike Days Detail")
    st.dataframe(spikes[["date","tweet_count","z_score","total_engagement","pct_negative"]]
                 .assign(z_score=lambda d: d["z_score"].round(2),
                         pct_negative=lambda d: d["pct_negative"].round(1))
                 .reset_index(drop=True),
                 use_container_width=True, hide_index=True)

with col2:
    st.markdown("#### Sentiment: Spike Days vs Normal Days")
    df["is_spike_day"] = df["date"].isin(spikes["date"].values)
    spike_s  = df[df["is_spike_day"]]["sentiment_normalized"].value_counts(normalize=True)*100
    normal_s = df[~df["is_spike_day"]]["sentiment_normalized"].value_counts(normalize=True)*100
    cmp = pd.DataFrame({"Spike days": spike_s, "Normal days": normal_s}).round(1).fillna(0)
    fig2 = px.bar(cmp.reset_index().melt(id_vars="sentiment_normalized"),
                  x="sentiment_normalized", y="value", color="variable",
                  barmode="group",
                  color_discrete_map={"Spike days":"#e74c3c","Normal days":"#3498db"},
                  labels={"sentiment_normalized":"Sentiment","value":"%","variable":""})
    fig2.update_layout(height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── What drove spikes ─────────────────────────────────────────────────────────
st.markdown("#### What Topics Drove Spike Days?")
spike_tweets = df[df["is_spike_day"]]
col3, col4 = st.columns(2)
with col3:
    st.markdown("**Top queries on spike days**")
    qv = spike_tweets["query_raw"].value_counts().head(8).reset_index()
    qv.columns = ["query","count"]
    qv["query"] = qv["query"].str[:60] + "..."
    fig3 = px.bar(qv, x="count", y="query", orientation="h",
                  color_discrete_sequence=["#e74c3c"])
    fig3.update_layout(yaxis=dict(autorange="reversed"), height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("**Top posts on spike days**")
    top_spike = spike_tweets.nlargest(10,"engagement_total")[
        ["text","sentiment_normalized","engagement_total","date"]]
    st.dataframe(top_spike, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Negativity over time with spike markers ───────────────────────────────────
st.markdown("#### Daily Negativity % with Spike Markers")
fig4 = go.Figure()
fig4.add_trace(go.Scatter(x=daily["date"], y=daily["pct_negative"].rolling(7).mean(),
    name="Neg% (7-day avg)", line=dict(color="#e74c3c", width=2)))
fig4.add_trace(go.Scatter(x=spikes["date"], y=spikes["pct_negative"],
    mode="markers", name="Spike days",
    marker=dict(color="#c0392b", size=10, symbol="star")))
fig4.add_hline(y=50, line_dash="dot", line_color="gray", annotation_text="50%")
fig4.update_layout(hovermode="x unified", yaxis_title="% Negative tweets",
                   height=300, margin=dict(t=10,b=10))
st.plotly_chart(fig4, use_container_width=True)
