import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from auth import require_auth
from io import StringIO

st.set_page_config(page_title="Replies  MBG", page_icon=None, layout="wide")
require_auth()

DATA = "/opt/mbg/data"
BUCKET = "s3://mbg-scraper-network-20260419071440/output"
COLORS = {"negative":"#e74c3c","neutral":"#95a5a6","positive":"#2ecc71"}

st.title("Reply Analysis")
st.caption("How replies react to parent posts  sentiment shift, controversy, and debate depth")
st.markdown("---")

def run_s3cmd(args):
    try:
        result = subprocess.run(["s3cmd"] + args, capture_output=True, text=True, timeout=30)
        return result.stdout if result.returncode == 0 else None
    except:
        return None

@st.cache_data(ttl=600)
def load_reply_sentiment():
    local = f"{DATA}/output/replies_with_sentiment.csv"
    if os.path.exists(local):
        return pd.read_csv(local, parse_dates=["date"])
    output = run_s3cmd(["get", f"{BUCKET}/replies_with_sentiment.csv", "-"])
    if output:
        return pd.read_csv(StringIO(output), parse_dates=["date"])
    return None

@st.cache_data(ttl=600)
def load_reply_tree():
    local = f"{DATA}/output/reply_tree.csv"
    if os.path.exists(local):
        return pd.read_csv(local)
    output = run_s3cmd(["get", f"{BUCKET}/reply_tree.csv", "-"])
    if output:
        return pd.read_csv(StringIO(output))
    return None

@st.cache_data(ttl=600)
def load_analysis(name):
    local = f"{DATA}/output/analysis/{name}"
    if os.path.exists(local):
        return pd.read_csv(local)
    output = run_s3cmd(["get", f"{BUCKET}/analysis/{name}", "-"])
    if output:
        return pd.read_csv(StringIO(output))
    return None

replies = load_reply_sentiment()
tree = load_reply_tree()

if replies is None:
    st.error("Reply data not available. Run the reply pipeline first.")
    st.stop()

total = len(replies)
dist = replies["sentiment_normalized"].value_counts()

#  KPIs
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Replies", f"{total:,}")
c2.metric("Negative", f"{dist.get('negative',0)/total*100:.1f}%", f"{dist.get('negative',0):,}")
c3.metric("Neutral",  f"{dist.get('neutral',0)/total*100:.1f}%",  f"{dist.get('neutral',0):,}")
c4.metric("Positive", f"{dist.get('positive',0)/total*100:.1f}%", f"{dist.get('positive',0):,}")
c5.metric("Unique Parents", f"{replies['parent_id'].nunique():,}")

st.markdown("---")

#  1. Sentiment by depth
st.markdown("### Reply Depth vs Sentiment")
st.caption("Depth-1 = direct reply to parent. Depth-2 = reply to another reply.")

depth_sent = replies.groupby(["depth", "sentiment_normalized"]).size().reset_index(name="count")
depth_sent["depth_label"] = depth_sent["depth"].map({0:"unknown", 1:"depth-1 (→ parent)", 2:"depth-2 (→ reply)"})

fig1 = px.bar(depth_sent, x="depth_label", y="count", color="sentiment_normalized",
              color_discrete_map=COLORS, barmode="group",
              labels={"depth_label":"Depth","count":"Replies","sentiment_normalized":""})
fig1.update_layout(height=320, margin=dict(t=10,b=10))
st.plotly_chart(fig1, use_container_width=True)

# Depth sentiment table
col_d1, col_d2 = st.columns(2)
for col, d, label in [(col_d1, 1, "Depth-1"), (col_d2, 2, "Depth-2")]:
    with col:
        sub = replies[replies["depth"]==d]
        if len(sub) > 0:
            ddist = sub["sentiment_normalized"].value_counts(normalize=True) * 100
            st.metric(label, f"{len(sub):,} replies")
            for s in ["negative","neutral","positive"]:
                st.caption(f"  {'🔴' if s=='negative' else '🟢' if s=='positive' else '⚪'} {s.capitalize()}: {ddist.get(s,0):.1f}%")

st.markdown("---")

#  2. Sentiment shift (if tree has parent_sentiment)
if tree is not None and "parent_sentiment" in tree.columns:
    st.markdown("### Sentiment Shift: Parent → Reply")
    st.caption("How sentiment changes from the original post to its replies")

    shift = tree[["parent_sentiment", "reply_sentiment", "depth"]].dropna()
    shift["shift_label"] = shift.apply(
        lambda r: "same" if r["parent_sentiment"] == r["reply_sentiment"]
        else f"{r['parent_sentiment']}→{r['reply_sentiment']}",
        axis=1
    )

    # Overall shift
    shift_summary = shift.groupby("shift_label").size().reset_index(name="count")
    shift_summary = shift_summary.sort_values("count", ascending=False)

    fig2 = px.bar(shift_summary, x="shift_label", y="count",
                  color=shift_summary["shift_label"].apply(
                      lambda x: "same" if x=="same" else "changed"
                  ),
                  color_discrete_map={"same":"#2ecc71","changed":"#e74c3c"},
                  labels={"shift_label":"Shift","count":"Replies","color":""})
    fig2.update_layout(xaxis_tickangle=-30, height=320, margin=dict(t=10,b=10), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    # Shift by depth
    col_s1, col_s2 = st.columns(2)
    for col, d, label in [(col_s1, 1, "Depth-1"), (col_s2, 2, "Depth-2")]:
        with col:
            st.markdown(f"#### {label}")
            dshift = shift[shift["depth"]==d].groupby("shift_label").size().reset_index(name="count")
            dshift = dshift.sort_values("count", ascending=False).head(6)
            st.dataframe(dshift, use_container_width=True, hide_index=True)

    st.markdown("---")

#  3. Controversy scores
if tree is not None:
    st.markdown("### Parent Post Controversy")
    st.caption("High controversy = parent attracts both positive AND negative replies. Low = one-sided reaction.")

    controversy = tree.groupby("parent_id")["reply_sentiment"].agg(
        controversy_score=lambda s: min(
            (s=="positive").mean(), (s=="negative").mean()
        ) * 2,
        reply_count="count"
    ).reset_index()

    fig3 = px.histogram(controversy, x="controversy_score", nbins=50,
                        color_discrete_sequence=["#3498db"],
                        labels={"controversy_score":"Controversy Score","count":"Parent Posts"})
    fig3.update_layout(height=300, margin=dict(t=10,b=10), showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Avg Controversy", f"{controversy['controversy_score'].mean():.3f}")
    col_c2.metric("Median", f"{controversy['controversy_score'].median():.3f}")
    col_c3.metric("Max", f"{controversy['controversy_score'].max():.3f}")

    st.markdown("---")

#  4. Talk vs amplify
st.markdown("### Talk vs Amplify by Sentiment")
st.caption("Reply/(RT+1) ratio. High = more debate. Low = content spread without discussion.")

replies["talk_amplify"] = replies["reply_count"] / (replies["retweet_count"] + 1)
ta = replies.groupby("sentiment_normalized")["talk_amplify"].agg(["mean","median"]).reset_index()
ta.columns = ["sentiment","mean_ratio","median_ratio"]

col_t1, col_t2 = st.columns(2)
with col_t1:
    fig4 = px.bar(ta, x="sentiment", y="mean_ratio", color="sentiment",
                  color_discrete_map=COLORS,
                  labels={"sentiment":"Sentiment","mean_ratio":"Avg Reply/(RT+1)"})
    fig4.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig4, use_container_width=True)

with col_t2:
    fig5 = px.box(replies, x="sentiment_normalized", y="talk_amplify",
                  color="sentiment_normalized", color_discrete_map=COLORS,
                  labels={"sentiment_normalized":"Sentiment","talk_amplify":"Reply/(RT+1)"})
    fig5.update_layout(showlegend=False, height=300, margin=dict(t=10,b=10))
    st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

#  5. Most replied parents
if tree is not None:
    st.markdown("### Top 20 Most Replied Parent Posts")

    most_replied = tree.groupby("parent_id").agg(
        reply_count=("reply_id","count"),
        avg_reply_score=("reply_sentiment_score","mean"),
        controversy=("reply_sentiment", lambda s: min(
            (s=="positive").mean(), (s=="negative").mean()
        ) * 2)
    ).sort_values("reply_count", ascending=False).head(20).reset_index()

    if "parent_sentiment" in tree.columns:
        parent_sent = tree.groupby("parent_id")["parent_sentiment"].first().reset_index()
        most_replied = most_replied.merge(parent_sent, on="parent_id", how="left")

    st.dataframe(most_replied, use_container_width=True, hide_index=True)

st.markdown("---")

#  6. Reply sentiment over time
st.markdown("### Reply Sentiment Over Time (Monthly)")

replies["month"] = replies["date"].dt.to_period("M").dt.to_timestamp()
monthly = replies.groupby(["month","sentiment_normalized"]).size().unstack(fill_value=0)
mp = monthly.div(monthly.sum(axis=1), axis=0) * 100

fig6 = go.Figure()
for s, color in COLORS.items():
    if s in mp.columns:
        fig6.add_trace(go.Scatter(x=mp.index, y=mp[s], name=s.capitalize(),
            line=dict(color=color, width=2.5), hovertemplate="%{y:.1f}%"))
fig6.add_hline(y=50, line_dash="dot", line_color="red", annotation_text="50% threshold")
fig6.update_layout(hovermode="x unified", yaxis_title="% of replies",
                   height=320, margin=dict(t=10,b=10))
st.plotly_chart(fig6, use_container_width=True)
