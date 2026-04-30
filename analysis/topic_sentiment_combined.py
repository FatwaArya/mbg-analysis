import pandas as pd
import numpy as np
from scipy import stats
import os

os.makedirs("data/analysis", exist_ok=True)

df = pd.read_csv("data/processed/tweets_with_topics.csv", parse_dates=["date"])
ti = pd.read_csv("data/processed/topic_info.csv")
valid = ti[ti["Topic"] != -1].copy()
id_to_name = dict(zip(valid["Topic"], valid["Name"]))

assigned = df[df["topic_id"] != -1].copy()

# ── 3a. Topic × Sentiment ─────────────────────────────────────────────────────
ts = assigned.groupby(["topic_id", "sentiment_normalized"]).size().unstack(fill_value=0)
ts_pct = ts.div(ts.sum(axis=1), axis=0) * 100
ts_pct["topic_name"] = ts_pct.index.map(id_to_name)
ts_pct["total_tweets"] = ts.sum(axis=1)
ts_pct = ts_pct.sort_values("negative", ascending=False)
ts_pct.to_csv("data/analysis/topic_sentiment_matrix.csv")

print("=== TOP 10 MOST NEGATIVE TOPICS ===")
cols = ["topic_name", "negative", "positive", "neutral", "total_tweets"]
print(ts_pct[cols].head(10).round(1).to_string())

# ── 3b. Topic dominance over time (monthly) ───────────────────────────────────
top10 = valid.nlargest(10, "Count")["Topic"].tolist()
top_df = assigned[assigned["topic_id"].isin(top10)].copy()
topic_time = top_df.groupby([top_df["date"].dt.to_period("M"), "topic_id"]).size().unstack(fill_value=0)
topic_time.index = topic_time.index.to_timestamp()
topic_time.columns = [id_to_name.get(c, str(c)) for c in topic_time.columns]
topic_time.to_csv("data/analysis/topic_over_time_monthly.csv")
print("\n=== TOPIC MONTHLY TREND (last 6 months) ===")
print(topic_time.tail(6).to_string())

# ── 3c. Topic amplification ───────────────────────────────────────────────────
amp = assigned.groupby("topic_id").agg(
    topic_name=("topic_id", lambda x: id_to_name.get(x.iloc[0], str(x.iloc[0]))),
    tweet_count=("id", "count"),
    avg_rt=("retweet_count", "mean"),
    avg_reply=("reply_count", "mean"),
    avg_engagement=("engagement_total", "mean"),
    pct_negative=("sentiment_normalized", lambda x: (x == "negative").mean() * 100),
).round(1)
amp["talk_amplify"] = (amp["avg_reply"] / (amp["avg_rt"] + 1)).round(3)
amp = amp.sort_values("avg_rt", ascending=False)
amp.to_csv("data/analysis/topic_amplification.csv")

print("\n=== TOP 10 MOST AMPLIFIED TOPICS (avg RT) ===")
print(amp[["topic_name", "tweet_count", "avg_rt", "avg_reply", "talk_amplify", "pct_negative"]].head(10).to_string())

# ── Sentiment shift per topic (early vs recent) ───────────────────────────────
df_s = assigned.sort_values("date")
n = int(len(df_s) * 0.2)
early = df_s.head(n)
recent = df_s.tail(n)

shift_rows = []
for tid in top10:
    e_neg = (early[early["topic_id"] == tid]["sentiment_normalized"] == "negative").mean() * 100
    r_neg = (recent[recent["topic_id"] == tid]["sentiment_normalized"] == "negative").mean() * 100
    shift_rows.append({"topic_id": tid, "topic_name": id_to_name.get(tid, str(tid)),
                       "early_neg_pct": round(e_neg, 1), "recent_neg_pct": round(r_neg, 1),
                       "change_pp": round(r_neg - e_neg, 1)})
shift_df = pd.DataFrame(shift_rows).sort_values("change_pp", ascending=False)
shift_df.to_csv("data/analysis/topic_sentiment_shift.csv", index=False)
print("\n=== TOPIC SENTIMENT SHIFT (early vs recent) ===")
print(shift_df.to_string(index=False))

print("\n=== TOPIC × SENTIMENT COMBINED COMPLETE ===")
