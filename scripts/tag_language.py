import pandas as pd
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from tqdm import tqdm
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # FIX: allow importing runtime from repo root.
from runtime import RUNTIME

DetectorFactory.seed = 42

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

df = pd.read_csv(f"{RUNTIME.processed_dir}/tweets_relevant.csv")  # FIX: centralize runtime input path.
print(f"Tagging {len(df):,} tweets...")

def detect_lang_safe(text):
    try:
        return detect(str(text))
    except (LangDetectException, TypeError, ValueError) as e:
        # FIX: avoid silent fallback to Indonesian and surface detection failures.
        log.warning("Language detection failed: %s", e)
        return "unknown"

tqdm.pandas()
df["detected_lang"] = df["text"].progress_apply(detect_lang_safe)

def route_sentiment_model(lang: str) -> str:
    if lang == "en":
        return "cardiffnlp/twitter-roberta-base-sentiment-latest"
    if lang == "unknown":
        # FIX: explicit routing fallback for unknown language rows.
        return "mdhugol/indonesia-bert-sentiment-classifier"
    return "mdhugol/indonesia-bert-sentiment-classifier"

df["sentiment_model"] = df["detected_lang"].apply(route_sentiment_model)

df.to_csv(f"{RUNTIME.processed_dir}/tweets_relevant_tagged.csv", index=False)

# Write completion signal
with open(f"{RUNTIME.data_dir}/.tagging_done", "w") as f:
    f.write(f"completed at {pd.Timestamp.now()}\n")
    f.write(f"rows tagged: {len(df)}\n")
print(f"Completion signal written -> {RUNTIME.data_dir}/.tagging_done")

print(f"\nLanguage breakdown:\n{df['detected_lang'].value_counts().to_string()}")
print(f"\nModel routing:\n{df['sentiment_model'].value_counts().to_string()}")
print(f"\nSaved -> {RUNTIME.processed_dir}/tweets_relevant_tagged.csv")
