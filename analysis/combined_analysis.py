import pandas as pd
import numpy as np
from scipy import stats
import os

os.makedirs("data/analysis", exist_ok=True)
df = pd.read_csv("data/processed/tweets_with_topics.csv")
df["date"] = pd.to_datetime(df["date"])

print("=== COMBINED ANALYSIS ===\n")

# 1. Do negative posts spread more?
neg = df[df["sentiment_normalized"] == "negative"]["retweet_count"]
pos = df[df["sentiment_normalized"] == "positive"]["retweet_count"]
_, p_val = stats.mannwhitneyu(neg, pos, alternative="two-sided")
print("1. NEGATIVE AMPLIFICATION TEST")
print(f"   Avg RT negative : {neg.mean():.1f}")
print(f"   Avg RT positive : {pos.mean():.1f}")
print(f"   p-value         : {p_val:.4f}")
print(f"   Significant     : {p_val < 0.05}")
print()

# 2. Sentiment shift over time
monthly = (df.groupby([df["date"].dt.to_period("M").astype(str), "sentiment_normalized"])
             .size().unstack(fill_value=0))
monthly = monthly.div(monthly.sum(axis=1), axis=0) * 100
monthly.to_csv("data/analysis/monthly_sentiment_shift.csv")
first_pos = monthly["positive"].iloc[0] if "positive" in monthly else 0
last_pos = monthly["positive"].iloc[-1] if "positive" in monthly else 0
print(f"2. SENTIMENT TREND")
print(f"   First month +ve : {first_pos:.1f}%")
print(f"   Last month +ve  : {last_pos:.1f}%")
print(f"   Trend           : {'improving' if last_pos > first_pos else 'declining'}")
print()

# 3. Topic x sentiment x engagement crosstab
if "topic_id" in df.columns:
    crosstab = pd.crosstab(
        df["topic_id"], df["sentiment_normalized"],
        values=df["engagement_total"], aggfunc="mean"
    ).round(0)
    crosstab.to_csv("data/analysis/topic_sentiment_engagement_crosstab.csv")
    print("3. Crosstab saved")
print()

# 4. Talk vs amplify by sentiment
df["talk_amplify"] = df["reply_count"] / (df["retweet_count"] + 1)
ta = df.groupby("sentiment_normalized")["talk_amplify"].mean()
ta.to_csv("data/analysis/talk_amplify_by_sentiment.csv")
print("4. TALK VS AMPLIFY BY SENTIMENT\n", ta.to_string())
print()

# 5. Paper statistics summary
summary = {
    "total_tweets": len(df),
    "date_from": str(df["date"].min().date()),
    "date_to": str(df["date"].max().date()),
    "pct_positive": round((df["sentiment_normalized"] == "positive").mean() * 100, 1),
    "pct_negative": round((df["sentiment_normalized"] == "negative").mean() * 100, 1),
    "pct_neutral": round((df["sentiment_normalized"] == "neutral").mean() * 100, 1),
    "n_topics": int(df["topic_id"].nunique()) if "topic_id" in df.columns else 0,
    "negative_amplification_significant": bool(p_val < 0.05),
    "sentiment_trend": "improving" if last_pos > first_pos else "declining"
}
pd.DataFrame([summary]).to_csv("data/analysis/paper_statistics_summary.csv", index=False)
print("5. PAPER STATISTICS SUMMARY")
for k, v in summary.items():
    print(f"   {k:<48}: {v}")

print("\n=== COMBINED ANALYSIS COMPLETE ===")
print("All outputs -> data/analysis/")
