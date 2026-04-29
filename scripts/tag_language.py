import pandas as pd
from langdetect import detect, DetectorFactory
from tqdm import tqdm

DetectorFactory.seed = 42

df = pd.read_csv("data/processed/tweets_relevant.csv")
print(f"Tagging {len(df):,} tweets...")

def detect_lang_safe(text):
    try:
        return detect(str(text))
    except:
        return "id"

tqdm.pandas()
df["detected_lang"] = df["text"].progress_apply(detect_lang_safe)
df["sentiment_model"] = df["detected_lang"].apply(
    lambda lang: "cardiffnlp/twitter-roberta-base-sentiment-latest" if lang == "en"
    else "mdhugol/indonesia-bert-sentiment-classifier"
)

df.to_csv("data/processed/tweets_relevant_tagged.csv", index=False)
print(f"\nLanguage breakdown:\n{df['detected_lang'].value_counts().to_string()}")
print(f"\nModel routing:\n{df['sentiment_model'].value_counts().to_string()}")
print(f"\nSaved -> data/processed/tweets_relevant_tagged.csv")
