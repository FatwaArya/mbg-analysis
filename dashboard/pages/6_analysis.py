import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth

st.set_page_config(page_title="Analysis  MBG", page_icon=None, layout="wide")
require_auth()

# Note: Analysis CSVs stay local-only (not versioned in Spaces)
DATA  = "/opt/mbg/data"
ADIR  = f"{DATA}/analysis"
COLORS = {"negative": "#e74c3c", "neutral": "#95a5a6", "positive": "#2ecc71"}

st.title("Research Analysis")
st.caption("Core findings from 107,375 tweets  Topic × Sentiment × Time  Framing  Amplification")
st.markdown("---")

#  Paper stats banner 
try:
    s = pd.read_csv(f"{ADIR}/paper_statistics_summary.csv").iloc[0]
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Total Tweets", f"{int(s['total_tweets']):,}")
    c2.metric("Negative", f"{s['pct_negative']}%")
    c3.metric("Neutral",  f"{s['pct_neutral']}%")
    c4.metric("Positive", f"{s['pct_positive']}%")
    c5.metric("Topics Found", f"{int(s['n_topics'])}")
    c6.metric("Negative Amplification", "Significant" if s['negative_amplification_significant'] else "Not significant")
    st.caption(f"Period: {s['date_from']}  {s['date_to']}")
except Exception:
    pass

st.markdown("---")

#  FINDING 1: Topic × Sentiment matrix 
st.markdown("## Finding 1  Which Topics Are Most Negative?")
st.caption("Corruption and political criticism dominate negativity. Food poisoning is the most negative *large* topic.")

try:
    tm = pd.read_csv(f"{ADIR}/topic_sentiment_matrix.csv", index_col=0)
    tm = tm[tm["total_tweets"] >= 100].sort_values("negative", ascending=False).head(20)
    tm["label"] = tm["topic_name"].str[:45]

    col1, col2 = st.columns([2,1])
    with col1:
        fig = px.bar(tm.reset_index(), x="label", y=["negative","neutral","positive"],
                     barmode="stack", color_discrete_map={
                         "negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"},
                     labels={"label":"Topic","value":"%","variable":"Sentiment"})
        fig.update_layout(height=420, margin=dict(t=10,b=10),
                          xaxis=dict(tickangle=-40), legend_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("**Top 10 most negative topics (100 tweets)**")
        st.dataframe(tm[["label","negative","total_tweets"]].rename(columns={
            "label":"Topic","negative":"% Neg","total_tweets":"Tweets"
        }).head(10).round(1), use_container_width=True, hide_index=True)
except Exception as e:
    st.warning(f"Topic sentiment matrix: {e}")

st.markdown("---")

#  FINDING 2: Topic amplification 
st.markdown("## Finding 2  Which Topics Spread the Furthest?")
st.caption("Political/corruption topics get 35× more retweets than average. Food poisoning spreads widely too.")

try:
    amp = pd.read_csv(f"{ADIR}/topic_amplification.csv", index_col=0)
    amp = amp[amp["tweet_count"] >= 100].sort_values("avg_rt", ascending=False).head(15)
    amp["label"] = amp["topic_name"].str[:40]

    col3, col4 = st.columns(2)
    with col3:
        fig2 = px.bar(amp, x="avg_rt", y="label", orientation="h",
                      color="pct_negative", color_continuous_scale="Reds",
                      labels={"avg_rt":"Avg Retweets","label":"Topic","pct_negative":"% Negative"})
        fig2.update_layout(height=400, margin=dict(t=10,b=10),
                           yaxis=dict(autorange="reversed"), coloraxis_colorbar_title="% Neg")
        st.plotly_chart(fig2, use_container_width=True)
    with col4:
        fig3 = px.scatter(amp, x="avg_rt", y="pct_negative", size="tweet_count",
                          text="label", color="pct_negative",
                          color_continuous_scale="Reds",
                          labels={"avg_rt":"Avg RT","pct_negative":"% Negative","tweet_count":"Volume"})
        fig3.update_traces(textposition="top center", textfont_size=9)
        fig3.update_layout(height=400, margin=dict(t=10,b=10), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
except Exception as e:
    st.warning(f"Amplification: {e}")

st.markdown("---")

#  FINDING 3: Topic sentiment shift 
st.markdown("## Finding 3  Which Topics Got More Negative Over Time?")
st.caption("Dairy/milk topic (+16.7pp) and general MBG discourse (+15.1pp) became significantly more negative.")

try:
    shift = pd.read_csv(f"{ADIR}/topic_sentiment_shift.csv")
    shift["label"] = shift["topic_name"].str[:40]
    shift = shift.sort_values("change_pp", ascending=False)

    col5, col6 = st.columns([2,1])
    with col5:
        fig4 = px.bar(shift, x="label", y="change_pp",
                      color=shift["change_pp"].apply(lambda x: "More negative" if x > 0 else "Less negative"),
                      color_discrete_map={"More negative":"#e74c3c","Less negative":"#2ecc71"},
                      labels={"label":"Topic","change_pp":"Change (pp)","color":""})
        fig4.add_hline(y=0, line_color="white", opacity=0.3)
        fig4.update_layout(height=350, margin=dict(t=10,b=10),
                           xaxis=dict(tickangle=-35), showlegend=True)
        st.plotly_chart(fig4, use_container_width=True)
    with col6:
        st.dataframe(shift[["label","early_neg_pct","recent_neg_pct","change_pp"]].rename(columns={
            "label":"Topic","early_neg_pct":"Early %","recent_neg_pct":"Recent %","change_pp":" pp"
        }), use_container_width=True, hide_index=True)
except Exception as e:
    st.warning(f"Sentiment shift: {e}")

st.markdown("---")

#  FINDING 4: Topic over time 
st.markdown("## Finding 4  How Did Topic Dominance Change?")
st.caption("Corruption topic (Topic 1) surged from 815  2,091 tweets/month in FebMar 2026  driving the negativity spike.")

try:
    tt = pd.read_csv(f"{ADIR}/topic_over_time_monthly.csv", index_col=0, parse_dates=True)
    fig5 = px.line(tt, labels={"value":"Tweets/month","variable":"Topic","index":"Month"})
    fig5.update_layout(height=380, margin=dict(t=10,b=10),
                       hovermode="x unified", legend_title="Topic")
    st.plotly_chart(fig5, use_container_width=True)
except Exception as e:
    st.warning(f"Topic over time: {e}")

st.markdown("---")

#  FINDING 5: Framing analysis 
st.markdown("## Finding 5  How Is MBG Being Framed?")
st.caption("22% positive support vs 19% operational criticism vs 5% political criticism. Political framing is 70.8% negative.")

try:
    fd = pd.read_csv(f"{ADIR}/framing_distribution.csv", index_col=0)
    fd.columns = ["count"]
    fs = pd.read_csv(f"{ADIR}/framing_sentiment.csv", index_col=0)

    col7, col8 = st.columns(2)
    with col7:
        st.markdown("**Framing distribution**")
        fig6 = px.pie(fd.reset_index(), values="count", names="frame",
                      color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
        fig6.update_layout(height=320, margin=dict(t=10,b=10))
        st.plotly_chart(fig6, use_container_width=True)
    with col8:
        st.markdown("**Sentiment within each frame**")
        fig7 = px.bar(fs.reset_index().melt(id_vars="frame"),
                      x="frame", y="value", color="sentiment_normalized",
                      color_discrete_map=COLORS, barmode="stack",
                      labels={"frame":"Frame","value":"%","sentiment_normalized":""})
        fig7.update_layout(height=320, margin=dict(t=10,b=10),
                           xaxis=dict(tickangle=-20))
        st.plotly_chart(fig7, use_container_width=True)
except Exception as e:
    st.warning(f"Framing: {e}")

st.markdown("---")

#  FINDING 6: Spike events 
st.markdown("## Finding 6  What Triggered the Discourse Spikes?")

spike_events = {
    "2026-02-13": ("420 tweets", "Prabowo publicly complained professors were criticising MBG. Triggered mass debate about academic freedom vs program defense."),
    "2025-09-18": ("372 tweets", "17 food poisoning cases across 10 provinces reported, 4,000+ students affected. Biggest health crisis moment for MBG."),
    "2026-01-06": ("294 tweets", "Aceh/West Sumatra taxpayer controversy  debate over whether regions that voted against Prabowo still fund MBG."),
}

for date, (vol, event) in spike_events.items():
    with st.expander(f"{date}  {vol}"):
        st.info(event)
        try:
            spike_df = pd.read_csv(f"{ADIR}/spike_event_tweets.csv", parse_dates=["date"])
            day_tweets = spike_df[spike_df["date"].dt.date == pd.Timestamp(date).date()]
            if len(day_tweets):
                st.dataframe(day_tweets[["text","sentiment_normalized","engagement_total","retweet_count"]]
                             .nlargest(5,"engagement_total"), use_container_width=True, hide_index=True)
        except Exception:
            pass

st.markdown("---")

#  Hypothesis confirmation 
st.markdown("## Hypothesis Confirmation")
hyps = [
    ("H1", "Food safety topics are most negative AND most amplified",
     "Food poisoning topic: 49.2% negative. Corruption topic: 60% negative. Both in top amplified topics."),
    ("H2", "Political/corruption topics have highest engagement per tweet",
     "Topic 34 (bencana/anggaran): avg 230 RT. Topic 1 (korupsi): 60% negative, 14,946 tweets."),
    ("H3", "Outer island topics cluster around distribution/access",
     "Topic 3 (Papua): 17.8% negative  most positive large topic. Outer islands 39% positive vs Java 24%."),
    ("H4", "Negativity surge traceable to specific growing topics",
     "Topic 1 (corruption) grew 815  2,091 tweets/month FebMar 2026, driving the 52%+ negativity."),
    ("H5", "Positive topics have low amplification",
     "Positive support framing: only 14.5% negative, but lowest avg engagement. Good news doesn't spread."),
]
for badge, title, evidence in hyps:
    with st.expander(f"{badge}  {title}"):
        st.success(evidence)
