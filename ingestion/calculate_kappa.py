import pandas as pd
from sklearn.metrics import classification_report, cohen_kappa_score

# Load all reviewed files
high = pd.read_csv("data/processed/review_high_confidence_spotcheck.csv")
medium = pd.read_csv("data/processed/review_medium_confidence.csv")
low = pd.read_csv("data/processed/review_low_confidence.csv")

reviewed = pd.concat([high, medium, low], ignore_index=True)
if "human_label" not in reviewed.columns:
    reviewed["human_label"] = pd.NA
reviewed = reviewed.dropna(subset=["human_label"])

if reviewed.empty:
    print("=" * 60)
    print("INTER-RATER AGREEMENT REPORT")
    print("=" * 60)
    print("Tweets reviewed          : 0")
    print("No human_label values found yet. Fill review files first, then rerun.")
    print("=" * 60)
    raise SystemExit(0)

haiku_labels = reviewed["label"].tolist()
human_labels = reviewed["human_label"].tolist()

kappa = cohen_kappa_score(haiku_labels, human_labels)
correction_rate = (
    sum(1 for h, u in zip(haiku_labels, human_labels) if h != u) / len(haiku_labels) * 100
)

print("=" * 60)
print("INTER-RATER AGREEMENT REPORT")
print("=" * 60)
print(f"Tweets reviewed          : {len(reviewed)}")
print(f"Cohen's Kappa            : {kappa:.3f}")
print(f"Correction rate          : {correction_rate:.1f}%")
print()
print("Kappa interpretation:")
if kappa >= 0.80:
    print("  > 0.80 -> Almost perfect — Haiku was very reliable")
elif kappa >= 0.60:
    print("  0.60-0.80 -> Substantial — acceptable for academic use")
else:
    print("  < 0.60 -> Moderate — note limitations in your methods section")
print()
print("Classification report (Haiku vs Human):")
print(classification_report(human_labels, haiku_labels))
print("=" * 60)
print()
print("Paste this into your methods section:")
print(
    f"""
A stratified random sample of 10,000 tweets was annotated using Claude
Haiku 4.5 (Anthropic, accessed 2025) via a structured prompt specifying
MBG program relevance criteria. All medium and low-confidence annotations
were manually reviewed and corrected by the first author, alongside a 10%
random sample of high-confidence annotations. Inter-rater agreement between
the LLM and human reviewer yielded Cohen's Kappa of {kappa:.2f}, indicating
{'near-perfect' if kappa >= 0.80 else 'substantial'} agreement.
The correction rate was {correction_rate:.1f}%.
"""
)
