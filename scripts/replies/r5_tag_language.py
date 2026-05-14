#!/usr/bin/env python3
"""R5: Language detection and model routing"""
import pandas as pd
from langdetect import detect, DetectorFactory
import sys

DetectorFactory.seed = 42

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample_filtered.csv"
OUTPUT = INPUT.replace("_filtered.csv", "_tagged.csv")

df = pd.read_csv(INPUT)

def detect_safe(text):
    try:
        return detect(str(text))
    except:
        return "id"

null_lang = df["lang"].isna()
print(f"Detecting language for {null_lang.sum()} rows...")
df.loc[null_lang, "detected_lang"] = df.loc[null_lang, "text"].apply(detect_safe)
df.loc[~null_lang, "detected_lang"] = df.loc[~null_lang, "lang"]

df["sentiment_model"] = df["detected_lang"].apply(
    lambda x: "cardiffnlp/twitter-roberta-base-sentiment-latest" if x == "en" 
    else "w11wo/indonesian-roberta-base-sentiment-classifier"
)

df.to_csv(OUTPUT, index=False)
print(f"\nLanguage tagging → {OUTPUT}")
print(df["detected_lang"].value_counts().to_string())
