"""
scripts/preprocess_text.py
Text preprocessing with Sastrawi (Indonesian) and spaCy (English).
Insert between Phase 1 (tag_language.py) and Phase 2 (run_sentiment.py).

Input : data/processed/tweets_relevant_tagged.csv
Output: data/processed/tweets_preprocessed.csv
        data/processed/tweets_preprocessing_rejected.csv
"""

import re
import pandas as pd
import spacy
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from tqdm import tqdm
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # FIX: allow importing runtime from repo root.
from runtime import RUNTIME

tqdm.pandas()

INPUT = f"{RUNTIME.processed_dir}/tweets_relevant_tagged.csv"  # FIX: centralize runtime input path.
OUTPUT = f"{RUNTIME.processed_dir}/tweets_preprocessed.csv"  # FIX: centralize runtime output path.
REJECTED = f"{RUNTIME.processed_dir}/tweets_preprocessing_rejected.csv"  # FIX: centralize runtime reject path.

# ── Load tools once at startup ────────────────────────────────────────
print("Loading Sastrawi stemmer...")
stem_factory = StemmerFactory()
stemmer = stem_factory.create_stemmer()

print("Loading Sastrawi stopword remover...")
stop_factory = StopWordRemoverFactory()
id_stopwords = set(stop_factory.get_stop_words())

# Add Twitter-specific Indonesian stopwords not in Sastrawi list
id_stopwords.update({
    "yg", "dgn", "utk", "krn", "tdk", "jd", "tp", "sy",
    "gw", "gue", "lo", "lu", "nih", "deh", "sih", "dong",
    "lah", "kah", "pun", "aja", "mah", "dong", "wkwk",
    "wkwkwk", "haha", "hehe", "hahaha", "lol", "omg",
    "btw", "fyi", "imo", "irl", "afk", "brb",
})

print("Loading spaCy English model...")
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
# Disable parser and NER — we only need tokenizer + tagger for lemmas
# This makes spaCy ~3x faster on large batches

print("All tools loaded.\n")

# ── Load data ─────────────────────────────────────────────────────────
df = pd.read_csv(INPUT)
print(f"Input : {len(df):,} tweets")
print(f"Columns: {list(df.columns)}")
print(f"Lang breakdown:\n{df['detected_lang'].value_counts().to_string()}\n")

# ── STEP 1: Base noise removal (applied to ALL tweets) ───────────────
# This runs before language-specific processing
def remove_noise(text):
    text = str(text)
    text = re.sub(r"http\S+", "", text) # remove URLs
    text = re.sub(r"@\w+", "", text) # remove @mentions
    text = re.sub(r"^RT\s+:?\s*", "", text) # remove RT prefix
    text = re.sub(r"(.)\1{2,}", r"\1\1", text) # looook → look (keep 2)
    text = re.sub(r"\s+", " ", text) # normalize whitespace
    return text.strip()

# ── STEP 2: Light cleaning — for sentiment model ──────────────────────
# Keep: emojis, punctuation, ! ? intensity markers
# Only base noise removal — no stemming, no stopwords
def clean_light(text):
    text = remove_noise(text)
    text = re.sub(r"#(\w+)", r"\1", text) # remove # keep word
    return text.strip()

# ── STEP 3a: Indonesian topic cleaning — Sastrawi ─────────────────────
def clean_topic_id(text):
    text = remove_noise(text)
    text = re.sub(r"#\w+", "", text) # remove hashtags fully
    text = re.sub(r"[^\w\s]", " ", text) # remove punctuation
    text = re.sub(r"\d+", "", text) # remove numbers
    text = text.lower()

    # Sastrawi stemming — handles Indonesian morphology
    text = stemmer.stem(text)

    # Remove stopwords using Sastrawi list + Twitter additions
    words = [
        w for w in text.split()
        if w not in id_stopwords and len(w) > 2
    ]
    text = " ".join(words)
    return re.sub(r"\s+", " ", text).strip()

# ── STEP 3b: English topic cleaning — spaCy ───────────────────────────
def clean_topic_en(text):
    text = remove_noise(text)
    text = re.sub(r"#\w+", "", text) # remove hashtags fully
    text = re.sub(r"[^\w\s]", " ", text) # remove punctuation
    text = re.sub(r"\d+", "", text) # remove numbers
    text = text.lower()

    # spaCy lemmatization — returns real words not chopped stems
    doc = nlp(text[:1000000]) # spaCy token limit safety
    words = [
        token.lemma_
        for token in doc
        if not token.is_stop # spaCy built-in stopwords
        and not token.is_punct
        and not token.is_space
        and len(token.lemma_) > 2
        and token.lemma_.isalpha() # only real words
    ]
    return " ".join(words).strip()

# ── Apply cleaners ────────────────────────────────────────────────────
print("Step 1/2: Applying light cleaning (for sentiment)...")
df["text_clean_light"] = df["text"].progress_apply(clean_light)

print("Step 2/2: Applying topic cleaning (Sastrawi for id, spaCy for en)...")
df["text_clean_topic"] = ""
lang_series = df.get("detected_lang", pd.Series(index=df.index, data="id")).fillna("unknown").astype(str)
en_mask = lang_series == "en"
id_mask = ~en_mask
df.loc[id_mask, "text_clean_topic"] = df.loc[id_mask, "text"].progress_apply(clean_topic_id)

if en_mask.any():
    # FIX: replace row-wise apply with batched nlp.pipe for English rows.
    en_prepped = (
        df.loc[en_mask, "text"]
        .astype(str)
        .apply(remove_noise)
        .str.replace(r"#\w+", "", regex=True)
        .str.replace(r"[^\w\s]", " ", regex=True)
        .str.replace(r"\d+", "", regex=True)
        .str.lower()
        .str.slice(0, 1_000_000)
    )
    en_cleaned = []
    for doc in nlp.pipe(en_prepped.tolist(), batch_size=RUNTIME.embedding_batch_size):
        words = [
            token.lemma_
            for token in doc
            if not token.is_stop
            and not token.is_punct
            and not token.is_space
            and len(token.lemma_) > 2
            and token.lemma_.isalpha()
        ]
        en_cleaned.append(" ".join(words).strip())
    df.loc[en_mask, "text_clean_topic"] = en_cleaned

# ── Quality check ─────────────────────────────────────────────────────
empty_mask = df["text_clean_topic"].str.strip() == ""
print(f"\nEmpty after topic cleaning : {empty_mask.sum()} tweets → rejected")

if empty_mask.sum() > 0:
    rejected = df[empty_mask].copy()
    rejected["reject_reason"] = "empty_after_text_cleaning"
    rejected.to_csv(REJECTED, index=False)
    df = df[~empty_mask].copy()

# ── Sample comparison ─────────────────────────────────────────────────
print("\n=== SAMPLE COMPARISON ===")

# Indonesian sample
id_sample_df = df[df["detected_lang"] == "id"]
if len(id_sample_df) > 0:
    # FIX: guard against empty language subsets before iloc access.
    id_sample = id_sample_df.iloc[0]
    print("Indonesian tweet:")
    print(f" Original : {id_sample['text'][:120]}")
    print(f" Light clean : {id_sample['text_clean_light'][:120]}")
    print(f" Topic clean : {id_sample['text_clean_topic'][:120]}")
else:
    print("Indonesian tweet sample unavailable (no id rows).")

print()

# English sample
en_sample = df[df["detected_lang"] == "en"]
if len(en_sample) > 0:
    # FIX: guard against empty language subsets before iloc access.
    en_sample = en_sample.iloc[0]
    print("English tweet:")
    print(f" Original : {en_sample['text'][:120]}")
    print(f" Light clean : {en_sample['text_clean_light'][:120]}")
    print(f" Topic clean : {en_sample['text_clean_topic'][:120]}")
else:
    print("English tweet sample unavailable (no en rows).")

# ── Save ──────────────────────────────────────────────────────────────
df.to_csv(OUTPUT, index=False)

# Write completion signal
with open(f"{RUNTIME.data_dir}/.preprocessing_done", "w") as f:
    f.write(f"completed at {pd.Timestamp.now()}\n")
    f.write(f"rows preprocessed: {len(df)}\n")
print(f"Completion signal written -> {RUNTIME.data_dir}/.preprocessing_done")

print(f"\n=== PREPROCESSING COMPLETE ===")
print(f"Output rows : {len(df):,}")
print(f"Rejected : {empty_mask.sum()}")
print(f"Columns added : text_clean_light, text_clean_topic")
print(f"Saved → {OUTPUT}")
print()
print("Tools used:")
print(" Indonesian → Sastrawi ECS stemmer + Sastrawi stopwords")
print(" English → spaCy en_core_web_sm lemmatizer + spaCy stopwords")
print()
print("Next step: python3 scripts/run_sentiment.py")
