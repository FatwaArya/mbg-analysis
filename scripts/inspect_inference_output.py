import pandas as pd

relevant = pd.read_csv("data/processed/tweets_relevant.csv")
rejected = pd.read_csv("data/processed/tweets_rejected.csv")
borderline = pd.read_csv("data/processed/tweets_borderline.csv")
total = len(relevant) + len(rejected) + len(borderline)

print("=== INFERENCE OUTPUT INSPECTION ===")
print(f"Relevant   : {len(relevant):,}")
print(f"Rejected   : {len(rejected):,}")
print(f"Borderline : {len(borderline):,}")
print(f"Total      : {total:,}")
print(f"Retention  : {len(relevant)/total*100:.1f}%")
print(f"Columns    : {list(relevant.columns)}")
print(f"Date range : {relevant['date'].min()} -> {relevant['date'].max()}")
print(f"Lang sample:\n{relevant['lang'].value_counts().head(10)}")

retention = len(relevant) / total * 100
if retention < 50:
    print("\n⚠️  WARNING: Retention < 50% — confidence threshold may be too strict")
elif retention > 95:
    print("\n⚠️  WARNING: Retention > 95% — model may not be filtering, check labels")
else:
    print("\n✅ Retention in expected range (60-90%), continue to Phase 1.4")
