#!/usr/bin/env python3
"""Bot Detection — Multi-signal composite scoring with near-duplicate detection."""
import pandas as pd
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time

ANALYSIS_DIR = "/opt/mbg/data/analysis"
OUTPUT_DIR = ANALYSIS_DIR
BOT_THRESHOLD = 0.50

print("Loading data...")
t0 = time.time()
df = pd.read_csv(f"{ANALYSIS_DIR}/replies_with_sentiment.csv",
                 usecols=["user_screen_name", "user_id", "created_at", "text",
                          "favorite_count", "retweet_count", "reply_count",
                          "sentiment_label", "tweet_type"])
df["created_at"] = pd.to_datetime(df["created_at"])
df["user"] = df["user_screen_name"].fillna(df["user_id"].astype(str))
print(f"  Loaded {len(df):,} rows, {df['user'].nunique():,} unique users ({time.time()-t0:.1f}s)")

# ── Signal 1: Username Anomaly ──────────────────────────────────────
print("\n1. Username anomaly signal...")
def username_score(name):
    if pd.isna(name) or name == "":
        return 0.5
    name = str(name)
    digit_ratio = len(re.findall(r"\d", name)) / max(len(name), 1)
    has_pattern = bool(re.match(r"^[a-zA-Z]+\d{5,}$", name))
    is_very_short = len(name) < 6
    score = 0.5 * digit_ratio + 0.3 * has_pattern + 0.2 * is_very_short
    return min(score, 1.0)

df["username_score"] = df["user_screen_name"].apply(username_score)

# ── Signal 2: Temporal Pattern ──────────────────────────────────────
print("2. Temporal pattern signal...")
def temporal_features(group):
    hours = group["created_at"].dt.hour
    hour_coverage = hours.nunique() / 24.0
    if len(group) < 3:
        return pd.Series({"hour_coverage": hour_coverage, "regularity": 0.5, "tweet_count": len(group)})
    intervals = group["created_at"].sort_values().diff().dt.total_seconds().dropna()
    if len(intervals) < 2:
        regularity = 0.5
    else:
        cv = intervals.std() / (intervals.mean() + 1)
        regularity = max(0, 1 - cv / 10)
    return pd.Series({"hour_coverage": hour_coverage, "regularity": regularity, "tweet_count": len(group)})

temporal = df.groupby("user").apply(temporal_features).reset_index()
temporal["temporal_score"] = 0.6 * temporal["hour_coverage"] + 0.4 * temporal["regularity"]

# ── Signal 3: Content Diversity (Near-Duplicate Detection) ──────────
print("3. Content diversity signal (near-duplicate detection)...")
def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["text_norm"] = df["text"].apply(normalize_text)

def content_score(group):
    texts = group["text_norm"].tolist()
    if len(texts) < 3:
        return 0.5
    exact_dup_ratio = 1 - (len(set(texts)) / len(texts))
    if len(texts) <= 20:
        sample_texts = texts
    else:
        np.random.seed(42)
        idx = np.random.choice(len(texts), 20, replace=False)
        sample_texts = [texts[i] for i in idx]
    try:
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        tfidf = vectorizer.fit_transform(sample_texts)
        sim = cosine_similarity(tfidf)
        np.fill_diagonal(sim, 0)
        avg_sim = sim.mean()
        near_dup_score = min(avg_sim * 2, 1.0)
    except:
        near_dup_score = exact_dup_ratio
    return 0.4 * exact_dup_ratio + 0.6 * near_dup_score

content_scores = df.groupby("user").apply(content_score).reset_index()
content_scores.columns = ["user", "content_score"]

# ── Signal 4: Engagement Ratio ──────────────────────────────────────
print("4. Engagement ratio signal...")
engagement = df.groupby("user").agg(
    tweet_count=("user", "count"),
    total_favs=("favorite_count", "sum"),
    total_rts=("retweet_count", "sum"),
).reset_index()
engagement["avg_fav"] = engagement["total_favs"] / engagement["tweet_count"]
engagement["engagement_score"] = np.where(
    engagement["avg_fav"] == 0, 1.0,
    np.where(engagement["avg_fav"] < 0.1, 0.8,
             np.where(engagement["avg_fav"] < 1, 0.5,
                      np.where(engagement["avg_fav"] < 5, 0.2, 0.0)))
)

# ── Signal 5: Activity Intensity ────────────────────────────────────
print("5. Activity intensity signal...")
activity = df.groupby("user")["created_at"].agg(["min", "max", "count"]).reset_index()
activity.columns = ["user", "first_post", "last_post", "tweet_count"]
activity["span_days"] = (activity["last_post"] - activity["first_post"]).dt.days + 1
activity["tweets_per_day"] = activity["tweet_count"] / activity["span_days"].clip(lower=1)
activity["intensity_score"] = activity["tweets_per_day"].clip(upper=10) / 10.0

# ── Composite Score ─────────────────────────────────────────────────
print("\nComputing composite bot scores...")
scores = temporal[["user", "temporal_score", "tweet_count"]].merge(
    content_scores, on="user", how="outer"
).merge(
    engagement[["user", "engagement_score", "avg_fav", "total_favs", "total_rts"]], on="user", how="outer"
).merge(
    activity[["user", "intensity_score", "tweets_per_day", "span_days"]], on="user", how="outer"
)

usernames = df.groupby("user")["user_screen_name"].first().reset_index()
usernames.columns = ["user", "user_screen_name"]
scores = scores.merge(usernames, on="user", how="left")

scores["username_score"] = scores["user_screen_name"].apply(username_score)
scores["content_score"] = scores["content_score"].fillna(0.5)
scores["temporal_score"] = scores["temporal_score"].fillna(0.5)
scores["engagement_score"] = scores["engagement_score"].fillna(0.5)
scores["intensity_score"] = scores["intensity_score"].fillna(0.5)
scores["avg_fav"] = scores["avg_fav"].fillna(0)
scores["tweets_per_day"] = scores["tweets_per_day"].fillna(0)
scores["span_days"] = scores["span_days"].fillna(1)
scores["tweet_count"] = scores["tweet_count"].fillna(1)

scores["bot_score"] = (
    0.20 * scores["username_score"] +
    0.20 * scores["temporal_score"] +
    0.25 * scores["content_score"] +
    0.20 * scores["engagement_score"] +
    0.15 * scores["intensity_score"]
)
scores["bot_score"] = scores["bot_score"].round(4)
scores["is_bot"] = scores["bot_score"] >= BOT_THRESHOLD

# ── Save Outputs ────────────────────────────────────────────────────
print(f"\nSaving outputs (threshold={BOT_THRESHOLD})...")
output_cols = ["user", "user_screen_name", "bot_score", "is_bot",
               "username_score", "temporal_score", "content_score",
               "engagement_score", "intensity_score",
               "tweet_count", "avg_fav", "tweets_per_day", "span_days"]
scores[output_cols].to_csv(f"{OUTPUT_DIR}/user_bot_scores.csv", index=False)
print(f"  Saved → user_bot_scores.csv ({len(scores):,} users)")

flagged = scores[scores["is_bot"]].sort_values("bot_score", ascending=False)
flagged[output_cols].to_csv(f"{OUTPUT_DIR}/flagged_bots.csv", index=False)
print(f"  Saved → flagged_bots.csv ({len(flagged):,} flagged bots)")

print(f"\n=== BOT DETECTION COMPLETE ({time.time()-t0:.1f}s) ===")
print(f"  Total users: {len(scores):,}")
print(f"  Flagged bots: {len(flagged):,} ({len(flagged)/len(scores)*100:.1f}%)")
print(f"  Score distribution:")
print(f"    Mean: {scores['bot_score'].mean():.3f}")
print(f"    Median: {scores['bot_score'].median():.3f}")
print(f"    Max: {scores['bot_score'].max():.3f}")
