#!/usr/bin/env python3
"""Topic Reply Analysis — topic distribution in replies, topic controversy, sentiment shift."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
combined = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv")
tree = pd.read_csv(f"{ANALYSIS_DIR}/reply_tree.csv")
topic_info = pd.read_csv(f"{ANALYSIS_DIR}/topic_overview.csv")
controversy = pd.read_csv(f"{ANALYSIS_DIR}/reply_controversy_scores.csv")

parents = combined[combined["tweet_type"] == "parent"].copy()
replies = combined[combined["tweet_type"] == "reply"].copy()
print(f"  Parents: {len(parents):,} | Replies: {len(replies):,} | Topics: {len(topic_info)}")

# ── 1. Reply Topic Distribution ─────────────────────────────────────
print("\n1. Reply topic distribution...")
reply_topics = replies.merge(
    parents[["id", "topic_id"]].rename(columns={"id": "parent_id"}),
    on="parent_id", how="left"
)
topic_dist = reply_topics.groupby(["topic_id", "sentiment_normalized"]).size().reset_index(name="reply_count")
topic_dist = topic_dist.merge(topic_info[["Topic", "Name", "Count"]].rename(columns={"Topic": "topic_id", "Count": "parent_count"}), on="topic_id", how="left")
topic_dist.to_csv(f"{OUTPUT_DIR}/reply_topic_distribution.csv", index=False)
print(f"   Saved → reply_topic_distribution.csv")
print(topic_dist.to_string(index=False))

# ── 2. Topic Controversy Ranking ────────────────────────────────────
print("\n2. Topic controversy ranking...")
if "topic_id" in parents.columns:
    cont_topic = controversy.merge(
        parents[["id", "topic_id"]].rename(columns={"id": "parent_id"}),
        on="parent_id", how="left"
    )
    topic_cont_rank = cont_topic.groupby("topic_id").agg(
        avg_controversy=("controversy_score", "mean"),
        median_controversy=("controversy_score", "median"),
        highly_controversial=("controversy_score", lambda x: (x > 0.4).sum()),
        parent_count=("parent_id", "count")
    ).reset_index()
    topic_cont_rank = topic_cont_rank.merge(topic_info[["Topic", "Name"]].rename(columns={"Topic": "topic_id"}), on="topic_id", how="left")
    topic_cont_rank = topic_cont_rank.sort_values("avg_controversy", ascending=False)
    topic_cont_rank.to_csv(f"{OUTPUT_DIR}/topic_controversy_ranking.csv", index=False)
    print(f"   Saved → topic_controversy_ranking.csv")
    print(topic_cont_rank.to_string(index=False))

# ── 3. Topic Sentiment Shift ────────────────────────────────────────
print("\n3. Topic sentiment shift (parent → reply)...")
if "parent_sentiment" in tree.columns and "topic_id" in parents.columns:
    tree_topic = tree.merge(
        parents[["id", "topic_id"]].rename(columns={"id": "parent_id"}),
        on="parent_id", how="left"
    )
    tree_topic["same_sentiment"] = tree_topic["parent_sentiment"] == tree_topic["reply_sentiment"]
    tree_topic["shift_direction"] = "same"
    tree_topic.loc[~tree_topic["same_sentiment"], "shift_direction"] = (
        tree_topic.loc[~tree_topic["same_sentiment"], "parent_sentiment"] + "→" +
        tree_topic.loc[~tree_topic["same_sentiment"], "reply_sentiment"]
    )
    topic_shift = tree_topic.groupby(["topic_id", "shift_direction"]).size().reset_index(name="count")
    topic_shift = topic_shift.merge(topic_info[["Topic", "Name"]].rename(columns={"Topic": "topic_id"}), on="topic_id", how="left")
    topic_shift.to_csv(f"{OUTPUT_DIR}/topic_sentiment_shift.csv", index=False)
    print(f"   Saved → topic_sentiment_shift.csv")
    print(topic_shift.to_string(index=False))

print("\n=== TOPIC REPLY ANALYSIS COMPLETE ===")
