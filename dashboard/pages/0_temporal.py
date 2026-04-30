import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from scipy import stats
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Temporal  MBG", page_icon=None, layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

st.title("Temporal Analysis")
st.caption("How discourse evolved over time  volume, sentiment shifts, weekly rhythms, and trend direction")
st.markdown("---")

@st.cache_data
def load():
    df = pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])
    df = df[df["date"] >= "2025-01-01"]
    df["hour_wib"] = (df["hour"] + 7) % 24
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    df["year_month"] = df["date"].dt.to_period("M")
    df["dayofweek"] = df["date"].dt.day_name()
    return df

df = load()

#  KPIs 
daily = df.groupby("date").size().reset_index(name="count")
busiest = daily.loc[daily["count"].idxmax()]
monthly_vol = df.groupby("month").size()
busiest_month = monthly_vol.idxmax()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Date Range", f"{df['date'].min().strftime('%b %Y')}  {df['date'].max().strftime('%b %Y')}")
c2.metric("Busiest Day", str(busiest["date"].date()), f"{int(busiest['count']):,} tweets")
c3.metric("Busiest Month", busiest_month.strftime("%b %Y"), f"{int(monthly_vol.max()):,} tweets")
c4.metric("Avg Tweets/Day", f"{daily['count'].mean():.0f}")
c5.metric("Days with Data", f"{len(daily):,}")

st.markdown("---")

#  1. Volume + sentiment stacked area 
st.markdown("### Volume and Sentiment Over Time")

tab1, tab2, tab3 = st.tabs(["Monthly", "Weekly", "Daily (last 6 months)"])

with tab1:
    monthly_sent = df.groupby(["month", "sentiment_normalized"]).size().unstack(fill_value=0)
    mp = monthly_sent.div(monthly_sent.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    FILL = {"negative": "rgba(231,76,60,0.6)", "neutral": "rgba(149,165,166,0.6)", "positive": "rgba(46,204,113,0.6)"}
    for s, color in COLORS.items():
        if s in mp.columns:
            fig.add_trace(go.Scatter(x=mp.index, y=mp[s], name=s.capitalize(),
                stackgroup="one", line=dict(color=color),
                fillcolor=FILL[s], hovertemplate="%{y:.1f}%"))
    fig.add_hline(y=50, line_dash="dot", line_color="white", opacity=0.4,
                  annotation_text="50%", annotation_font_color="white")
    fig.update_layout(yaxis_title="% of monthly tweets", hovermode="x unified",
                      height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    weekly_sent = df.groupby(["week", "sentiment_normalized"]).size().unstack(fill_value=0)
    wp = weekly_sent.div(weekly_sent.sum(axis=1), axis=0) * 100
    fig2 = go.Figure()
    for s, color in COLORS.items():
        if s in wp.columns:
            fig2.add_trace(go.Scatter(x=wp.index, y=wp[s], name=s.capitalize(),
                line=dict(color=color, width=1.5), hovertemplate="%{y:.1f}%"))
    fig2.update_layout(hovermode="x unified", yaxis_title="% of weekly tweets",
                       height=350, margin=dict(t=10, b=10))
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
                name=s.capitalize(), line=dict(color=color, width=2),
                hovertemplate="%{y:.1f}%"))
    fig3.update_layout(hovermode="x unified", yaxis_title="% (7-day rolling avg)",
                       height=350, margin=dict(t=10, b=10))
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

#  2. Trend direction (linear regression) 
st.markdown("### Negativity Trend")

monthly_neg = df.groupby("month").apply(
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
    fig4.add_hline(y=50, line_dash="dot", line_color="orange",
                   annotation_text="50% threshold")
    fig4.update_layout(yaxis_title="% Negative", hovermode="x unified",
                       height=320, margin=dict(t=10, b=10))
    st.plotly_chart(fig4, use_container_width=True)

with col2:
    direction = " INCREASING" if slope > 0 else " DECREASING"
    st.markdown(f"**Trend Direction:** {direction}")
    st.metric("Slope", f"{slope:+.2f} pp/month",
              help="Percentage points change per month")
    st.metric("R (fit quality)", f"{r**2:.3f}")
    st.metric("p-value", f"{p:.4f}", help="< 0.05 = statistically significant")
    if p < 0.05:
        st.error("Trend is **statistically significant**  this is not random noise.")
    else:
        st.info("Trend is not statistically significant.")
    months_to_60 = (60 - monthly_neg["pct_negative"].iloc[-1]) / slope if slope > 0 else None
    if months_to_60 and months_to_60 > 0:
        st.warning(f"At this rate, negativity hits **60%** in ~{months_to_60:.0f} months.")

st.markdown("---")

#  3. Day of week + hour heatmap 
st.markdown("### Posting Patterns")

col3, col4 = st.columns(2)
with col3:
    st.markdown("#### By Day of Week")
    dow_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = df.groupby("dayofweek").size().reindex(dow_order).reset_index()
    dow.columns = ["day", "count"]
    fig5 = px.bar(dow, x="day", y="count", color="count",
                  color_continuous_scale="Blues",
                  labels={"day": "Day", "count": "Tweets"})
    fig5.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig5, use_container_width=True)

with col4:
    st.markdown("#### By Hour (WIB)")
    st.caption("Peak at 6am  morning school news reaction")
    hourly = df.groupby("hour_wib").size().reset_index(name="count")
    fig6 = px.bar(hourly, x="hour_wib", y="count", color="count",
                  color_continuous_scale="Reds",
                  labels={"hour_wib": "Hour (WIB)", "count": "Tweets"})
    fig6.update_layout(height=280, margin=dict(t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig6, use_container_width=True)

# Day × Hour heatmap
st.markdown("#### Day × Hour Heatmap (WIB)")
heatmap = df.groupby(["dayofweek", "hour_wib"]).size().unstack(fill_value=0)
heatmap = heatmap.reindex(dow_order)
fig7 = px.imshow(heatmap, color_continuous_scale="Reds",
                 labels=dict(x="Hour (WIB)", y="Day", color="Tweets"),
                 aspect="auto")
fig7.update_layout(height=300, margin=dict(t=10, b=10))
st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

#  4. Cumulative negativity 
st.markdown("### Cumulative Sentiment Share Over Time")
st.caption("Shows how the overall balance has shifted as more tweets accumulated")

df_sorted = df.sort_values("date").reset_index(drop=True)
df_sorted["cum_neg"] = (df_sorted["sentiment_normalized"] == "negative").cumsum() / (df_sorted.index + 1) * 100
df_sorted["cum_pos"] = (df_sorted["sentiment_normalized"] == "positive").cumsum() / (df_sorted.index + 1) * 100
df_sorted["cum_neu"] = (df_sorted["sentiment_normalized"] == "neutral").cumsum() / (df_sorted.index + 1) * 100

# Sample every 500 rows for performance
sample = df_sorted.iloc[::500]
fig8 = go.Figure()
for col, color, name in [("cum_neg","#e74c3c","Negative"),
                          ("cum_pos","#2ecc71","Positive"),
                          ("cum_neu","#95a5a6","Neutral")]:
    fig8.add_trace(go.Scatter(x=sample["date"], y=sample[col],
                              name=name, line=dict(color=color, width=2)))
fig8.add_hline(y=50, line_dash="dot", line_color="white", opacity=0.3)
fig8.update_layout(yaxis_title="Cumulative %", hovermode="x unified",
                   height=320, margin=dict(t=10, b=10))
st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")

#  5. Month-over-month change 
st.markdown("### Month-over-Month Sentiment Change")

mom = monthly_neg.copy()
mom["prev"] = mom["pct_negative"].shift(1)
mom["change"] = mom["pct_negative"] - mom["prev"]
mom = mom.dropna()

fig9 = px.bar(mom, x="month", y="change",
              color=mom["change"].apply(lambda x: "Worse" if x > 0 else "Better"),
              color_discrete_map={"Worse": "#e74c3c", "Better": "#2ecc71"},
              labels={"month": "Month", "change": "Change in neg% (pp)", "color": ""})
fig9.update_layout(height=300, margin=dict(t=10, b=10), showlegend=True)
st.plotly_chart(fig9, use_container_width=True)
