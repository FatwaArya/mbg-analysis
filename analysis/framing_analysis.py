import pandas as pd
import re
import os

os.makedirs("data/analysis", exist_ok=True)

ann = pd.read_csv("data/processed/tweets_final_annotated.csv")
ann = ann[ann["final_label"] == "RELEVANT"].dropna(subset=["reason"])

FRAMES = {
    "operational_criticism": r"keracunan|food poison|basi|busuk|distribusi|terlambat|belum dapat|tidak merata|kualitas|logistik|delivery|distribution fail",
    "political_criticism":   r"korupsi|corrupt|pencitraan|gimmick|janji palsu|mark.?up|anggaran|bocor|politis|propaganda",
    "positive_support":      r"bagus|baik|mendukung|support|manfaat|gizi|nutrisi|stunting|berhasil|sukses|positif|lanjutkan",
    "neutral_reporting":     r"laporan|report|data|statistik|angka|persen|jumlah|total|survey|penelitian",
}

def classify(text):
    text = str(text).lower()
    for frame, pattern in FRAMES.items():
        if re.search(pattern, text):
            return frame
    return "other"

ann["frame"] = ann["reason"].apply(classify)

# Distribution
dist = ann["frame"].value_counts()
dist_pct = (dist / len(ann) * 100).round(1)
print("=== FRAMING DISTRIBUTION ===")
print(pd.DataFrame({"count": dist, "pct": dist_pct}).to_string())

# Frame × sentiment
if "final_label" in ann.columns:
    # use sentiment from tweets_with_sentiment if available
    try:
        sent = pd.read_csv("data/processed/tweets_with_sentiment.csv", parse_dates=["date"])
        sent = sent[sent["date"] >= "2025-01-01"]
        sent = sent[["id","sentiment_normalized","engagement_total","retweet_count"]]
        ann = ann.merge(sent, on="id", how="left")
        frame_sent = ann.groupby(["frame","sentiment_normalized"]).size().unstack(fill_value=0)
        frame_sent_pct = frame_sent.div(frame_sent.sum(axis=1), axis=0) * 100
        frame_sent_pct.to_csv("data/analysis/framing_sentiment.csv")
        print("\n=== FRAME × SENTIMENT ===")
        print(frame_sent_pct.round(1).to_string())

        frame_eng = ann.groupby("frame").agg(
            count=("id","count"),
            avg_engagement=("engagement_total","mean"),
            avg_rt=("retweet_count","mean"),
        ).round(1)
        frame_eng.to_csv("data/analysis/framing_engagement.csv")
        print("\n=== FRAME × ENGAGEMENT ===")
        print(frame_eng.to_string())
    except Exception as e:
        print(f"Sentiment merge skipped: {e}")

dist.to_csv("data/analysis/framing_distribution.csv")
print("\n=== FRAMING ANALYSIS COMPLETE ===")
