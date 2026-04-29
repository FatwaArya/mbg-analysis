import pandas as pd
import os

os.makedirs("data/analysis", exist_ok=True)
df = pd.read_csv("data/processed/tweets_with_sentiment.csv")
df["date"] = pd.to_datetime(df["date"])

# 1. Overall distribution
dist = df["sentiment_normalized"].value_counts(normalize=True) * 100
dist.to_csv("data/analysis/sentiment_distribution.csv")
print("1. SENTIMENT DISTRIBUTION\n", dist.to_string())

# 2. Sentiment over time daily
sent_time = df.groupby(["date", "sentiment_normalized"]).size().unstack(fill_value=0)
sent_time_pct = sent_time.div(sent_time.sum(axis=1), axis=0) * 100
sent_time_pct.to_csv("data/analysis/sentiment_over_time.csv")
print("\n2. Sentiment over time saved")

# 3. Weekly sentiment
weekly = df.resample("W", on="date").apply(
    lambda x: x["sentiment_normalized"].value_counts(normalize=True) * 100
).unstack(fill_value=0)
weekly.to_csv("data/analysis/sentiment_weekly.csv")
print("3. Weekly sentiment saved")

# 4. By language
lang_sent = df.groupby(["detected_lang", "sentiment_normalized"]).size().unstack(fill_value=0)
lang_sent.to_csv("data/analysis/sentiment_by_language.csv")
print("4. Sentiment by language saved\n", lang_sent.to_string())

# 5. Sentiment vs engagement
eng_sent = df.groupby("sentiment_normalized").agg(
    count=("id", "count"),
    avg_engagement=("engagement_total", "mean"),
    avg_likes=("favorite_count", "mean"),
    avg_retweets=("retweet_count", "mean"),
    avg_replies=("reply_count", "mean")
)
eng_sent.to_csv("data/analysis/sentiment_vs_engagement.csv")
print("5. Sentiment vs engagement saved\n", eng_sent.to_string())

print("\n=== SENTIMENT ANALYSIS COMPLETE ===")
