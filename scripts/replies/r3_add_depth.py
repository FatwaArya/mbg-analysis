#!/usr/bin/env python3
"""R3: Add depth column"""
import pandas as pd
import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample_enriched.csv"
PARENTS = "/opt/mbg/data/output/tweets_relevant.csv"
OUTPUT = INPUT.replace("_enriched.csv", "_depth.csv")

replies = pd.read_csv(INPUT, dtype={"id": str, "parent_id": str})
parents = pd.read_csv(PARENTS, dtype={"id": str}, usecols=["id"])

parent_ids = set(parents["id"].astype(str))
reply_ids = set(replies["id"].astype(str))

def classify_depth(pid):
    pid = str(pid)
    if pid in parent_ids:
        return 1
    elif pid in reply_ids:
        return 2
    return 0

replies["depth"] = replies["parent_id"].apply(classify_depth)
replies.to_csv(OUTPUT, index=False)

depth_counts = replies["depth"].value_counts().sort_index()
print(f"Depth classification → {OUTPUT}")
for d, c in depth_counts.items():
    print(f"  Depth {d}: {c}")
