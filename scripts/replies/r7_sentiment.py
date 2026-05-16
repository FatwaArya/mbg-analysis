#!/usr/bin/env python3
"""R7: Sentiment classification for replies"""
import pandas as pd
from transformers import pipeline
from tqdm import tqdm
import sys

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample_preprocessed.csv"
OUTPUT = INPUT.replace("_preprocessed.csv", "_sentiment.csv")
BATCH_SIZE = 32

df = pd.read_csv(INPUT)
print(f"Input: {len(df)} replies")

print("Loading Indonesian sentiment model...")
sentiment_id = pipeline("text-classification", model="w11wo/indonesian-roberta-base-sentiment-classifier", device=-1, batch_size=BATCH_SIZE)

print("Loading English sentiment model...")
sentiment_en = pipeline("text-classification", model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=-1, batch_size=BATCH_SIZE)

ID_MAP = {"positive": "positive", "negative": "negative", "neutral": "neutral", "pos": "positive", "neg": "negative", "neu": "neutral"}
EN_MAP = {"positive": "positive", "negative": "negative", "neutral": "neutral", "label_0": "negative", "label_1": "neutral", "label_2": "positive"}

def run_batch(texts, model, label_map, label=""):
    labels, scores = [], []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in tqdm(range(0, len(texts), BATCH_SIZE), total=total_batches, desc=f"Sentiment {label}"):
        batch = [str(t)[:512] for t in texts[i:i+BATCH_SIZE]]
        try:
            results = model(batch)
            for r in results:
                labels.append(label_map.get(r["label"].lower(), "neutral"))
                scores.append(r["score"])
        except Exception as e:
            print(f"Batch {i} error: {e}")
            labels.extend(["neutral"] * len(batch))
            scores.extend([0.0] * len(batch))
    return labels, scores

id_mask = df["detected_lang"] != "en"
en_mask = df["detected_lang"] == "en"
id_df = df[id_mask].copy()
en_df = df[en_mask].copy()

print(f"Indonesian: {len(id_df)} | English: {len(en_df)}")

if len(id_df) > 0:
    labels, scores = run_batch(id_df["text_clean_light"].fillna("").tolist(), sentiment_id, ID_MAP, "id")
    id_df["sentiment_label"] = labels
    id_df["sentiment_score"] = scores
    id_df["sentiment_normalized"] = labels

if len(en_df) > 0:
    labels, scores = run_batch(en_df["text_clean_light"].fillna("").tolist(), sentiment_en, EN_MAP, "en")
    en_df["sentiment_label"] = labels
    en_df["sentiment_score"] = scores
    en_df["sentiment_normalized"] = labels

result = pd.concat([id_df, en_df], ignore_index=True)
result.to_csv(OUTPUT, index=False)

print(f"\nSentiment complete → {OUTPUT}")
print(result["sentiment_normalized"].value_counts().to_string())
