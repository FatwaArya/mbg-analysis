#!/usr/bin/env python3
import json
import hashlib
import os
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # FIX: allow importing runtime from repo root.
from runtime import RUNTIME

def get_file_metadata(filepath):
    """Compute file metadata: rows, size, MD5 hash"""
    if not os.path.exists(filepath):
        return None
    
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    # Count rows (CSV files)
    rows = 0
    if filepath.endswith('.csv'):
        with open(filepath, 'r') as f:
            rows = sum(1 for _ in f) - 1  # Exclude header
    
    # Compute MD5
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    
    return {
        "rows": rows,
        "size_mb": round(size_mb, 2),
        "md5": md5.hexdigest()[:8]
    }

def extract_stats(data_dir=RUNTIME.data_dir):
    """Extract statistics from output files"""
    stats = {}
    
    # Sentiment distribution
    sentiment_file = f"{data_dir}/output/tweets_with_sentiment.csv"
    if os.path.exists(sentiment_file):
        df = pd.read_csv(sentiment_file)
        stats["total_tweets"] = len(df)
        if "sentiment_normalized" in df.columns:
            dist = df["sentiment_normalized"].value_counts().to_dict()
            stats["sentiment"] = {
                "negative": dist.get("negative", 0),
                "neutral": dist.get("neutral", 0),
                "positive": dist.get("positive", 0)
            }
    
    # Topic info
    topic_file = f"{data_dir}/output/topic_info.csv"
    if os.path.exists(topic_file):
        df = pd.read_csv(topic_file)
        stats["topics_discovered"] = len(df)
    
    # Outliers from topics file
    topics_file = f"{data_dir}/output/tweets_with_topics.csv"
    if os.path.exists(topics_file):
        df = pd.read_csv(topics_file)
        if "topic_id" in df.columns:
            # FIX: outlier topic column is topic_id, not topic.
            stats["outliers"] = (df["topic_id"] == -1).sum()
    
    return stats

def get_git_commit():
    """Get current git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except:
        return "unknown"

def generate_manifest(run_id, duration_seconds, data_dir=RUNTIME.data_dir, status="success"):
    """Build complete manifest JSON"""
    
    files = {}
    for name, filename in [
        ("tweets_with_sentiment", "tweets_with_sentiment.csv"),
        ("tweets_with_topics", "tweets_with_topics.csv"),
        ("topic_info", "topic_info.csv")
    ]:
        filepath = f"{data_dir}/output/{filename}"
        metadata = get_file_metadata(filepath)
        if metadata:
            files[name] = {
                "path": f"runs/{run_id}/{filename}",
                **metadata
            }
    
    manifest = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "git_commit": get_git_commit(),
        "duration_seconds": duration_seconds,
        "status": status,
        "files": files,
        "stats": extract_stats(data_dir)
    }
    
    return manifest

if __name__ == "__main__":
    import sys
    
    # Demo: generate manifest from current output files
    run_id = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y%m%d_%H%M%S")
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    manifest = generate_manifest(run_id, duration)
    
    # Save to output directory
    output_path = f"{RUNTIME.output_dir}/metadata.json"  # FIX: centralize runtime output path.
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✓ Manifest generated: {output_path}")
    print(f"  Run ID: {manifest['run_id']}")
    print(f"  Files: {len(manifest['files'])}")
    print(f"  Total tweets: {manifest['stats'].get('total_tweets', 0):,}")
