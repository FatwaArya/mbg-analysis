import pandas as pd
import numpy as np
from scipy import stats
import os

os.makedirs("data/analysis", exist_ok=True)
for _p in ["data/processed/tweets_with_topics.csv",
           "data/processed/tweets_with_sentiment.csv",
           "data/processed/tweets_relevant_tagged.csv"]:
    if os.path.exists(_p):
        df = pd.read_csv(_p)
        break
if "df" not in locals():
    # FIX: emit insufficient-data outputs when no input datasets exist.
    print("No statistical input datasets found. Writing empty outputs.")
    pd.DataFrame(columns=["date", "tweet_count"]).to_csv("data/analysis/daily_volume.csv", index=False)
    pd.DataFrame(columns=["date", "tweet_count"]).to_csv("data/analysis/weekly_volume.csv", index=False)
    pd.DataFrame(columns=["hour", "tweet_count"]).to_csv("data/analysis/hourly_pattern.csv", index=False)
    pd.DataFrame(columns=["id", "text", "engagement_total", "favorite_count",
                          "retweet_count", "reply_count", "date", "detected_lang"]).to_csv(
        "data/analysis/top_posts.csv", index=False
    )
    # FIX: continue with an empty frame instead of raising.
    df = pd.DataFrame(columns=[
        "id", "text", "engagement_total", "favorite_count", "retweet_count", "reply_count",
        "date", "created_at", "detected_lang", "user_id", "scrape_tab", "hour", "query_raw"
    ])
df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] >= "2025-01-01"]
df["created_at"] = pd.to_datetime(df["created_at"])

print("=== STATISTICAL ANALYSIS ===\n")

# 1. CORPUS OVERVIEW
print("1. CORPUS OVERVIEW")
print(f"   Total tweets : {len(df):,}")
print(f"   Date range   : {df['date'].min().date()} -> {df['date'].max().date()}")
print(f"   Unique users : {df['user_id'].nunique():,}")
print(f"   Languages    : {df['detected_lang'].value_counts().to_dict()}")
print(f"   Scrape tabs  : {df['scrape_tab'].value_counts().to_dict()}")
print()

# 2. TWEET VOLUME OVER TIME
daily_volume = df.groupby("date").size().reset_index(name="tweet_count")
weekly_volume = df.resample("W", on="date").size().reset_index(name="tweet_count")
daily_volume.to_csv("data/analysis/daily_volume.csv", index=False)
weekly_volume.to_csv("data/analysis/weekly_volume.csv", index=False)
if len(daily_volume) > 0:
    peak = daily_volume.loc[daily_volume["tweet_count"].idxmax()]
    print(f"2. Peak day    : {peak['date'].date()}")
    print(f"   Peak count  : {peak['tweet_count']:,}")
else:
    # FIX: avoid idxmax crash on empty daily aggregates.
    print("2. Peak day    : insufficient data")
    print("   Peak count  : insufficient data")
print(f"   Avg/day     : {daily_volume['tweet_count'].mean():.0f}")
print()

# 3. ENGAGEMENT PATTERNS
eng_stats = df[["favorite_count", "retweet_count", "reply_count", "engagement_total"]].describe()
eng_stats.to_csv("data/analysis/engagement_stats.csv")
df["talk_amplify_ratio"] = df["reply_count"] / (df["retweet_count"] + 1)
print(f"3. Avg talk/amplify ratio : {df['talk_amplify_ratio'].mean():.3f}")
print()

# 4. HOURLY POSTING PATTERN
hourly = df.groupby("hour").size().reset_index(name="tweet_count")
hourly.to_csv("data/analysis/hourly_pattern.csv", index=False)
if len(hourly) > 0:
    print(f"4. Peak hour : {hourly.loc[hourly['tweet_count'].idxmax(), 'hour']}:00")
else:
    # FIX: avoid idxmax crash on empty hourly aggregates.
    print("4. Peak hour : insufficient data")
print()

# 5. QUERY EFFECTIVENESS
query_stats = df.groupby("query_raw").agg(
    tweet_count=("id", "count"),
    avg_engagement=("engagement_total", "mean"),
    median_engagement=("engagement_total", "median"),
    total_engagement=("engagement_total", "sum")
).sort_values("tweet_count", ascending=False)
query_stats.to_csv("data/analysis/query_effectiveness.csv")
print("5. Query effectiveness saved")
print()

# 6. TOP POSTS
top_posts = df.nlargest(20, "engagement_total")[
    ["id", "text", "engagement_total", "favorite_count",
     "retweet_count", "reply_count", "date", "detected_lang"]
]
top_posts.to_csv("data/analysis/top_posts.csv", index=False)
if len(top_posts) > 0:
    print(f"6. Top post engagement : {top_posts['engagement_total'].iloc[0]:,}")
else:
    # FIX: avoid iloc crash on empty top posts.
    print("6. Top post engagement : insufficient data")
print()

# 7. ENGAGEMENT CORRELATION
corr = df[["favorite_count", "retweet_count", "reply_count", "engagement_total"]].corr()
corr.to_csv("data/analysis/engagement_correlation.csv")
print("7. Correlation matrix saved")

print("\n=== STATISTICAL ANALYSIS COMPLETE ===")
print("Output -> data/analysis/")
