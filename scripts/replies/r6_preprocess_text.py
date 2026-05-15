#!/usr/bin/env python3
"""R6: Text preprocessing"""
import pandas as pd
import re, sys, spacy
from tqdm import tqdm
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

INPUT = sys.argv[1] if len(sys.argv) > 1 else "/opt/mbg/data/consolidated/replies_sample_tagged.csv"
OUTPUT = INPUT.replace("_tagged.csv", "_preprocessed.csv")
REJECTED = INPUT.replace("_tagged.csv", "_preprocess_rejected.csv")

stemmer = StemmerFactory().create_stemmer()
id_stopwords = set(StopWordRemoverFactory().get_stop_words())
id_stopwords.update({"yg","dgn","utk","krn","tdk","jd","tp","sy","gw","gue","lo","lu","nih","deh","sih","dong","wkwk","haha","hehe","lol","btw"})
nlp = spacy.load("en_core_web_sm", disable=["parser","ner"])

df = pd.read_csv(INPUT)

def remove_noise(text):
    text = re.sub(r"http\S+", "", str(text))
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"^RT\s+:?\s*", "", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return re.sub(r"\s+", " ", text).strip()

def clean_light(text):
    text = remove_noise(text)
    return re.sub(r"#(\w+)", r"\1", text).strip()

def clean_topic_id(text):
    text = remove_noise(text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", "", text).lower()
    text = stemmer.stem(text)
    words = [w for w in text.split() if w not in id_stopwords and len(w) > 2]
    return " ".join(words).strip()

def clean_topic_en(text):
    text = remove_noise(text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\d+", "", text).lower()
    doc = nlp(text[:5000])
    words = [t.lemma_ for t in doc if not t.is_stop and not t.is_punct and not t.is_space and len(t.lemma_) > 2 and t.lemma_.isalpha()]
    return " ".join(words).strip()

df["text_clean_light"] = [clean_light(t) for t in tqdm(df["text"], desc="Light cleaning")]

df["text_clean_topic"] = [
    clean_topic_en(r["text"]) if r.get("detected_lang") == "en" else clean_topic_id(r["text"])
    for _, r in tqdm(df.iterrows(), total=len(df), desc="Topic cleaning")
]

empty_mask = df["text_clean_topic"].str.strip() == ""
if empty_mask.sum() > 0:
    rejected = df[empty_mask].copy()
    rejected["reject_reason"] = "empty_after_preprocessing"
    rejected.to_csv(REJECTED, index=False)
    df = df[~empty_mask].copy()

df.to_csv(OUTPUT, index=False)
print(f"Preprocessed {len(df)} rows → {OUTPUT}")
print(f"Rejected {empty_mask.sum()} empty rows")
