#!/usr/bin/env python3
"""Temporal Reply Analysis — reply volume, sentiment trends, hourly/weekly patterns."""
import pandas as pd
import os

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR

print("Loading data...")
replies = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv")
replies["date"] = pd.to_datetime(replies["date"], errors="coerce")
replies["hour_wib"] = (replies["hour"] + 7) % 24
replies["month"] = replies["date"].dt.to_period("M").dt.to_timestamp()
replies["dayofweek"] = replies["date"].dt.day_name()

print(f"  Replies: {len(replies):,}")

# ── 1. Reply Daily Volume ───────────────────────────────────────────
print("\n1. Reply daily volume...")
daily_vol = replies.groupby("date").agg(
    reply_count=("id", "count"),
    avg_sentiment_score=("sentiment_score", "mean")
).reset_index()
daily_vol = daily_vol.sort_values("date")
daily_vol.to_csv(f"{OUTPUT_DIR}/reply_daily_volume.csv", index=False)
print(f"   Saved → reply_daily_volume.csv ({len(daily_vol)} days)")

# ── 2. Reply Sentiment Trend ────────────────────────────────────────
print("\n2. Reply sentiment trend...")
daily_sent = replies.groupby(["date", "sentiment_normalized"]).size().reset_index(name="count")
daily_sent = daily_sent.pivot_table(index="date", columns="sentiment_normalized", values="count", fill_value=0).reset_index()
for col in ["negative", "neutral", "positive"]:
    if col not in daily_sent.columns:
        daily_sent[col] = 0
total = daily_sent["negative"] + daily_sent["neutral"] + daily_sent["positive"]
daily_sent["neg_pct"] = (daily_sent["negative"] / total * 100).round(2)
daily_sent["neu_pct"] = (daily_sent["neutral"] / total * 100).round(2)
daily_sent["pos_pct"] = (daily_sent["positive"] / total * 100).round(2)
daily_sent = daily_sent.sort_values("date")
daily_sent.to_csv(f"{OUTPUT_DIR}/reply_sentiment_trend.csv", index=False)
print(f"   Saved → reply_sentiment_trend.csv ({len(daily_sent)} days)")
print(f"   Overall: neg={daily_sent['neg_pct'].mean():.1f}% neu={daily_sent['neu_pct'].mean():.1f}% pos={daily_sent['pos_pct'].mean():.1f}%")

# ── 3. Reply Hourly Pattern (WIB) ───────────────────────────────────
print("\n3. Reply hourly pattern (WIB)...")
hourly = replies.groupby("hour_wib").agg(
    reply_count=("id", "count"),
    neg_pct=("sentiment_normalized", lambda x: (x == "negative").mean() * 100)
).reset_index()
hourly.to_csv(f"{OUTPUT_DIR}/reply_hourly_pattern.csv", index=False)
print(f"   Saved → reply_hourly_pattern.csv")
peak_hour = hourly.loc[hourly["reply_count"].idxmax()]
print(f"   Peak hour: {int(peak_hour['hour_wib'])}:00 WIB ({int(peak_hour['reply_count']):,} replies)")

# ── 4. Reply Weekly Pattern ─────────────────────────────────────────
print("\n4. Reply weekly pattern...")
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekly = replies.groupby("dayofweek").agg(
    reply_count=("id", "count"),
    neg_pct=("sentiment_normalized", lambda x: (x == "negative").mean() * 100)
).reset_index()
weekly["dayofweek"] = pd.Categorical(weekly["dayofweek"], categories=dow_order, ordered=True)
weekly = weekly.sort_values("dayofweek")
weekly.to_csv(f"{OUTPUT_DIR}/reply_weekly_pattern.csv", index=False)
print(f"   Saved → reply_weekly_pattern.csv")
print(weekly.to_string(index=False))

print("\n=== TEMPORAL REPLY ANALYSIS COMPLETE ===")
