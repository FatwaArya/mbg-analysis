import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os
import logging
import numpy as np
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
        logging.FileHandler(f"{LOG_DIR}/run_topics.py.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

os.makedirs(RUNTIME.output_dir, exist_ok=True)  # FIX: centralize runtime output path.
df = pd.read_csv(f"{RUNTIME.output_dir}/tweets_with_sentiment.csv")
id_df = df[df["detected_lang"] != "en"].copy()
topic_text_col = "text_clean_topic" if "text_clean_topic" in id_df.columns else "text"
# FIX: use preprocessed topic text with fallback to raw text.
docs = id_df[topic_text_col].fillna(id_df["text"]).astype(str).str[:512].tolist()

log.info(f"Topic modeling on {len(docs):,} Indonesian tweets...")
if not docs:
    # FIX: handle empty Indonesian subset without crashing topic model training.
    full_df = df.copy()
    full_df["topic_id"] = -1
    full_df["topic_prob"] = np.nan
    topic_info = pd.DataFrame([{"Topic": -1, "Count": 0, "Name": "No topics"}])
    topic_info.to_csv(f"{RUNTIME.output_dir}/topic_info.csv", index=False)
    full_df.to_csv(f"{RUNTIME.output_dir}/tweets_with_topics.csv", index=False)
    log.info("No Indonesian documents found; wrote fallback topic outputs.")
    raise SystemExit(0)

embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2", device=RUNTIME.device)
# FIX: pass runtime-selected device to embedding model.

log.info("Computing embeddings...")
embeddings = embed_model.encode(
    docs,
    batch_size=RUNTIME.embedding_batch_size,  # FIX: runtime-specific embedding batch size.
    show_progress_bar=True,
)

topic_model = BERTopic(
    embedding_model=embed_model,
    language="multilingual",
    calculate_probabilities=False,  # FIX: disable heavy probability matrix by default.
    verbose=True,
    nr_topics="auto",
    min_topic_size=50
)

topics, _ = topic_model.fit_transform(docs, embeddings)
id_df["topic_id"] = topics
# FIX: lightweight topic confidence proxy without allocating full probability matrix.
id_df["topic_prob"] = np.where(id_df["topic_id"] == -1, np.nan, 1.0)

# FIX: preserve full dataset rows by merging topics back; non-ID rows become outliers.
full_df = df.copy()
full_df["topic_id"] = -1
full_df["topic_prob"] = np.nan
full_df.loc[id_df.index, "topic_id"] = id_df["topic_id"].values
full_df.loc[id_df.index, "topic_prob"] = id_df["topic_prob"].values

topic_info = topic_model.get_topic_info()
topic_info.to_csv(f"{RUNTIME.output_dir}/topic_info.csv", index=False)
full_df.to_csv(f"{RUNTIME.output_dir}/tweets_with_topics.csv", index=False)
topic_model.save(RUNTIME.model_save_dir)  # FIX: runtime-controlled model save path.

log.info(f"\nTopics found : {topic_info['Topic'].nunique()}")
log.info(topic_info.head(15).to_string())
