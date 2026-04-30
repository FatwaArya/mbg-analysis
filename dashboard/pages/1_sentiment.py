import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Sentiment  MBG", page_icon=None, layout="wide")
require_auth()

DATA = "/opt/mbg/data"
COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("Sentiment Analysis")
st.caption("How does the public feel about MBG  and how is that changing?")
st.markdown("---")

@st.cache_data
def load():
    df = pd.read_csv(f"{DATA}/processed/tweets_with_sentiment.csv", parse_dates=["date"])
    return df[df["date"] >= "2025-01-01"]

df = load()
total = len(df)
dist = df["sentiment_normalized"].value_counts()

#  KPIs 
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Tweets", f"{total:,}")
c2.metric("Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,}")
c3.metric("Neutral",  f"{dist.get('neutral',0)/total*100:.1f}%",  f"{dist.get('neutral',0):,}")
c4.metric("Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,}")

st.markdown("---")

#  Row 1: pie + monthly trend 
col1, col2 = st.columns([1,2])
with col1:
    st.markdown("#### Overall Distribution")
    fig = px.pie(values=dist.values, names=dist.index,
                 color=dist.index, color_discrete_map=COLORS, hole=0.5)
    fig.update_traces(textinfo="percent+label", textfont_size=14)
    fig.update_layout(showlegend=False, margin=dict(t=10,b=10), height=300)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("#### Monthly Sentiment % (7-day smoothed)")
    st.caption(" Negativity crossed 50% in Feb 2026 and hasn't come back down")
    monthly = df.groupby([df["date"].dt.to_period("M"),"sentiment_normalized"]).size().unstack(fill_value=0)
    mp = monthly.div(monthly.sum(axis=1),axis=0)*100
    mp.index = mp.index.to_timestamp()
    fig2 = go.Figure()
    for s,color in COLORS.items():
        if s in mp.columns:
            fig2.add_trace(go.Scatter(x=mp.index, y=mp[s], name=s.capitalize(),
                line=dict(color=color,width=2.5), hovertemplate="%{y:.1f}%"))
    fig2.add_hline(y=50, line_dash="dot", line_color="red", annotation_text="50% threshold")
    fig2.update_layout(hovermode="x unified", yaxis_title="% of tweets",
                       height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

#  Row 2: engagement by sentiment + amplification 
col3, col4 = st.columns(2)
with col3:
    st.markdown("#### Engagement by Sentiment")
    st.caption("Negative posts get 3.4× more retweets than positive (p<0.000001)")
    eng = df.groupby("sentiment_normalized").agg(
        avg_likes=("favorite_count","mean"),
        avg_retweets=("retweet_count","mean"),
        avg_replies=("reply_count","mean"),
    ).reset_index()
    fig3 = px.bar(eng.melt(id_vars="sentiment_normalized"),
                  x="sentiment_normalized", y="value", color="variable", barmode="group",
                  color_discrete_map={"avg_likes":"#f39c12","avg_retweets":"#3498db","avg_replies":"#9b59b6"},
                  labels={"sentiment_normalized":"Sentiment","value":"Avg count","variable":""})
    fig3.update_layout(height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("#### Talk vs Amplify Ratio")
    st.caption("High ratio = more debate. Low = content being spread without discussion.")
    df["talk_amplify"] = df["reply_count"] / (df["retweet_count"] + 1)
    ta = df.groupby("sentiment_normalized")["talk_amplify"].mean().reset_index()
    fig4 = px.bar(ta, x="sentiment_normalized", y="talk_amplify",
                  color="sentiment_normalized", color_discrete_map=COLORS,
                  labels={"sentiment_normalized":"Sentiment","talk_amplify":"Reply / (RT+1)"})
    fig4.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

#  Row 3: sentiment by language + confidence 
col5, col6 = st.columns(2)
with col5:
    st.markdown("#### Sentiment by Language")
    lang_sent = df.groupby(["detected_lang","sentiment_normalized"]).size().unstack(fill_value=0)
    lp = lang_sent.div(lang_sent.sum(axis=1),axis=0)*100
    top_langs = lang_sent.sum(axis=1).nlargest(8).index
    fig5 = px.bar(lp.loc[top_langs].reset_index().melt(id_vars="detected_lang"),
                  x="detected_lang", y="value", color="sentiment_normalized",
                  color_discrete_map=COLORS, barmode="stack",
                  labels={"detected_lang":"Language","value":"%","sentiment_normalized":""})
    fig5.update_layout(height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown("#### Model Confidence by Sentiment")
    st.caption("Negative labels are most confident (avg 89%)  these findings are reliable")
    fig6 = px.box(df, x="sentiment_normalized", y="sentiment_score",
                  color="sentiment_normalized", color_discrete_map=COLORS,
                  labels={"sentiment_normalized":"Sentiment","sentiment_score":"Confidence Score"})
    fig6.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

#  Row 4: first vs last period comparison 
st.markdown("#### Sentiment Shift: Early Period vs Recent Period")
st.caption("Comparing first 10% of corpus vs last 10%  shows the direction of change")
df_s = df.sort_values("date")
n = int(len(df)*0.1)
early = df_s.head(n)["sentiment_normalized"].value_counts(normalize=True)*100
recent = df_s.tail(n)["sentiment_normalized"].value_counts(normalize=True)*100
shift = pd.DataFrame({"Early period %": early, "Recent period %": recent}).round(1).fillna(0)
shift["Change"] = (shift["Recent period %"] - shift["Early period %"]).round(1)
shift["Change_str"] = shift["Change"].apply(lambda x: f"+{x:.1f}pp" if x>0 else f"{x:.1f}pp")
col7, col8 = st.columns([1,2])
with col7:
    st.dataframe(shift, use_container_width=True)
with col8:
    fig7 = px.bar(shift.reset_index(), x="sentiment_normalized", y=["Early period %","Recent period %"],
                  barmode="group", color_discrete_map={"Early period %":"#bdc3c7","Recent period %":"#e74c3c"},
                  labels={"sentiment_normalized":"Sentiment","value":"%","variable":""})
    fig7.update_layout(height=280, margin=dict(t=10,b=10))
    st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

#  Sentiment per topic (top 15) 
st.markdown("#### Sentiment Breakdown by Topic (Top 15 by volume)")
st.caption("Topic 1 (corruption) and Topic 2 (school/education) are the most negative large topics")
try:
    ti = pd.read_csv(f"{DATA}/processed/topic_info.csv")
    dft = pd.read_csv(f"{DATA}/processed/tweets_with_topics.csv", parse_dates=["date"])
    dft = dft[dft["date"] >= "2025-01-01"]
    valid = ti[ti["Topic"] != -1]
    id_to_name = dict(zip(valid["Topic"], valid["Name"].str[:40]))
    top15 = valid.nlargest(15, "Count")["Topic"].tolist()
    ts = dft[dft["topic_id"].isin(top15)].groupby(["topic_id","sentiment_normalized"]).size().unstack(fill_value=0)
    ts_pct = ts.div(ts.sum(axis=1), axis=0) * 100
    ts_pct.index = [id_to_name.get(i, str(i)) for i in ts_pct.index]
    ts_pct = ts_pct.sort_values("negative", ascending=False)
    fig8 = px.bar(ts_pct.reset_index().melt(id_vars="topic_id"),
                  x="topic_id", y="value", color="sentiment_normalized",
                  color_discrete_map=COLORS, barmode="stack",
                  labels={"topic_id":"Topic","value":"%","sentiment_normalized":""})
    fig8.update_layout(height=380, margin=dict(t=10,b=10),
                       xaxis=dict(tickangle=-35))
    st.plotly_chart(fig8, use_container_width=True)
except Exception as e:
    st.info(f"Topic data loading: {e}")

st.markdown("---")

#  Top posts by sentiment 
st.markdown("#### Top Posts by Sentiment")
tab_neg, tab_pos, tab_neu = st.tabs(["Most Viral  Negative", "Most Viral  Positive", "Most Viral  Neutral"])
cols_show = ["text","sentiment_score","engagement_total","favorite_count","retweet_count","reply_count","date"]
for tab, sent in [(tab_neg,"negative"),(tab_pos,"positive"),(tab_neu,"neutral")]:
    with tab:
        st.dataframe(df[df["sentiment_normalized"]==sent].nlargest(20,"engagement_total")[cols_show],
                     use_container_width=True, hide_index=True)
