#!/usr/bin/env python3
"""Reply vs Parent Analysis — cross-analysis of reply sentiment against parent posts."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
tree = pd.read_csv(f"{ANALYSIS_DIR}/reply_tree.csv")
combined = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv")

parents = combined[combined["tweet_type"] == "parent"].copy()
replies = combined[combined["tweet_type"] == "reply"].copy()

print(f"  Parents: {len(parents):,} | Replies: {len(replies):,}")

# ── 1. Reply vs Parent Sentiment Matrix ──────────────────────────────
print("\n1. Building sentiment matrix...")
if "parent_sentiment" in tree.columns:
    matrix = tree.groupby(["parent_sentiment", "reply_sentiment"]).size().reset_index(name="count")
    matrix.to_csv(f"{OUTPUT_DIR}/reply_vs_parent_sentiment_matrix.csv", index=False)
    print(f"   Saved → reply_vs_parent_sentiment_matrix.csv")
    print(matrix.to_string(index=False))

# ── 2. Reply Sentiment by Parent Topic ───────────────────────────────
print("\n2. Reply sentiment by parent topic...")
if "topic_id" in parents.columns and "parent_id" in replies.columns:
    reply_topics = replies.merge(
        parents[["id", "topic_id"]].rename(columns={"id": "parent_id"}),
        on="parent_id", how="left"
    )
    by_topic = reply_topics.groupby(["topic_id", "sentiment_normalized"]).size().reset_index(name="count")
    by_topic.to_csv(f"{OUTPUT_DIR}/reply_sentiment_by_parent_topic.csv", index=False)
    print(f"   Saved → reply_sentiment_by_parent_topic.csv ({len(by_topic)} rows)")

# ── 3. Topic Reply Ratio ─────────────────────────────────────────────
print("\n3. Topic reply ratio...")
if "topic_id" in parents.columns:
    reply_counts = replies.groupby("parent_id").size().reset_index(name="reply_count")
    parent_topic_reply = parents.merge(reply_counts, left_on="id", right_on="parent_id", how="left")
    parent_topic_reply["reply_count"] = parent_topic_reply["reply_count"].fillna(0).astype(int)
    topic_ratio = parent_topic_reply.groupby("topic_id").agg(
        parent_count=("id", "count"),
        total_replies=("reply_count", "sum"),
        avg_replies_per_parent=("reply_count", "mean"),
        median_replies=("reply_count", "median")
    ).reset_index()
    topic_ratio.to_csv(f"{OUTPUT_DIR}/topic_reply_ratio.csv", index=False)
    print(f"   Saved → topic_reply_ratio.csv")
    print(topic_ratio.to_string(index=False))

# ── 4. Parent-Reply Sentiment Gap ────────────────────────────────────
print("\n4. Parent-reply sentiment gap...")
if "parent_sentiment" in tree.columns:
    sent_map = {"positive": 1, "neutral": 0, "negative": -1}
    tree["parent_sent_val"] = tree["parent_sentiment"].map(sent_map)
    tree["reply_sent_val"] = tree["reply_sentiment"].map(sent_map)
    tree["sentiment_gap"] = tree["reply_sent_val"] - tree["parent_sent_val"]
    gap = tree.groupby("parent_id").agg(
        avg_gap=("sentiment_gap", "mean"),
        reply_count=("reply_id", "count"),
        parent_sentiment=("parent_sentiment", "first")
    ).reset_index()
    gap = gap.merge(parents[["id", "topic_id"]].rename(columns={"id": "parent_id"}), on="parent_id", how="left")
    gap.to_csv(f"{OUTPUT_DIR}/parent_reply_sentiment_gap.csv", index=False)
    print(f"   Saved → parent_reply_sentiment_gap.csv")
    print(f"   Avg gap: {gap['avg_gap'].mean():.3f} (negative = replies more negative)")

print("\n=== REPLY VS PARENT ANALYSIS COMPLETE ===")
