import pandas as pd

TARGET = 10000

df = pd.read_csv("data/processed/tweets_clean.csv")

# Stratified sample by query_raw so all query types are represented
sample = (
    df.groupby("query_raw", group_keys=False)
    .apply(
        lambda x: x.sample(
            min(len(x), int(TARGET * len(x) / len(df))),
            random_state=42,
        )
    )
    .reset_index(drop=True)
)

# Top up from remaining rows to hit target when proportional rounding undershoots
if len(sample) < min(TARGET, len(df)):
    remainder = min(TARGET, len(df)) - len(sample)
    sampled_ids = set(sample["id"].astype(str))
    remaining = df[~df["id"].astype(str).isin(sampled_ids)]
    if not remaining.empty:
        top_up = remaining.sample(min(remainder, len(remaining)), random_state=42)
        sample = pd.concat([sample, top_up], ignore_index=True)

# Cap at exactly target (or full corpus when corpus < target)
sample = sample.sample(min(len(sample), TARGET), random_state=42).reset_index(drop=True)

sample.to_csv("data/processed/tweets_sample_10k.csv", index=False)

print(f"Total corpus   : {len(df)}")
print(f"Sample size    : {len(sample)}")
print(f"Query breakdown:\n{sample['query_raw'].value_counts()}")
print(f"Lang breakdown :\n{sample['lang'].value_counts()}")
print("Saved to data/processed/tweets_sample_10k.csv")
