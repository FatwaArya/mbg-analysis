import pandas as pd
from transformers import pipeline
from tqdm import tqdm
import os
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # FIX: allow importing runtime from repo root.
from runtime import RUNTIME

# Setup unified logging
LOG_DIR = RUNTIME.logs_dir  # FIX: centralize runtime log path.
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

os.makedirs(RUNTIME.output_dir, exist_ok=True)  # FIX: centralize runtime output path.
input_candidates = [
    f"{RUNTIME.processed_dir}/tweets_preprocessed.csv",
    f"{RUNTIME.processed_dir}/tweets_relevant_tagged.csv",
]
input_path = next((p for p in input_candidates if os.path.exists(p)), input_candidates[-1])
df = pd.read_csv(input_path)
log.info(f"Running sentiment on {len(df):,} tweets...")
text_col = "text_clean_light" if "text_clean_light" in df.columns else "text"
# FIX: use preprocessed light text for sentiment with fallback to raw text.
log.info(f"Using text column: {text_col}")

log.info("Loading Indonesian model (w11wo)...")
sentiment_id = pipeline("text-classification",
    model="w11wo/indonesian-roberta-base-sentiment-classifier",
    device=RUNTIME.hf_device,  # FIX: runtime-controlled device selection.
    batch_size=RUNTIME.sentiment_batch_size)

log.info("Loading English model (cardiffnlp)...")
sentiment_en = pipeline("text-classification",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    device=RUNTIME.hf_device,  # FIX: runtime-controlled device selection.
    batch_size=RUNTIME.sentiment_batch_size)

id_df = df[df["detected_lang"] != "en"].copy()
en_df = df[df["detected_lang"] == "en"].copy()
log.info(f"Indonesian : {len(id_df):,} | English : {len(en_df):,}")

def run_batch(model, texts, batch_size):
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
id_res = run_batch(sentiment_id, id_df[text_col].tolist(), RUNTIME.sentiment_batch_size)
id_df["sentiment_label"] = [r["label"].lower() for r in id_res]
id_df["sentiment_score"] = [r["score"] for r in id_res]

log.info("Running English sentiment...")
en_res = run_batch(sentiment_en, en_df[text_col].tolist(), RUNTIME.sentiment_batch_size)
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

df_out.to_csv(f"{RUNTIME.output_dir}/tweets_with_sentiment.csv", index=False)
log.info("\n=== SENTIMENT COMPLETE ===")
log.info(df_out["sentiment_normalized"].value_counts().to_string())
