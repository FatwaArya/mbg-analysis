"""
scripts/validate_data_contract.py
Validate pipeline outputs and optional analysis outputs.
Run: python3 scripts/validate_data_contract.py [--analysis]
"""

import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # FIX: allow importing runtime from repo root.
from runtime import RUNTIME

PIPELINE_REQUIRED = {
    f"{RUNTIME.output_dir}/tweets_with_sentiment.csv": [
        "text", "date", "sentiment_normalized", "detected_lang"
    ],
    f"{RUNTIME.output_dir}/tweets_with_topics.csv": [
        "text", "date", "sentiment_normalized", "topic_id", "detected_lang"
    ],
    f"{RUNTIME.output_dir}/topic_info.csv": ["Topic", "Count", "Name"],
}

ANALYSIS_REQUIRED = {
    "data/analysis/daily_volume.csv": ["date", "tweet_count"],
    "data/analysis/hourly_pattern.csv": ["hour", "tweet_count"],
    "data/analysis/sentiment_overall.csv": ["sentiment", "count"],
    "data/analysis/sentiment_weekly.csv": ["date", "sentiment", "count"],
    "data/analysis/sentiment_engagement.csv": ["sentiment", "mean", "median"],
    "data/analysis/topic_prevalence.csv": ["Topic", "Count", "Name"],
    "data/analysis/topic_weekly.csv": ["date", "topic_id", "count"],
    "data/analysis/top_engaging_tweets.csv": ["text", "date", "sentiment", "engagement_total"],
    "data/analysis/query_effectiveness.csv": ["query_raw", "tweet_count", "avg_engagement"],
}


def _validate_required(required: dict[str, list[str]], label: str) -> bool:
    print(f"=== {label} ===\n")
    all_ok = True
    for filepath, required_cols in required.items():
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
    print()
    return all_ok


def validate_pipeline_outputs() -> bool:
    # FIX: validate only files produced by the pipeline itself.
    return _validate_required(PIPELINE_REQUIRED, "PIPELINE OUTPUT VALIDATION")


def validate_analysis_outputs() -> bool:
    # FIX: analysis validation is optional and meant for post-analysis checks.
    os.makedirs("data/analysis", exist_ok=True)
    return _validate_required(ANALYSIS_REQUIRED, "ANALYSIS OUTPUT VALIDATION")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MBG data contracts")
    parser.add_argument(
        "--analysis",
        action="store_true",
        help="Also validate optional post-analysis CSV outputs",
    )
    args = parser.parse_args()

    pipeline_ok = validate_pipeline_outputs()
    analysis_ok = True
    if args.analysis:
        analysis_ok = validate_analysis_outputs()

    all_ok = pipeline_ok and analysis_ok
    print("=" * 40)
    if all_ok:
        print("VALIDATION PASSED")
        return 0
    print("VALIDATION FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
