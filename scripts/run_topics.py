import pandas as pd
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os
import logging
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import RUNTIME

# Setup unified logging
LOG_DIR = RUNTIME.logs_dir
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

os.makedirs(RUNTIME.output_dir, exist_ok=True)
df = pd.read_csv(f"{RUNTIME.output_dir}/tweets_with_sentiment.csv")

# ── Filter to Indonesian tweets only (English get topic_id=-1) ──
id_df = df[df["detected_lang"] != "en"].copy()
topic_text_col = "text_clean_topic" if "text_clean_topic" in id_df.columns else "text"
id_df["topic_text"] = id_df[topic_text_col].fillna(id_df["text"]).astype(str).str[:512]

# ── SPEC FIX: exclude tweets with <3 terms (applied to main corpus) ──
term_counts = id_df["topic_text"].str.split().str.len()
too_few_terms = term_counts < 3
log.info(f"Excluding {too_few_terms.sum()} tweets with <3 terms from topic modeling corpus")
id_df = id_df[~too_few_terms].copy()

docs = id_df["topic_text"].str.strip().tolist()

log.info(f"Topic modeling on {len(docs):,} Indonesian tweets (after <3 term filter)...")
if not docs:
    full_df = df.copy()
    full_df["topic_id"] = -1
    full_df["topic_prob"] = np.nan
    full_df["lda_topic_id"] = -1
    full_df["bertopic_subtopic"] = -1
    full_df["is_representative"] = False
    topic_info = pd.DataFrame([{"Topic": -1, "Count": 0, "Name": "No topics"}])
    topic_info.to_csv(f"{RUNTIME.output_dir}/topic_info.csv", index=False)
    full_df.to_csv(f"{RUNTIME.output_dir}/tweets_with_topics.csv", index=False)
    log.info("No documents after filtering; wrote fallback outputs.")
    raise SystemExit(0)

# ======================================================================
# STAGE 1: LDA with Gensim — search k=1..30, pick best by CV coherence
# ======================================================================
log.info("=" * 60)
log.info("STAGE 1: LDA topic modeling (k=1..30, CV coherence)")
log.info("=" * 60)

from gensim.corpora import Dictionary
from gensim.models import LdaModel, CoherenceModel

# Build corpus for LDA
tokenized_docs = [doc.lower().split() for doc in docs]
dictionary = Dictionary(tokenized_docs)
dictionary.filter_extremes(no_below=5, no_above=0.5)
corpus = [dictionary.doc2bow(doc) for doc in tokenized_docs]

# Search k=1..30 with CV coherence
best_k = 1
best_coherence = -1
coherence_scores = {}

for k in range(1, 31):
    lda_model = LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=k,
        alpha=0.5,
        eta="auto",          # beta=auto in gensim is eta="auto"
        passes=10,
        random_state=42,
    )
    cm = CoherenceModel(model=lda_model, texts=tokenized_docs, dictionary=dictionary, coherence="c_v")
    score = cm.get_coherence()
    coherence_scores[k] = score
    log.info(f"  k={k:2d}  CV coherence={score:.4f}")
    if score > best_coherence:
        best_coherence = score
        best_k = k

log.info(f"Best k={best_k} with CV coherence={best_coherence:.4f}")

# Train final LDA model with best k
lda_final = LdaModel(
    corpus=corpus,
    id2word=dictionary,
    num_topics=best_k,
    alpha=0.5,
    eta="auto",
    passes=15,
    random_state=42,
)

# Assign each tweet to its dominant LDA topic
lda_topic_assignments = []
lda_topic_probs = []
for bow in corpus:
    topic_dist = lda_final.get_document_topics(bow, minimum_probability=0)
    dominant = max(topic_dist, key=lambda x: x[1])
    lda_topic_assignments.append(dominant[0])
    lda_topic_probs.append(dominant[1])

id_df["lda_topic_id"] = lda_topic_assignments
id_df["lda_topic_prob"] = lda_topic_probs

log.info(f"LDA assigned {len(id_df)} tweets to {best_k} topics")

# Save LDA coherence scores
coherence_df = pd.DataFrame([
    {"k": k, "cv_coherence": score} for k, score in coherence_scores.items()
])
coherence_df.to_csv(f"{RUNTIME.output_dir}/lda_coherence_scores.csv", index=False)

# Save LDA topic info
lda_topic_info = []
for topic_id in range(best_k):
    terms = lda_final.show_topic(topic_id, topn=10)
    lda_topic_info.append({
        "lda_topic_id": topic_id,
        "terms": ", ".join([w for w, _ in terms]),
        "term_weights": ", ".join([f"{w}:{s:.3f}" for w, s in terms]),
    })
pd.DataFrame(lda_topic_info).to_csv(f"{RUNTIME.output_dir}/lda_topic_info.csv", index=False)

# ======================================================================
# STAGE 2: Per-LDA-topic BERTopic with distiluse-base-multilingual-cased
# ======================================================================
log.info("=" * 60)
log.info("STAGE 2: BERTopic per LDA topic")
log.info("=" * 60)

embed_model = SentenceTransformer("distiluse-base-multilingual-cased", device=RUNTIME.device)

bertopic_subtopic = np.full(len(id_df), -1, dtype=int)
bertopic_cluster_labels = []  # (lda_topic, subtopic, representative_tweet_idx)

for lda_topic in range(best_k):
    mask = id_df["lda_topic_id"] == lda_topic
    topic_indices = id_df.index[mask]
    topic_docs = id_df.loc[topic_indices, "topic_text"].tolist()

    if len(topic_docs) < 10:
        log.info(f"  LDA topic {lda_topic}: only {len(topic_docs)} tweets, skipping BERTopic")
        continue

    log.info(f"  LDA topic {lda_topic}: {len(topic_docs)} tweets → BERTopic...")

    topic_embeddings = embed_model.encode(
        topic_docs,
        batch_size=RUNTIME.embedding_batch_size,
        show_progress_bar=False,
    )

    topic_bertopic = BERTopic(
        embedding_model=embed_model,
        language="multilingual",
        calculate_probabilities=False,
        verbose=False,
        min_topic_size=max(5, len(topic_docs) // 20),
    )

    subtopics, _ = topic_bertopic.fit_transform(topic_docs, topic_embeddings)

    # Map subtopic assignments back to global index
    for local_idx, global_idx in enumerate(topic_indices):
        bertopic_subtopic[global_idx] = subtopics[local_idx]

    # Get the 3 largest BERTopic clusters (excluding -1 outlier)
    cluster_counts = {}
    for s in subtopics:
        if s >= 0:
            cluster_counts[s] = cluster_counts.get(s, 0) + 1

    top3_clusters = sorted(cluster_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    log.info(f"  LDA topic {lda_topic}: found {len(cluster_counts)} BERTopic clusters, top 3: {top3_clusters}")

    # For each of the 3 largest clusters, find representative tweet
    for cluster_id, cluster_size in top3_clusters:
        cluster_local_indices = [i for i, s in enumerate(subtopics) if s == cluster_id]
        cluster_global_indices = [topic_indices[i] for i in cluster_local_indices]

        if len(cluster_local_indices) < 2:
            continue

        # Compute pairwise cosine similarity within cluster
        cluster_embeddings = topic_embeddings[cluster_local_indices]
        from sklearn.metrics.pairwise import cosine_similarity
        sim_matrix = cosine_similarity(cluster_embeddings)

        # Representative = tweet with highest average cosine similarity to all others
        avg_sims = sim_matrix.mean(axis=1)
        rep_local_idx = np.argmax(avg_sims)
        rep_global_idx = cluster_global_indices[rep_local_idx]

        bertopic_cluster_labels.append({
            "lda_topic": lda_topic,
            "bertopic_subtopic": cluster_id,
            "cluster_size": cluster_size,
            "representative_tweet_id": id_df.loc[rep_global_idx, "id"] if "id" in id_df.columns else rep_global_idx,
            "representative_avg_similarity": float(avg_sims[rep_local_idx]),
            "representative_text": id_df.loc[rep_global_idx, "topic_text"][:200],
        })

id_df["bertopic_subtopic"] = bertopic_subtopic

# ======================================================================
# STAGE 3: Merge back to full dataframe
# ======================================================================
log.info("=" * 60)
log.info("STAGE 3: Merging results back to full dataset")
log.info("=" * 60)

full_df = df.copy()
full_df["lda_topic_id"] = -1
full_df["lda_topic_prob"] = np.nan
full_df["bertopic_subtopic"] = -1
full_df["is_representative"] = False

full_df.loc[id_df.index, "lda_topic_id"] = id_df["lda_topic_id"].values
full_df.loc[id_df.index, "lda_topic_prob"] = id_df["lda_topic_prob"].values
full_df.loc[id_df.index, "bertopic_subtopic"] = id_df["bertopic_subtopic"].values

# Mark representative tweets
rep_ids = [r["representative_tweet_id"] for r in bertopic_cluster_labels]
full_df["is_representative"] = full_df["id"].isin(rep_ids) if "id" in full_df.columns else False

# Create combined topic_id for backward compatibility (use LDA topic as primary)
full_df["topic_id"] = full_df["lda_topic_id"]
full_df["topic_prob"] = full_df["lda_topic_prob"]

# Save topic info (combined LDA + BERTopic)
topic_info_rows = []
for lda_topic in range(best_k):
    lda_terms = lda_final.show_topic(lda_topic, topn=10)
    bertopic_for_topic = [r for r in bertopic_cluster_labels if r["lda_topic"] == lda_topic]
    topic_info_rows.append({
        "Topic": lda_topic,
        "Count": int((id_df["lda_topic_id"] == lda_topic).sum()),
        "Name": f"{lda_topic}_{'_'.join([w for w, _ in lda_terms[:3]])}",
        "Representation": str([w for w, _ in lda_terms]),
        "Representative_Docs": str([r["representative_text"] for r in bertopic_for_topic[:3]]),
        "lda_topic_id": lda_topic,
        "num_bertopic_subtopics": len(bertopic_for_topic),
    })
topic_info = pd.DataFrame(topic_info_rows)
topic_info.to_csv(f"{RUNTIME.output_dir}/topic_info.csv", index=False)

# Save representative tweets
if bertopic_cluster_labels:
    rep_df = pd.DataFrame(bertopic_cluster_labels)
    rep_df.to_csv(f"{RUNTIME.output_dir}/representative_tweets.csv", index=False)
    log.info(f"Saved {len(rep_df)} representative tweets")

full_df.to_csv(f"{RUNTIME.output_dir}/tweets_with_topics.csv", index=False)

log.info(f"\nTopics found (LDA): {best_k}")
log.info(f"BERTopic subtopics total: {len(bertopic_cluster_labels)}")
log.info(topic_info.head(15).to_string())
