import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from spaces_loader import load_with_fallback, load_reply_dataset

st.set_page_config(page_title="Overview  MBG", page_icon=None, layout="wide")
require_auth()

COLORS = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

st.title("MBG Discourse Overview")
st.caption("State of the discourse  volume, sentiment, topics, temporal patterns, and data freshness")
st.markdown("---")

@st.cache_data
def load_corpus():
    df, source, run_info = load_with_fallback("tweets_with_sentiment")
    if df is None:
        return None, None, None
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"] >= "2025-01-01"]
    df["hour_wib"] = (df["hour"] + 7) % 24
    df["dayofweek"] = df["date"].dt.day_name()
    return df, source, run_info

df, source, run_info = load_corpus()

ADIR = "/opt/mbg/data/analysis"
try:
    paper_stats = pd.read_csv(f"{ADIR}/paper_statistics_summary.csv").iloc[0]
except:
    paper_stats = None

reply_vol = load_reply_dataset("reply_daily_volume")

if df is None:
    st.error("Failed to load data")
    st.stop()

total = len(df)
dist = df["sentiment_normalized"].value_counts()
daily = df.groupby("date").size().reset_index(name="count")
busiest = daily.loc[daily["count"].idxmax()]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total Tweets", f"{total:,}")
c2.metric("Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,}")
c3.metric("Neutral", f"{dist.get('neutral',0)/total*100:.1f}%", f"{dist.get('neutral',0):,}")
c4.metric("Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,}")
c5.metric("Date Range", f"{df['date'].min().strftime('%b %y')} - {df['date'].max().strftime('%b %y')}")
c6.metric("Busiest Day", str(busiest["date"].date()), f"{int(busiest['count']):,}")

st.markdown("---")

st.subheader("Volume and Sentiment Over Time")

tab1, tab2, tab3 = st.tabs(["Monthly", "Weekly", "Daily (last 6 months)"])

with tab1:
    monthly = df.groupby([df["date"].dt.to_period("M"), "sentiment_normalized"]).size().unstack(fill_value=0)
    mp = monthly.div(monthly.sum(axis=1), axis=0) * 100
    mp.index = mp.index.to_timestamp()
    fig = go.Figure()
    FILL = {"negative": "rgba(231,76,60,0.6)", "neutral": "rgba(149,165,166,0.6)", "positive": "rgba(46,204,113,0.6)"}
    for s, color in COLORS.items():
        if s in mp.columns:
            fig.add_trace(go.Scatter(x=mp.index, y=mp[s], name=s.capitalize(),
                stackgroup="one", line=dict(color=color), fillcolor=FILL[s], hovertemplate="%{y:.1f}%"))
    fig.add_hline(y=50, line_dash="dot", line_color="white", opacity=0.4, annotation_text="50%")
    fig.update_layout(yaxis_title="% of monthly tweets", hovermode="x unified", height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    weekly = df.groupby([df["date"].dt.to_period("W").dt.start_time, "sentiment_normalized"]).size().unstack(fill_value=0)
    wp = weekly.div(weekly.sum(axis=1), axis=0) * 100
    fig2 = go.Figure()
    for s, color in COLORS.items():
        if s in wp.columns:
            fig2.add_trace(go.Scatter(x=wp.index, y=wp[s], name=s.capitalize(),
                line=dict(color=color, width=1.5), hovertemplate="%{y:.1f}%"))
    fig2.update_layout(hovermode="x unified", yaxis_title="% of weekly tweets", height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    cutoff = df["date"].max() - pd.Timedelta(days=180)
    recent = df[df["date"] >= cutoff]
    daily_sent = recent.groupby(["date", "sentiment_normalized"]).size().unstack(fill_value=0)
    dp = daily_sent.div(daily_sent.sum(axis=1), axis=0) * 100
    fig3 = go.Figure()
    for s, color in COLORS.items():
        if s in dp.columns:
            fig3.add_trace(go.Scatter(x=dp.index, y=dp[s].rolling(7).mean(),
                name=s.capitalize(), line=dict(color=color, width=2), hovertemplate="%{y:.1f}%"))
    fig3.update_layout(hovermode="x unified", yaxis_title="% (7-day rolling avg)", height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

st.subheader("Negativity Trend Analysis")

monthly_neg = df.groupby(df["date"].dt.to_period("M").dt.to_timestamp()).apply(
    lambda x: (x["sentiment_normalized"] == "negative").mean() * 100
).reset_index()
monthly_neg.columns = ["month", "pct_negative"]
monthly_neg["x"] = range(len(monthly_neg))

slope, intercept, r, p, _ = stats.linregress(monthly_neg["x"], monthly_neg["pct_negative"])
trend_line = intercept + slope * monthly_neg["x"]

col1, col2 = st.columns([2, 1])
with col1:
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(x=monthly_neg["month"], y=monthly_neg["pct_negative"],
                          name="Monthly neg%", marker_color="#e74c3c", opacity=0.7))
    fig4.add_trace(go.Scatter(x=monthly_neg["month"], y=trend_line,
                              name=f"Trend (slope={slope:+.2f}pp/month)",
                              line=dict(color="white", width=2, dash="dash")))
    fig4.add_hline(y=50, line_dash="dot", line_color="orange", annotation_text="50%")
    fig4.update_layout(yaxis_title="% Negative", hovermode="x unified", height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

with col2:
    direction = "INCREASING" if slope > 0 else "DECREASING"
    st.markdown(f"**Trend:** {direction}")
    st.metric("Slope", f"{slope:+.2f} pp/month")
    st.metric("R-squared", f"{r**2:.3f}")
    st.metric("p-value", f"{p:.4f}")
    if p < 0.05:
        st.error("Trend is **statistically significant**")
    else:
        st.info("Trend is not statistically significant")
    months_to_60 = (60 - monthly_neg["pct_negative"].iloc[-1]) / slope if slope > 0 else None
    if months_to_60 and months_to_60 > 0:
        st.warning(f"At this rate, negativity hits **60%** in ~{months_to_60:.0f} months")

st.markdown("---")

st.subheader("Posting Patterns")

col3, col4 = st.columns(2)
with col3:
    st.markdown("#### By Day of Week")
    dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow = df.groupby("dayofweek").size().reindex(dow_order).reset_index()
    dow.columns = ["day", "count"]
    fig5 = px.bar(dow, x="day", y="count", color="count",
                  color_continuous_scale="Blues", labels={"day": "Day", "count": "Tweets"})
    fig5.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

with col4:
    st.markdown("#### By Hour (WIB)")
    hourly = df.groupby("hour_wib").size().reset_index(name="count")
    fig6 = px.bar(hourly, x="hour_wib", y="count", color="count",
                  color_continuous_scale="Reds", labels={"hour_wib": "Hour (WIB)", "count": "Tweets"})
    fig6.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("#### Day  Hour Heatmap (WIB)")
heatmap = df.groupby(["dayofweek", "hour_wib"]).size().unstack(fill_value=0).reindex(dow_order)
fig7 = px.imshow(heatmap, color_continuous_scale="Reds",
                 labels=dict(x="Hour (WIB)", y="Day", color="Tweets"), aspect="auto")
fig7.update_layout(height=300, margin=dict(t=10, b=10))
st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

if reply_vol is not None and len(reply_vol) > 0:
    st.subheader("Reply Volume Over Time")
    reply_vol["date"] = pd.to_datetime(reply_vol["date"])
    reply_vol = reply_vol.sort_values("date")
    reply_vol["rolling_7d"] = reply_vol["reply_count"].rolling(7, min_periods=1).mean()

    fig_rv = go.Figure()
    fig_rv.add_trace(go.Bar(x=reply_vol["date"], y=reply_vol["reply_count"],
                            name="Daily", marker_color="rgba(52,152,219,0.4)"))
    fig_rv.add_trace(go.Scatter(x=reply_vol["date"], y=reply_vol["rolling_7d"],
                                name="7-day avg", line=dict(color="#3498db", width=2)))
    fig_rv.update_layout(hovermode="x unified", yaxis_title="Replies per day", height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig_rv, use_container_width=True)

    st.markdown("---")

if paper_stats is not None:
    st.subheader("Corpus Statistics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Tweets", f"{int(paper_stats['total_tweets']):,}")
    c2.metric("Negative", f"{paper_stats['pct_negative']}%")
    c3.metric("Neutral", f"{paper_stats['pct_neutral']}%")
    c4.metric("Positive", f"{paper_stats['pct_positive']}%")
    c5.metric("Topics Found", f"{int(paper_stats['n_topics'])}")
    c6.metric("Neg Amplification", "Yes" if paper_stats['negative_amplification_significant'] else "No")

    st.markdown("---")

st.subheader("Data Status")
col_s1, col_s2 = st.columns(2)
with col_s1:
    st.markdown(f"**Source:** {'DigitalOcean Spaces' if source == 'spaces' else 'Local files'}")
    if run_info:
        st.markdown(f"**Last Run:** `{run_info.get('run_id', 'unknown')}`")
        st.markdown(f"**Timestamp:** {run_info.get('timestamp', 'unknown')}")
    else:
        st.info("No run info available (local files)")
with col_s2:
    st.markdown(f"**Latest Tweet:** {df['date'].max().strftime('%Y-%m-%d %H:%M')}")
    st.markdown(f"**Reply Data:** {'Available' if reply_vol is not None else 'Not available'}")
