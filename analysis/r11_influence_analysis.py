#!/usr/bin/env python3
"""Influence Analysis — User influence scores and sentiment consistency."""
import pandas as pd
import numpy as np
from scipy.stats import entropy
import time

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
t0 = time.time()
df = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv",
                 usecols=["id", "user_screen_name", "user_id", "parent_id",
                          "favorite_count", "retweet_count", "reply_count",
                          "sentiment_label", "created_at"])
df["created_at"] = pd.to_datetime(df["created_at"])
df["id"] = df["id"].astype(str)
df["parent_id"] = df["parent_id"].astype(str)
df["user"] = df["user_screen_name"].fillna(df["user_id"].astype(str))
print(f"  Loaded {len(df):,} rows ({time.time()-t0:.1f}s)")

# ── 1. User Influence Scores ────────────────────────────────────────
print("\n1. Computing user influence scores...")
user_engagement = df.groupby("user").agg(
    tweet_count=("id", "count"),
    total_favs=("favorite_count", "sum"),
    total_rts=("retweet_count", "sum"),
    total_replies_received=("reply_count", "sum"),
    unique_parents=("parent_id", "nunique"),
    first_post=("created_at", "min"),
    last_post=("created_at", "max"),
).reset_index()

user_engagement["total_engagement"] = (
    user_engagement["total_favs"] + user_engagement["total_rts"] + user_engagement["total_replies_received"]
)
user_engagement["avg_engagement"] = user_engagement["total_engagement"] / user_engagement["tweet_count"]
user_engagement["reply_reach"] = user_engagement["unique_parents"]
user_engagement["activity_span_days"] = (
    user_engagement["last_post"] - user_engagement["first_post"]
).dt.days.clip(lower=1)
user_engagement["tweets_per_day"] = user_engagement["tweet_count"] / user_engagement["activity_span_days"]

user_engagement["influence_score"] = (
    np.log1p(user_engagement["total_engagement"]) *
    np.log1p(user_engagement["reply_reach"]) *
    np.log1p(user_engagement["tweet_count"])
)
user_engagement["influence_score"] = user_engagement["influence_score"].round(4)
user_engagement = user_engagement.sort_values("influence_score", ascending=False)

user_engagement.to_csv(f"{OUTPUT_DIR}/user_influence_scores.csv", index=False)
print(f"  Saved → user_influence_scores.csv ({len(user_engagement):,} users)")

# ── 2. Sentiment Consistency ────────────────────────────────────────
print("\n2. Computing sentiment consistency...")
sentiment_dist = df.groupby(["user", "sentiment_label"]).size().unstack(fill_value=0)
for col in ["negative", "neutral", "positive"]:
    if col not in sentiment_dist.columns:
        sentiment_dist[col] = 0
sentiment_dist = sentiment_dist[["negative", "neutral", "positive"]]

row_sums = sentiment_dist.sum(axis=1)
sentiment_probs = sentiment_dist.div(row_sums, axis=0)
sentiment_probs["entropy"] = entropy(sentiment_probs.T, base=3)
sentiment_probs["consistency"] = 1 - sentiment_probs["entropy"]
sentiment_probs["dominant_sentiment"] = sentiment_probs[["negative", "neutral", "positive"]].idxmax(axis=1)
sentiment_probs["dominant_pct"] = sentiment_probs[["negative", "neutral", "positive"]].max(axis=1) * 100
sentiment_probs["tweet_count"] = row_sums

sentiment_consistency = sentiment_probs.reset_index()
sentiment_consistency = sentiment_consistency.rename(columns={
    "negative": "neg_count", "neutral": "neu_count", "positive": "pos_count"
})
sentiment_consistency["consistency"] = sentiment_consistency["consistency"].round(4)
sentiment_consistency["dominant_pct"] = sentiment_consistency["dominant_pct"].round(2)

sentiment_consistency.to_csv(f"{OUTPUT_DIR}/sentiment_consistency.csv", index=False)
print(f"  Saved → sentiment_consistency.csv ({len(sentiment_consistency):,} users)")

print(f"\n=== INFLUENCE ANALYSIS COMPLETE ({time.time()-t0:.1f}s) ===")
print(f"  Top 10 by influence score:")
print(user_engagement[["user", "influence_score", "total_engagement", "tweet_count", "reply_reach"]].head(10).to_string(index=False))
print(f"\n  Sentiment consistency:")
print(f"    Most consistent (negative): {sentiment_consistency[sentiment_consistency['dominant_sentiment']=='negative']['consistency'].mean():.3f}")
print(f"    Most consistent (positive): {sentiment_consistency[sentiment_consistency['dominant_sentiment']=='positive']['consistency'].mean():.3f}")
