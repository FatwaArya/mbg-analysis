#!/usr/bin/env python3
"""R1: JSONL → CSV conversion"""
import json, sys, csv

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample.jsonl"
OUTPUT = INPUT.replace(".jsonl", ".csv")

records = []
with open(INPUT, "r") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            user = obj.pop("user", {}) or {}
            records.append({
                "id": obj.get("id"),
                "text": obj.get("text"),
                "created_at": obj.get("created_at"),
                "lang": obj.get("lang"),
                "favorite_count": obj.get("favorite_count", 0),
                "retweet_count": obj.get("retweet_count", 0),
                "reply_count": obj.get("reply_count", 0),
                "user_id": user.get("id"),
                "user_screen_name": user.get("screen_name"),
                "user_name": user.get("name"),
                "parent_id": obj.get("parent_id"),
                "parent_user_screen_name": obj.get("parent_user_screen_name"),
                "scrape_source": obj.get("scrape_source"),
                "tweet_type": "reply",
            })
        except Exception as e:
            print(f"Parse error: {e}", file=sys.stderr)

# Write CSV
with open(OUTPUT, "w", newline="") as f:
    if records:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

print(f"Converted {len(records)} rows → {OUTPUT}")
