#!/usr/bin/env python3
"""Engagement Insights — parent vs reply engagement, viral patterns."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
combined = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv", low_memory=False)
tree = pd.read_csv(f"{ANALYSIS_DIR}/reply_tree.csv")

parents = combined[combined["tweet_type"] == "parent"].copy()
replies = combined[combined["tweet_type"] == "reply"].copy()
print(f"  Parents: {len(parents):,} | Replies: {len(replies):,}")

# Build parent lookup with string IDs
parent_lookup = parents.copy()
parent_lookup["id"] = parent_lookup["id"].astype(str)

# ── 1. Engagement: Parent vs Reply ──────────────────────────────────
print("\n1. Engagement comparison...")
eng_parent = parents.groupby("sentiment_normalized").agg(
    avg_favorites=("favorite_count", "mean"),
    median_favorites=("favorite_count", "median"),
    avg_retweets=("retweet_count", "mean"),
    median_retweets=("retweet_count", "median"),
    avg_replies=("reply_count", "mean"),
    median_replies=("reply_count", "median"),
    avg_engagement=("engagement_total", "mean"),
    median_engagement=("engagement_total", "median"),
    count=("id", "count")
).reset_index()
eng_parent["type"] = "parent"

eng_reply = replies.groupby("sentiment_normalized").agg(
    avg_favorites=("favorite_count", "mean"),
    median_favorites=("favorite_count", "median"),
    avg_retweets=("retweet_count", "mean"),
    median_retweets=("retweet_count", "median"),
    avg_replies=("reply_count", "mean"),
    median_replies=("reply_count", "median"),
    avg_engagement=("engagement_total", "mean"),
    median_engagement=("engagement_total", "median"),
    count=("id", "count")
).reset_index()
eng_reply["type"] = "reply"

eng_combined = pd.concat([eng_parent, eng_reply], ignore_index=True)
eng_combined.to_csv(f"{OUTPUT_DIR}/engagement_parent_vs_reply.csv", index=False)
print(f"   Saved → engagement_parent_vs_reply.csv")
print(eng_combined.to_string(index=False))

# ── 2. Viral Reply Parents ──────────────────────────────────────────
print("\n2. Viral reply parents...")
reply_engagement = tree.groupby("parent_id").agg(
    total_reply_favorites=("reply_favorites", "sum"),
    total_reply_retweets=("reply_retweets", "sum"),
    total_reply_replies=("reply_replies", "sum"),
    total_reply_engagement=("reply_engagement", "sum"),
    reply_count=("reply_id", "count")
).reset_index()
reply_engagement["parent_id"] = reply_engagement["parent_id"].astype(str)
reply_engagement = reply_engagement.sort_values("total_reply_engagement", ascending=False).head(100)
reply_engagement = reply_engagement.merge(
    parent_lookup[["id", "text", "topic_id", "sentiment_normalized", "engagement_total", "date"]].rename(columns={"id": "parent_id"}),
    on="parent_id", how="left"
)
reply_engagement.to_csv(f"{OUTPUT_DIR}/viral_reply_parents.csv", index=False)
print(f"   Saved → viral_reply_parents.csv (top 100)")

# ── 3. Query Reply Sentiment ────────────────────────────────────────
print("\n3. Query reply sentiment...")
if "query_raw" in parent_lookup.columns and "parent_id" in replies.columns:
    reply_query = replies[["parent_id", "sentiment_normalized"]].copy()
    reply_query["parent_id"] = reply_query["parent_id"].astype(str)
    reply_query = reply_query.merge(
        parent_lookup[["id", "query_raw"]].rename(columns={"id": "parent_id"}),
        on="parent_id", how="left"
    )
    query_sent = reply_query.groupby(["query_raw", "sentiment_normalized"]).size().reset_index(name="count")
    query_sent.to_csv(f"{OUTPUT_DIR}/query_reply_sentiment.csv", index=False)
    print(f"   Saved → query_reply_sentiment.csv")
    print(query_sent.to_string(index=False))

print("\n=== ENGAGEMENT INSIGHTS COMPLETE ===")
