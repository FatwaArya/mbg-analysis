#!/usr/bin/env python3
"""Reply vs Parent Analysis — cross-analysis of reply sentiment against parent posts."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
tree = pd.read_csv(f"{ANALYSIS_DIR}/reply_tree.csv")
combined = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv", low_memory=False)

parents = combined[combined["tweet_type"] == "parent"].copy()
replies = combined[combined["tweet_type"] == "reply"].copy()

print(f"  Parents: {len(parents):,} | Replies: {len(replies):,}")
print(f"  Parent columns: {list(parents.columns)}")

# ── 1. Reply vs Parent Sentiment Matrix ──────────────────────────────
print("\n1. Building sentiment matrix...")
if "parent_sentiment" in tree.columns:
    matrix = tree.groupby(["parent_sentiment", "reply_sentiment"]).size().reset_index(name="count")
    matrix.to_csv(f"{OUTPUT_DIR}/reply_vs_parent_sentiment_matrix.csv", index=False)
    print(f"   Saved → reply_vs_parent_sentiment_matrix.csv")
    print(matrix.to_string(index=False))

# ── 2. Reply Sentiment by Parent Topic ───────────────────────────────
print("\n2. Reply sentiment by parent topic...")
topic_col = "topic_id" if "topic_id" in parents.columns else None
if topic_col and "parent_id" in replies.columns:
    parent_topics = parents[["id", topic_col]].dropna(subset=["id"]).copy()
    parent_topics["id"] = parent_topics["id"].astype(str)
    replies_copy = replies[["parent_id", "sentiment_normalized"]].copy()
    replies_copy["parent_id_str"] = replies_copy["parent_id"].astype(str)
    reply_topics = replies_copy.merge(
        parent_topics.rename(columns={"id": "parent_id_str"}),
        on="parent_id_str", how="left"
    )
    reply_topics = reply_topics.dropna(subset=[topic_col])
    by_topic = reply_topics.groupby([topic_col, "sentiment_normalized"]).size().reset_index(name="count")
    by_topic.to_csv(f"{OUTPUT_DIR}/reply_sentiment_by_parent_topic.csv", index=False)
    print(f"   Saved → reply_sentiment_by_parent_topic.csv ({len(by_topic)} rows)")
else:
    print(f"   Skipped — topic_id in parents: {topic_col is not None}")

# ── 3. Topic Reply Ratio ─────────────────────────────────────────────
print("\n3. Topic reply ratio...")
if topic_col:
    reply_counts = replies.groupby("parent_id").size().reset_index(name="r_count")
    reply_counts["parent_id"] = reply_counts["parent_id"].astype(str)
    parent_topic_reply = parents.copy()
    parent_topic_reply["id"] = parent_topic_reply["id"].astype(str)
    parent_topic_reply = parent_topic_reply.merge(reply_counts, left_on="id", right_on="parent_id", how="left")
    parent_topic_reply["r_count"] = parent_topic_reply["r_count"].fillna(0).astype(int)
    topic_ratio = parent_topic_reply.groupby(topic_col).agg(
        parent_count=("id", "count"),
        total_replies=("r_count", "sum"),
        avg_replies_per_parent=("r_count", "mean"),
        median_replies=("r_count", "median")
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
    if topic_col:
        parent_topics = parents[["id", topic_col]].dropna(subset=["id"]).copy()
        parent_topics["id"] = parent_topics["id"].astype(str)
        gap["parent_id"] = gap["parent_id"].astype(str)
        gap = gap.merge(parent_topics.rename(columns={"id": "parent_id"}), on="parent_id", how="left")
    gap.to_csv(f"{OUTPUT_DIR}/parent_reply_sentiment_gap.csv", index=False)
    print(f"   Saved → parent_reply_sentiment_gap.csv")
    print(f"   Avg gap: {gap['avg_gap'].mean():.3f} (negative = replies more negative)")

print("\n=== REPLY VS PARENT ANALYSIS COMPLETE ===")
