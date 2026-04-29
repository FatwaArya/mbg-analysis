import pandas as pd
import os

os.makedirs("data/analysis", exist_ok=True)
df = pd.read_csv("data/processed/tweets_with_topics.csv")
topic_info = pd.read_csv("data/processed/topic_info.csv")
df["date"] = pd.to_datetime(df["date"])
valid = topic_info[topic_info["Topic"] != -1]

print(f"Topics discovered : {len(valid)}")
print(f"Outlier tweets    : {(df['topic_id'] == -1).sum():,}")
topic_info.to_csv("data/analysis/topic_overview.csv", index=False)

# Topic over time
topic_time = df[df["topic_id"] != -1].groupby(["date", "topic_id"]).size().unstack(fill_value=0)
topic_time.to_csv("data/analysis/topic_over_time.csv")
print("Topic over time saved")

# Sentiment per topic
if "sentiment_normalized" in df.columns:
    ts = df[df["topic_id"] != -1].groupby(["topic_id", "sentiment_normalized"]).size().unstack(fill_value=0)
    ts_pct = ts.div(ts.sum(axis=1), axis=0) * 100
    ts_pct.to_csv("data/analysis/topic_sentiment_breakdown.csv")
    print("Topic sentiment breakdown saved")

# Engagement per topic
te = df[df["topic_id"] != -1].groupby("topic_id").agg(
    count=("id", "count"),
    avg_engagement=("engagement_total", "mean"),
    total_engagement=("engagement_total", "sum")
).sort_values("total_engagement", ascending=False)
te.to_csv("data/analysis/topic_engagement.csv")
print("Topic engagement saved")

print("\n=== TOPIC ANALYSIS COMPLETE ===")
