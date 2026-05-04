import pandas as pd
import numpy as np
from scipy import stats
import os

os.makedirs("data/analysis", exist_ok=True)

# Load whichever enriched file is available
for path in [
    "data/processed/tweets_with_sentiment.csv",
    "data/processed/tweets_relevant_tagged.csv",
    "data/processed/tweets_clean.csv",
]:
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"Loaded: {path} ({len(df):,} rows)")
        break
if "df" not in locals():
    # FIX: emit clear insufficient-data state when no source file exists.
    print("No input file found. Writing empty temporal outputs.")
    pd.DataFrame(columns=["date", "tweet_count", "total_engagement", "avg_engagement", "total_retweets",
                          "rolling_mean", "rolling_std", "z_score", "is_spike"]).to_csv(
        "data/analysis/daily_volume_spikes.csv", index=False
    )
    pd.DataFrame([{
        "n_spike_days": 0,
        "peak_spike_date": "N/A",
        "peak_spike_tweets": 0,
        "peak_spike_z_score": 0,
        "weekly_trend": "insufficient data",
        "trend_p_value": "insufficient data",
    }]).to_csv("data/analysis/temporal_spike_summary.csv", index=False)
    # FIX: continue with an empty frame instead of raising.
    df = pd.DataFrame(columns=[
        "id", "date", "engagement_total", "retweet_count", "reply_count",
        "favorite_count", "sentiment_normalized", "text"
    ])

df["date"] = pd.to_datetime(df["date"])
df = df[df["date"] >= "2025-01-01"]

# ── 1. Daily volume + rolling baseline ───────────────────────────────────────
daily = df.groupby("date").agg(
    tweet_count=("id", "count"),
    total_engagement=("engagement_total", "sum"),
    avg_engagement=("engagement_total", "mean"),
    total_retweets=("retweet_count", "sum"),
).reset_index()

# Z-score spike detection (>2 std above 7-day rolling mean)
daily["rolling_mean"] = daily["tweet_count"].rolling(7, min_periods=1).mean()
daily["rolling_std"]  = daily["tweet_count"].rolling(7, min_periods=1).std().fillna(1)
daily["z_score"]      = (daily["tweet_count"] - daily["rolling_mean"]) / daily["rolling_std"]
daily["is_spike"]     = daily["z_score"] > 2.0

daily.to_csv("data/analysis/daily_volume_spikes.csv", index=False)

spikes = daily[daily["is_spike"]].sort_values("tweet_count", ascending=False)
print(f"\n1. SPIKE DAYS DETECTED: {len(spikes)}")
print(spikes[["date", "tweet_count", "z_score", "total_engagement"]].to_string(index=False))

# ── 2. Organic vs amplification on spike days ────────────────────────────────
spike_dates = spikes["date"].tolist()
df["is_spike_day"] = df["date"].isin(spike_dates)

amplify = df.groupby("is_spike_day").agg(
    avg_retweets=("retweet_count", "mean"),
    avg_replies=("reply_count", "mean"),
    avg_likes=("favorite_count", "mean"),
    avg_engagement=("engagement_total", "mean"),
).round(2)
amplify.to_csv("data/analysis/spike_vs_normal_engagement.csv")
print(f"\n2. SPIKE vs NORMAL ENGAGEMENT\n{amplify.to_string()}")

# ── 3. Sentiment on spike days (if available) ────────────────────────────────
if "sentiment_normalized" in df.columns:
    spike_sent = df[df["is_spike_day"]]["sentiment_normalized"].value_counts(normalize=True) * 100
    normal_sent = df[~df["is_spike_day"]]["sentiment_normalized"].value_counts(normalize=True) * 100
    sent_compare = pd.DataFrame({"spike_%": spike_sent, "normal_%": normal_sent}).round(1)
    sent_compare.to_csv("data/analysis/spike_sentiment_comparison.csv")
    print(f"\n3. SENTIMENT ON SPIKE vs NORMAL DAYS\n{sent_compare.to_string()}")

# ── 4. Weekly trend + Mann-Kendall direction ─────────────────────────────────
weekly = df.resample("W", on="date").size().reset_index(name="count")
# Simple linear trend
if len(weekly) >= 2:
    slope, intercept, r, p, _ = stats.linregress(range(len(weekly)), weekly["count"])
    trend_dir = "increasing" if slope > 0 else "decreasing"
else:
    # FIX: avoid linregress crash when less than 2 weekly points exist.
    slope, p = np.nan, np.nan
    trend_dir = "insufficient data"
weekly.to_csv("data/analysis/weekly_volume_trend.csv", index=False)
if np.isnan(slope):
    print("\n4. WEEKLY TREND: insufficient data")
else:
    print(f"\n4. WEEKLY TREND: {trend_dir} (slope={slope:.1f}, p={p:.4f})")

# ── 5. Top content on spike days ─────────────────────────────────────────────
top_spike = (
    df[df["is_spike_day"]]
    .nlargest(20, "engagement_total")
    [["id", "text", "date", "engagement_total", "retweet_count", "reply_count"]]
)
top_spike.to_csv("data/analysis/top_posts_spike_days.csv", index=False)
if len(top_spike) > 0:
    print(f"\n5. Top spike-day post engagement: {top_spike['engagement_total'].iloc[0]:,}")
else:
    # FIX: avoid iloc crash when spike-day slice is empty.
    print("\n5. Top spike-day post engagement: insufficient data")

# ── 6. Summary ───────────────────────────────────────────────────────────────
summary = {
    "n_spike_days": int(len(spikes)),
    "peak_spike_date": str(spikes["date"].iloc[0].date()) if len(spikes) else "N/A",
    "peak_spike_tweets": int(spikes["tweet_count"].iloc[0]) if len(spikes) else 0,
    "peak_spike_z_score": round(float(spikes["z_score"].iloc[0]), 2) if len(spikes) else 0,
    "weekly_trend": trend_dir,
    "trend_p_value": round(p, 4) if not np.isnan(p) else "insufficient data",
}
pd.DataFrame([summary]).to_csv("data/analysis/temporal_spike_summary.csv", index=False)
print("\n=== TEMPORAL SPIKE ANALYSIS COMPLETE ===")
for k, v in summary.items():
    print(f"  {k:<35}: {v}")
print("Output -> data/analysis/")
