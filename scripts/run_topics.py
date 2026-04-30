import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os
import logging
import numpy as np

# Setup unified logging
LOG_DIR = "/opt/mbg/logs"
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

os.makedirs("/opt/mbg/data/output", exist_ok=True)
df = pd.read_csv("/opt/mbg/data/output/tweets_with_sentiment.csv")
id_df = df[df["detected_lang"] != "en"].copy()
docs = id_df["text"].str[:512].tolist()

log.info(f"Topic modeling on {len(docs):,} Indonesian tweets...")
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

log.info("Computing embeddings...")
embeddings = embed_model.encode(docs, batch_size=64, show_progress_bar=True)

topic_model = BERTopic(
    embedding_model=embed_model,
    language="multilingual",
    calculate_probabilities=True,
    verbose=True,
    nr_topics="auto",
    min_topic_size=50
)

topics, probs = topic_model.fit_transform(docs, embeddings)
id_df["topic_id"] = topics
id_df["topic_prob"] = probs.max(axis=1) if hasattr(probs, "max") else probs

topic_info = topic_model.get_topic_info()
topic_info.to_csv("/opt/mbg/data/output/topic_info.csv", index=False)
id_df.to_csv("/opt/mbg/data/output/tweets_with_topics.csv", index=False)
topic_model.save("/opt/mbg/data/output/bertopic_model")

log.info(f"\nTopics found : {topic_info['Topic'].nunique()}")
log.info(topic_info.head(15).to_string())
