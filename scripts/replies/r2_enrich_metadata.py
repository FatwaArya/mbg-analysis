#!/usr/bin/env python3
"""R2: Fill missing metadata from parent join"""
import pandas as pd
import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample.csv"
PARENTS = "/opt/mbg/data/output/tweets_relevant.csv"
OUTPUT = INPUT.replace(".csv", "_enriched.csv")

replies = pd.read_csv(INPUT, dtype={"id": str, "parent_id": str})
parents = pd.read_csv(PARENTS, dtype={"id": str}, usecols=["id", "created_at", "lang", "date", "hour", "query_raw", "scrape_tab"])

parent_meta = parents.rename(columns={
    "id": "parent_id",
    "created_at": "parent_created_at",
    "lang": "parent_lang",
    "date": "parent_date",
    "hour": "parent_hour",
    "query_raw": "parent_query_raw",
    "scrape_tab": "parent_scrape_tab",
})

replies = replies.merge(parent_meta, on="parent_id", how="left")
replies["created_at"] = replies["created_at"].fillna(replies["parent_created_at"])
replies["lang"] = replies["lang"].fillna(replies["parent_lang"])

replies["created_at"] = pd.to_datetime(replies["created_at"], errors="coerce")
replies["date"] = replies["created_at"].dt.date.astype(str)
replies["hour"] = replies["created_at"].dt.hour
replies["date"] = replies["date"].fillna(replies["parent_date"])
replies["hour"] = replies["hour"].fillna(replies["parent_hour"])

replies = replies.drop(columns=["parent_created_at", "parent_lang", "parent_date", "parent_hour", "parent_query_raw", "parent_scrape_tab"], errors="ignore")
replies.to_csv(OUTPUT, index=False)

print(f"Enriched {len(replies)} rows → {OUTPUT}")
print(f"Nulls: created_at={replies['created_at'].isna().sum()}, lang={replies['lang'].isna().sum()}, date={replies['date'].isna().sum()}")
