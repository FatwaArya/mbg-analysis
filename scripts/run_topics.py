import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os

os.makedirs("/opt/mbg/data/output", exist_ok=True)
df = pd.read_csv("/opt/mbg/data/output/tweets_with_sentiment.csv")
id_df = df[df["detected_lang"] != "en"].copy()
docs = id_df["text"].str[:512].tolist()

print(f"Topic modeling on {len(docs):,} Indonesian tweets...")
embed_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

topic_model = BERTopic(
    embedding_model=embed_model,
    language="multilingual",
    calculate_probabilities=True,
    verbose=True,
    nr_topics="auto",
    min_topic_size=50
)

topics, probs = topic_model.fit_transform(docs)
id_df["topic_id"] = topics
id_df["topic_prob"] = probs.max(axis=1) if hasattr(probs, "max") else probs

topic_info = topic_model.get_topic_info()
topic_info.to_csv("/opt/mbg/data/output/topic_info.csv", index=False)
id_df.to_csv("/opt/mbg/data/output/tweets_with_topics.csv", index=False)
topic_model.save("/opt/mbg/data/output/bertopic_model")

print(f"\nTopics found : {topic_info['Topic'].nunique()}")
print(topic_info.head(15).to_string())
