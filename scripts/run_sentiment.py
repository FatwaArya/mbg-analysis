import pandas as pd
from transformers import pipeline
from tqdm import tqdm
import os
import logging

# Setup unified logging
LOG_DIR = "/opt/mbg/logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"{LOG_DIR}/run_sentiment.py.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

os.makedirs("/opt/mbg/data/output", exist_ok=True)
df = pd.read_csv("/opt/mbg/data/processed/tweets_relevant_tagged.csv")
log.info(f"Running sentiment on {len(df):,} tweets...")

log.info("Loading Indonesian model (w11wo)...")
sentiment_id = pipeline("text-classification",
    model="w11wo/indonesian-roberta-base-sentiment-classifier", device=-1, batch_size=32)

log.info("Loading English model (cardiffnlp)...")
sentiment_en = pipeline("text-classification",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest", device=-1, batch_size=32)

id_df = df[df["detected_lang"] != "en"].copy()
en_df = df[df["detected_lang"] == "en"].copy()
log.info(f"Indonesian : {len(id_df):,} | English : {len(en_df):,}")

def run_batch(model, texts, batch_size=32):
    results = []
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = [str(t)[:512] for t in texts[i:i+batch_size]]
        try:
            results.extend(model(batch))
        except Exception as e:
            log.error(f"Batch error at {i}: {e}")
            results.extend([{"label": "neutral", "score": 0.0}] * len(batch))
    return results

log.info("\nRunning Indonesian sentiment...")
id_res = run_batch(sentiment_id, id_df["text"].tolist())
id_df["sentiment_label"] = [r["label"].lower() for r in id_res]
id_df["sentiment_score"] = [r["score"] for r in id_res]

log.info("Running English sentiment...")
en_res = run_batch(sentiment_en, en_df["text"].tolist())
en_df["sentiment_label"] = [r["label"].lower() for r in en_res]
en_df["sentiment_score"] = [r["score"] for r in en_res]

df_out = pd.concat([id_df, en_df], ignore_index=True)

# Normalize labels from both models
label_map = {
    "positive": "positive", "negative": "negative", "neutral": "neutral",
    "label_0": "negative", "label_1": "neutral", "label_2": "positive"
}
df_out["sentiment_normalized"] = df_out["sentiment_label"].map(
    lambda x: label_map.get(x, x)
)

df_out.to_csv("/opt/mbg/data/output/tweets_with_sentiment.csv", index=False)
log.info("\n=== SENTIMENT COMPLETE ===")
log.info(df_out["sentiment_normalized"].value_counts().to_string())
