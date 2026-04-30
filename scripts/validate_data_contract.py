"""
scripts/validate_data_contract.py
Validates all required data files exist with correct columns
before launching the dashboard.
Run: python3 scripts/validate_data_contract.py
"""

import pandas as pd
import sys
import os

os.makedirs("data/analysis", exist_ok=True)

REQUIRED = {
    "data/analysis/daily_volume.csv": ["date", "tweet_count"],
    "data/analysis/hourly_pattern.csv": ["hour", "tweet_count"],
    "data/analysis/sentiment_overall.csv": ["sentiment", "count"],
    "data/analysis/sentiment_weekly.csv": ["date", "sentiment", "count"],
    "data/analysis/sentiment_engagement.csv": ["sentiment", "mean", "median"],
    "data/analysis/topic_prevalence.csv": ["Topic", "Count", "Name"],
    "data/analysis/topic_weekly.csv": ["date", "topic_id", "count"],
    "data/analysis/top_engaging_tweets.csv": ["text", "date", "sentiment", "engagement_total"],
    "data/analysis/query_effectiveness.csv": ["query_raw", "tweet_count", "avg_engagement"],
    "data/processed/tweets_with_topics.csv": ["text", "date", "sentiment_normalized", "topic_id", "detected_lang"],
    "data/processed/topic_info.csv": ["Topic", "Count", "Name"],
}

print("=== DATA CONTRACT VALIDATION ===\n")
all_ok = True

for filepath, required_cols in REQUIRED.items():
    try:
        df = pd.read_csv(filepath, nrows=5)
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            print(f"❌ {filepath}")
            print(f"   Missing columns: {missing_cols}")
            print(f"   Has columns: {list(df.columns)}")
            all_ok = False
        else:
            print(f"✅ {filepath} ({len(required_cols)} cols OK)")
    except FileNotFoundError:
        print(f"❌ {filepath} — FILE NOT FOUND")
        all_ok = False
    except Exception as e:
        print(f"❌ {filepath} — ERROR: {e}")
        all_ok = False

print("\n" + "=" * 40)
if all_ok:
    print("ALL FILES VALID — safe to launch dashboard")
    sys.exit(0)
else:
    print("VALIDATION FAILED — fix issues above before launching")
    sys.exit(1)
