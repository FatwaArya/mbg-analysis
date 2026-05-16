#!/usr/bin/env python3
"""Controversy Deep Dive — analysis of controversial parent posts."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
tree = pd.read_csv(f"{ANALYSIS_DIR}/reply_tree.csv")
controversy = pd.read_csv(f"{ANALYSIS_DIR}/reply_controversy_scores.csv")
combined = pd.read_csv(f"{ANALYSIS_DIR}/corpus_combined.csv", low_memory=False)

parents = combined[combined["tweet_type"] == "parent"].copy()
print(f"  Tree: {len(tree):,} | Controversy: {len(controversy):,} | Parents: {len(parents):,}")
print(f"  Parent columns: {list(parents.columns)}")

# Build parent lookup with string IDs
parent_lookup = parents.copy()
parent_lookup["id"] = parent_lookup["id"].astype(str)
controversy["parent_id"] = controversy["parent_id"].astype(str)

# ── 1. Controversy by Topic ─────────────────────────────────────────
print("\n1. Controversy by topic...")
if "topic_id" in parent_lookup.columns:
    cont_topic = controversy.merge(
        parent_lookup[["id", "topic_id"]].rename(columns={"id": "parent_id"}),
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
    parent_lookup[["id", "date"]].rename(columns={"id": "parent_id"}),
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
merge_cols = ["id", "text", "topic_id", "engagement_total", "date"]
merge_cols = [c for c in merge_cols if c in parent_lookup.columns]
top_cont = top_cont.merge(parent_lookup[merge_cols].rename(columns={"id": "parent_id"}), on="parent_id", how="left")
out_cols = ["parent_id", "controversy_score", "reply_count"]
if "text" in top_cont.columns: out_cols.insert(1, "text")
if "topic_id" in top_cont.columns: out_cols.insert(2, "topic_id")
if "engagement_total" in top_cont.columns: out_cols.append("engagement_total")
if "date" in top_cont.columns: out_cols.append("date")
out_cols = [c for c in out_cols if c in top_cont.columns]
top_cont[out_cols].to_csv(f"{OUTPUT_DIR}/top_controversial_parents.csv", index=False)
print(f"   Saved → top_controversial_parents.csv (top 100)")

# ── 4. Controversy vs Engagement ─────────────────────────────────────
print("\n4. Controversy vs engagement...")
eng_cols = ["id", "engagement_total", "favorite_count", "retweet_count"]
if "reply_count" in parent_lookup.columns:
    eng_cols.append("reply_count")
eng_cols = [c for c in eng_cols if c in parent_lookup.columns]
cont_eng = controversy.merge(
    parent_lookup[eng_cols].rename(columns={"id": "parent_id"}),
    on="parent_id", how="left"
)
cont_eng["controversy_bin"] = pd.cut(cont_eng["controversy_score"], bins=[0, 0.1, 0.2, 0.3, 0.5, 1.0], labels=["0-0.1", "0.1-0.2", "0.2-0.3", "0.3-0.5", "0.5-1.0"])
agg_dict = {
    "avg_engagement": ("engagement_total", "mean"),
    "median_engagement": ("engagement_total", "median"),
    "avg_favorites": ("favorite_count", "mean"),
    "avg_retweets": ("retweet_count", "mean"),
    "parent_count": ("parent_id", "count")
}
if "reply_count" in cont_eng.columns:
    agg_dict["avg_replies"] = ("reply_count", "mean")
vs_eng = cont_eng.groupby("controversy_bin", observed=True).agg(**agg_dict).reset_index()
vs_eng.to_csv(f"{OUTPUT_DIR}/controversy_vs_engagement.csv", index=False)
print(f"   Saved → controversy_vs_engagement.csv")
print(vs_eng.to_string(index=False))

print("\n=== CONTROVERSY DEEP DIVE COMPLETE ===")
