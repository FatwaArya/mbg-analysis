#!/usr/bin/env python3
"""R4: Filter unusable replies"""
import pandas as pd
import re, sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample_depth.csv"
OUTPUT = INPUT.replace("_depth.csv", "_filtered.csv")
REJECTED = INPUT.replace("_depth.csv", "_rejected.csv")

df = pd.read_csv(INPUT)
total = len(df)
rejected_rows = []

def reject(mask, reason):
    global df
    flagged = df[mask].copy()
    flagged["reject_reason"] = reason
    rejected_rows.append(flagged)
    df = df[~mask].copy()
    print(f"[{reason}] removed {mask.sum()}, remaining {len(df)}")

reject(df["text"].isna() | (df["text"].str.strip() == ""), "null_text")
reject(df["text"].str.split().str.len() < 3, "too_short")
reject(df.duplicated(subset=["text"], keep="first"), "duplicate")

spam = [r"follow\s*(back|4|f)", r"\bf4f\b|\bff\b", r"(http\S+\s*){3,}", r"(.)\1{5,}", r"(#\w+\s*){7,}"]
reject(df["text"].str.contains("|".join(spam), case=False, regex=True, na=False), "spam")

irrelevant = ["ja", "ko", "ar", "zh", "es", "fr", "de", "tr"]
reject(df["lang"].isin(irrelevant), "irrelevant_lang")

rejected_df = pd.concat(rejected_rows, ignore_index=True) if rejected_rows else pd.DataFrame()
rejected_df.to_csv(REJECTED, index=False)
df.to_csv(OUTPUT, index=False)

print(f"\nFiltered: {total} → {len(df)} kept, {len(rejected_df)} rejected")
print(f"Output: {OUTPUT}")
