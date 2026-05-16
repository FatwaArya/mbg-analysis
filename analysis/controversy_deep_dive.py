#!/usr/bin/env python3
"""Controversy Deep Dive — analysis of controversial parent posts."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
tree = pd.read_csv(f"{ANALYSIS_DIR}/reply_tree.csv")
controversy = pd.read_csv(f"{ANALYSIS_DIR}/reply_controversy_scores.csv")
combined = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv")

parents = combined[combined["tweet_type"] == "parent"].copy()
print(f"  Tree: {len(tree):,} | Controversy: {len(controversy):,} | Parents: {len(parents):,}")

# ── 1. Controversy by Topic ─────────────────────────────────────────
print("\n1. Controversy by topic...")
if "topic_id" in parents.columns:
    cont_topic = controversy.merge(
        parents[["id", "topic_id"]].rename(columns={"id": "parent_id"}),
        on="parent_id", how="left"
    )
    by_topic = cont_topic.groupby("topic_id").agg(
        avg_controversy=("controversy_score", "mean"),
        median_controversy=("controversy_score", "median"),
        max_controversy=("controversy_score", "max"),
        parent_count=("parent_id", "count")
    ).reset_index()
    by_topic = by_topic.sort_values("avg_controversy", ascending=False)
    by_topic.to_csv(f"{OUTPUT_DIR}/controversy_by_topic.csv", index=False)
    print(f"   Saved → controversy_by_topic.csv")
    print(by_topic.to_string(index=False))

# ── 2. Controversy Over Time ────────────────────────────────────────
print("\n2. Controversy over time...")
cont_time = controversy.merge(
    parents[["id", "date"]].rename(columns={"id": "parent_id"}),
    on="parent_id", how="left"
)
cont_time["date"] = pd.to_datetime(cont_time["date"], errors="coerce")
cont_time = cont_time.dropna(subset=["date"])
daily_cont = cont_time.groupby("date").agg(
    avg_controversy=("controversy_score", "mean"),
    controversial_count=("controversy_score", lambda x: (x > 0.3).sum()),
    total_parents=("controversy_score", "count")
).reset_index()
daily_cont = daily_cont.sort_values("date")
daily_cont.to_csv(f"{OUTPUT_DIR}/controversy_over_time.csv", index=False)
print(f"   Saved → controversy_over_time.csv ({len(daily_cont)} days)")

# ── 3. Top Controversial Parents ─────────────────────────────────────
print("\n3. Top controversial parents...")
top_cont = controversy.sort_values("controversy_score", ascending=False).head(100)
top_cont = top_cont.merge(parents[["id", "text", "topic_id", "engagement_total", "date"]].rename(columns={"id": "parent_id"}), on="parent_id", how="left")
top_cont = top_cont[["parent_id", "text", "topic_id", "controversy_score", "reply_count", "engagement_total", "date"]]
top_cont.to_csv(f"{OUTPUT_DIR}/top_controversial_parents.csv", index=False)
print(f"   Saved → top_controversial_parents.csv (top 100)")

# ── 4. Controversy vs Engagement ─────────────────────────────────────
print("\n4. Controversy vs engagement...")
cont_eng = controversy.merge(
    parents[["id", "engagement_total", "favorite_count", "retweet_count", "reply_count"]].rename(columns={"id": "parent_id"}),
    on="parent_id", how="left"
)
cont_eng["controversy_bin"] = pd.cut(cont_eng["controversy_score"], bins=[0, 0.1, 0.2, 0.3, 0.5, 1.0], labels=["0-0.1", "0.1-0.2", "0.2-0.3", "0.3-0.5", "0.5-1.0"])
vs_eng = cont_eng.groupby("controversy_bin", observed=True).agg(
    avg_engagement=("engagement_total", "mean"),
    median_engagement=("engagement_total", "median"),
    avg_favorites=("favorite_count", "mean"),
    avg_retweets=("retweet_count", "mean"),
    avg_replies=("reply_count", "mean"),
    parent_count=("parent_id", "count")
).reset_index()
vs_eng.to_csv(f"{OUTPUT_DIR}/controversy_vs_engagement.csv", index=False)
print(f"   Saved → controversy_vs_engagement.csv")
print(vs_eng.to_string(index=False))

print("\n=== CONTROVERSY DEEP DIVE COMPLETE ===")
