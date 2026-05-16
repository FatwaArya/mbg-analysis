#!/usr/bin/env python3
"""Thread Analysis — Reply depth patterns and conversation statistics."""
import pandas as pd
import numpy as np
import time

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
t0 = time.time()
df = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv",
                 usecols=["id", "parent_id", "depth", "created_at",
                          "favorite_count", "retweet_count", "reply_count",
                          "sentiment_label", "user_screen_name"])
df["created_at"] = pd.to_datetime(df["created_at"])
df["id"] = df["id"].astype(str)
df["parent_id"] = df["parent_id"].astype(str)
print(f"  Loaded {len(df):,} rows ({time.time()-t0:.1f}s)")

# ── 1. Thread Depth Statistics ──────────────────────────────────────
print("\n1. Thread depth statistics...")
depth_stats = df.groupby("depth").agg(
    reply_count=("id", "count"),
    unique_users=("user_screen_name", "nunique"),
    avg_favorites=("favorite_count", "mean"),
    avg_retweets=("retweet_count", "mean"),
    avg_reply_count=("reply_count", "mean"),
    neg_pct=("sentiment_label", lambda x: (x == "negative").mean() * 100),
    neu_pct=("sentiment_label", lambda x: (x == "neutral").mean() * 100),
    pos_pct=("sentiment_label", lambda x: (x == "positive").mean() * 100),
).reset_index()
depth_stats.to_csv(f"{OUTPUT_DIR}/thread_depth_stats.csv", index=False)
print(f"  Saved → thread_depth_stats.csv")
print(depth_stats.to_string(index=False))

# ── 2. Parent Conversation Statistics ───────────────────────────────
print("\n2. Parent conversation statistics...")
parent_stats = df.groupby("parent_id").agg(
    reply_count=("id", "count"),
    unique_users=("user_screen_name", "nunique"),
    max_depth=("depth", "max"),
    avg_favorites=("favorite_count", "mean"),
    avg_retweets=("retweet_count", "mean"),
    first_reply=("created_at", "min"),
    last_reply=("created_at", "max"),
    neg_pct=("sentiment_label", lambda x: (x == "negative").mean() * 100),
    neu_pct=("sentiment_label", lambda x: (x == "neutral").mean() * 100),
    pos_pct=("sentiment_label", lambda x: (x == "positive").mean() * 100),
    sentiment_diversity=("sentiment_label", "nunique"),
).reset_index()
parent_stats["conversation_span_hours"] = (
    parent_stats["last_reply"] - parent_stats["first_reply"]
).dt.total_seconds() / 3600

parent_stats = parent_stats.sort_values("reply_count", ascending=False)
parent_stats.to_csv(f"{OUTPUT_DIR}/parent_conversation_stats.csv", index=False)
print(f"  Saved → parent_conversation_stats.csv ({len(parent_stats):,} parents)")

print(f"\n=== THREAD ANALYSIS COMPLETE ({time.time()-t0:.1f}s) ===")
print(f"  Max depth: {df['depth'].max()}")
print(f"  Avg replies per parent: {parent_stats['reply_count'].mean():.1f}")
print(f"  Top 5 most replied parents:")
print(parent_stats[["parent_id", "reply_count", "unique_users", "max_depth", "sentiment_diversity"]].head().to_string(index=False))
