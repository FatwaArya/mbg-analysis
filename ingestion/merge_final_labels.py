import pandas as pd

# Load full annotated sample
df = pd.read_csv("data/processed/tweets_annotated_haiku.csv")

# Load reviewed files with human corrections
high = pd.read_csv("data/processed/review_high_confidence_spotcheck.csv")
medium = pd.read_csv("data/processed/review_medium_confidence.csv")
low = pd.read_csv("data/processed/review_low_confidence.csv")

reviewed = pd.concat([high, medium, low], ignore_index=True)
if "human_label" not in reviewed.columns:
    reviewed["human_label"] = pd.NA
reviewed = reviewed[["id", "human_label"]].dropna()
reviewed["id"] = reviewed["id"].astype(str)
df["id"] = df["id"].astype(str)

# Merge human corrections back
df = df.merge(reviewed, on="id", how="left")

# Final label: use human label if available, else use Haiku label
df["final_label"] = df["human_label"].fillna(df["label"])

df.to_csv("data/processed/tweets_final_annotated.csv", index=False)

print(f"Final annotated dataset  : {len(df)} tweets")
print(f"Human reviewed           : {df['human_label'].notna().sum()} tweets")
print(f"Haiku only               : {df['human_label'].isna().sum()} tweets")
print()
print("Final label breakdown:")
print(df["final_label"].value_counts())
print()
print("Saved to data/processed/tweets_final_annotated.csv")
print("Next step: fine-tune IndoBERT using this annotated dataset")
