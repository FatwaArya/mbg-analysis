import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Engagement  MBG", page_icon=None, layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("Engagement and Virality")
st.caption("What content spreads, when people post, and which topics drive the most interaction")
st.markdown("---")

@st.cache_data
def load():
    df = pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])
    df = df[df["date"] >= "2025-01-01"]
    df["hour_wib"] = (df["hour"] + 7) % 24
    df["talk_amplify"] = df["reply_count"] / (df["retweet_count"] + 1)
    return df

df = load()

# KPIs
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Avg Engagement", f"{df['engagement_total'].mean():.0f}")
c2.metric("Median Engagement", f"{df['engagement_total'].median():.0f}")
c3.metric("Zero Engagement", f"{(df['engagement_total']==0).mean()*100:.1f}%")
c4.metric(">1k Engagement", f"{(df['engagement_total']>1000).sum():,}")
c5.metric("Max Engagement", f"{df['engagement_total'].max():,}")

st.markdown("---")

#  Row 1: volume + hourly 
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Daily Tweet Volume")
    daily = df.groupby("date").size().reset_index(name="count")
    fig = px.area(daily, x="date", y="count", color_discrete_sequence=["#3498db"])
    fig.update_layout(height=280, margin=dict(t=10,b=10), yaxis_title="Tweets/day")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Posting by Hour (WIB)")
    st.caption("Peak at 6am WIB  people react to morning school meal news")
    hourly = df.groupby("hour_wib").size().reset_index(name="count")
    fig2 = px.bar(hourly, x="hour_wib", y="count", color="count",
                  color_continuous_scale="Blues",
                  labels={"hour_wib":"Hour (WIB)","count":"Tweets"})
    fig2.update_layout(height=280, margin=dict(t=10,b=10), coloraxis_showscale=False)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

#  Row 2: query effectiveness 
st.markdown("#### Query Effectiveness  Volume, Negativity & Engagement")
st.caption("The food poisoning query has 70.8% negative sentiment. The gimmick/fake promise query: 85.9% negative.")

qe = df.groupby("query_raw").agg(
    total=("id","count"),
    avg_eng=("engagement_total","mean"),
    pct_neg=("sentiment_normalized", lambda x: (x=="negative").mean()*100),
    pct_pos=("sentiment_normalized", lambda x: (x=="positive").mean()*100),
    avg_rt=("retweet_count","mean"),
).round(1).reset_index()
qe["query_short"] = qe["query_raw"].str[:55] + ""
qe = qe.sort_values("total", ascending=False)

fig3 = go.Figure()
fig3.add_trace(go.Bar(x=qe["query_short"], y=qe["total"], name="Tweet count",
                      marker_color="#3498db", yaxis="y"))
fig3.add_trace(go.Scatter(x=qe["query_short"], y=qe["pct_neg"], name="% Negative",
                          mode="lines+markers", marker_color="#e74c3c", yaxis="y2"))
fig3.update_layout(
    yaxis=dict(title="Tweet count"),
    yaxis2=dict(title="% Negative", overlaying="y", side="right", range=[0,100]),
    hovermode="x unified", height=380, margin=dict(t=10,b=120),
    xaxis=dict(tickangle=-35)
)
st.plotly_chart(fig3, use_container_width=True)

st.dataframe(qe[["query_short","total","avg_eng","pct_neg","pct_pos","avg_rt"]].rename(columns={
    "query_short":"Query","total":"Tweets","avg_eng":"Avg Engagement",
    "pct_neg":"% Negative","pct_pos":"% Positive","avg_rt":"Avg Retweets"
}), use_container_width=True, hide_index=True)

st.markdown("---")

#  Row 3: scrape tab + engagement distribution 
col3, col4 = st.columns(2)
with col3:
    st.markdown("#### Top vs Latest Tab Comparison")
    st.caption("'Latest' tab captures more negative content (45.5% vs 37.6%)")
    tab_stats = df.groupby("scrape_tab").agg(
        tweets=("id","count"),
        avg_eng=("engagement_total","mean"),
        pct_neg=("sentiment_normalized", lambda x: (x=="negative").mean()*100),
        pct_pos=("sentiment_normalized", lambda x: (x=="positive").mean()*100),
    ).round(1).reset_index()
    st.dataframe(tab_stats, use_container_width=True, hide_index=True)

    fig4 = px.bar(tab_stats.melt(id_vars="scrape_tab", value_vars=["pct_neg","pct_pos"]),
                  x="scrape_tab", y="value", color="variable", barmode="group",
                  color_discrete_map={"pct_neg":"#e74c3c","pct_pos":"#2ecc71"},
                  labels={"scrape_tab":"Tab","value":"%","variable":""})
    fig4.update_layout(height=250, margin=dict(t=10,b=10))
    st.plotly_chart(fig4, use_container_width=True)

with col4:
    st.markdown("#### Engagement Distribution (log scale)")
    st.caption("Power law: a tiny % of posts get almost all the attention")
    fig5 = px.histogram(df[df["engagement_total"]>0], x="engagement_total",
                        color="sentiment_normalized", color_discrete_map=COLORS,
                        log_x=True, barmode="overlay", opacity=0.65,
                        labels={"engagement_total":"Engagement (log scale)"})
    fig5.update_layout(height=350, margin=dict(t=10,b=10))
    st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

#  Regional analysis 
st.markdown("#### Regional Sentiment  Java vs Outer Islands")
st.caption("Outer islands (Papua, NTT, Maluku) are 39% positive. Java is only 24% positive.")

regions = {
    "Java": "Jakarta|Jawa|Surabaya|Bandung|Semarang",
    "Outer Islands": "Papua|NTT|NTB|Maluku|Kalimantan|Sulawesi",
    "Sumatra": "Sumatera|Medan|Aceh|Padang|Palembang",
}
rows = []
for region, pattern in regions.items():
    sub = df[df["query_raw"].str.contains(pattern, na=False)]
    if len(sub):
        rows.append({"Region": region, "Tweets": len(sub),
                     "% Negative": round((sub["sentiment_normalized"]=="negative").mean()*100,1),
                     "% Positive": round((sub["sentiment_normalized"]=="positive").mean()*100,1),
                     "% Neutral":  round((sub["sentiment_normalized"]=="neutral").mean()*100,1),
                     "Avg Engagement": round(sub["engagement_total"].mean(),0)})
reg_df = pd.DataFrame(rows)
col5, col6 = st.columns([1,2])
with col5:
    st.dataframe(reg_df, use_container_width=True, hide_index=True)
with col6:
    fig6 = px.bar(reg_df.melt(id_vars="Region", value_vars=["% Negative","% Positive","% Neutral"]),
                  x="Region", y="value", color="variable", barmode="stack",
                  color_discrete_map={"% Negative":"#e74c3c","% Positive":"#2ecc71","% Neutral":"#95a5a6"},
                  labels={"value":"%","variable":""})
    fig6.update_layout(height=280, margin=dict(t=10,b=10))
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

#  Top 20 posts 
st.markdown("#### Top 20 Most Engaging Posts")
top = df.nlargest(20,"engagement_total")[
    ["text","sentiment_normalized","engagement_total","favorite_count","retweet_count","reply_count","date"]]
st.dataframe(top, use_container_width=True, hide_index=True)
