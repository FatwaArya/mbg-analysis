import pandas as pd
import os

os.makedirs("data/analysis", exist_ok=True)
df = pd.read_csv("data/processed/tweets_with_sentiment.csv")
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] >= "2025-01-01"]

# 1. Overall distribution
dist = df["sentiment_normalized"].value_counts().reset_index()
dist.columns = ["sentiment", "count"]
dist.to_csv("data/analysis/sentiment_overall.csv", index=False)
print("1. SENTIMENT DISTRIBUTION\n", dist.to_string(index=False))
print()

# 2. Sentiment over time daily
sent_time = df.groupby(["date", "sentiment_normalized"]).size().unstack(fill_value=0)
sent_time_pct = sent_time.div(sent_time.sum(axis=1), axis=0) * 100
sent_time_pct = sent_time_pct.reset_index()
sent_time_pct.columns = ["date", "negative", "neutral", "positive"]
sent_time_pct.to_csv("data/analysis/sentiment_over_time.csv", index=False)
print("2. Sentiment over time saved")

# 3. Weekly sentiment
weekly = (df.groupby([df["date"].dt.to_period("W").astype(str), "sentiment_normalized"])
            .size().unstack(fill_value=0))
weekly = weekly.div(weekly.sum(axis=1), axis=0) * 100
weekly = weekly.reset_index()
weekly = weekly.melt(id_vars=["date"], var_name="sentiment", value_name="count")
weekly.to_csv("data/analysis/sentiment_weekly.csv", index=False)
print("3. Weekly sentiment saved")

# 4. By language
lang_sent = df.groupby(["detected_lang", "sentiment_normalized"]).size().unstack(fill_value=0)
lang_sent.to_csv("data/analysis/sentiment_by_language.csv")
print("4. Sentiment by language saved\n", lang_sent.to_string())

# 5. Sentiment vs engagement
eng_sent = df.groupby("sentiment_normalized").agg(
    mean=("engagement_total", "mean"),
    median=("engagement_total", "median")
)
eng_sent = eng_sent.reset_index()
eng_sent.columns = ["sentiment", "mean", "median"]
eng_sent.to_csv("data/analysis/sentiment_engagement.csv", index=False)
print("5. Sentiment vs engagement saved\n", eng_sent.to_string(index=False))

print("\n=== SENTIMENT ANALYSIS COMPLETE ===")
